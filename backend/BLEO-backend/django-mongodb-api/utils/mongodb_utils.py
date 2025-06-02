from utils.config_manager import ConfigManager
from models.enums.DebugType import DebugType
from models.AppParameters import AppParameters
import os
from pymongo import MongoClient, ASCENDING
from environs import Env
from .mongodb_schemas import (
    USER_SCHEMA, 
    LINK_SCHEMA, 
    MESSAGE_DAY_SCHEMA, 
    PASSWORD_RESET_SCHEMA, 
    TOKEN_BLACKLIST_SCHEMA,
    DEBUG_LOGS_SCHEMA,
    APP_PARAMETERS_SCHEMA
)

env = Env()
env.read_env()

class MongoDB:
    """MongoDB connection utility class"""
    
    _instance = None
    _client = None
    _db = None
    
    # Collection mapping dictionary
    COLLECTIONS = {
        'Users': 'Users',
        'Links': 'Links', 
        'MessagesDays': 'MessagesDays',
        'PasswordResets': 'PasswordResets',
        'TokenBlacklist': 'TokenBlacklist',
        'DebugLogs': 'DebugLogs',
        'AppParameters': 'AppParameters'
    }
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MongoDB()
        return cls._instance
    
    @classmethod
    def get_client(cls):
        if cls._instance is None:
            cls._instance = MongoDB()
        return cls._instance._client

    def __init__(self):
        # Get MongoDB connection details from environment variables
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            env.read_env(env_path)
            
            mongo_uri = env.str('MONGO_URI')
            mongo_password = env.str('MONGO_PASSWORD')
            db_name = env.str('MONGO_DB_NAME')
            
            print(f"Using MongoDB URI: {mongo_uri.replace(mongo_password, '***')}")
            
            # Insert password into connection string if placeholder exists
            if '{password}' in mongo_uri:
                mongo_uri = mongo_uri.replace('{password}', mongo_password)
            
            # Create MongoDB client and connect to database
            self._client = MongoClient(mongo_uri)
            self._db = self._client[db_name]
            
            # Test connection
            self._client.admin.command('ping')
            print("MongoDB connection successful!")
            
            # Initialize collections with schema validation
            self._initialize_collections()
            
            # Check app version and run any necessary migrations
            self.check_app_version()

        except Exception as e:
            print(f"MongoDB connection error: {str(e)}")
            raise

    def _initialize_collections(self):
        """Initialize MongoDB collections with schema validation"""
        # First check if AppParameters exists, and if not, create it with defaults
        self._initialize_app_parameters()
        
        # Now proceed with other collections as normal
        collection_names = self._db.list_collection_names()
        
        # Initialize each collection if it doesn't exist
        for collection in self.COLLECTIONS.values():
            if collection not in collection_names:
                self.setup_collection(collection, create=True)
            else:
                self.setup_collection(collection, create=False)

    def _initialize_app_parameters(self):
        """Initialize AppParameters collection with default values from config"""
        collection_names = self._db.list_collection_names()
        app_params_collection = self.COLLECTIONS['AppParameters']
        
        # Load current state from config file
        app_state = ConfigManager.get_app_state()
        
        # First, completely drop the collection if it exists (to ensure clean schema)
        if app_params_collection in collection_names:
            print(f"Dropping existing AppParameters collection to update schema")
            self._db.drop_collection(app_params_collection)
        
        # Create collection with new schema
        print("Creating AppParameters collection with new schema")
        self.setup_collection(app_params_collection, create=True, verbose=True)
        
        # Then insert default parameters with new structure
        default_params = [
            AppParameters(
                id=0,
                param_name=AppParameters.PARAM_DEBUG_LEVEL,
                param_value=app_state['debug_level']
            ),
            AppParameters(
                id=1,
                param_name=AppParameters.PARAM_APP_VERSION, 
                param_value=app_state['app_version']
            )
        ]
        
        for param in default_params:
            self._db[app_params_collection].insert_one(param.to_dict())
    
        print(f"Initialized AppParameters with new model structure")
    def check_app_version(self):
        """Check app version and handle updates if needed"""
        app_params_collection = self.COLLECTIONS['AppParameters']
        version_param = self._db[app_params_collection].find_one({"param_name": AppParameters.PARAM_APP_VERSION})
        
        if not version_param:
            print("Warning: App version parameter not found, initializing...")
            self._initialize_app_parameters()
            return
        
        current_version = version_param.get("param_value", "1.0.0")
        print(f"Current database app version: {current_version}")
        
        # Here's where you can implement version-based migrations
        # For example:
        if current_version == "1.0.0":
            # No migration needed for initial version
            pass
        elif current_version == "1.1.0":
            # Migrate from 1.1.0 to newer version
            self._migrate_from_1_1_0()
        elif current_version == "1.2.0":
            # Migrate from 1.2.0 to newer version
            self._migrate_from_1_2_0()

    def update_app_version(self, new_version):
        """Update the app version in both the database and config file"""
        app_params_collection = self.COLLECTIONS['AppParameters']
        result = self._db[app_params_collection].update_one(
            {"param_name": AppParameters.PARAM_APP_VERSION},
            {"$set": {"param_value": new_version}}
        )
        
        # Also update the config file
        ConfigManager.update_app_version(new_version)
        
        if result.modified_count > 0:
            print(f"Updated app version to {new_version}")
        else:
            print(f"Failed to update app version")
            
        return result.modified_count > 0

    def recreate_collection(self, collection_name):
        """Drop and recreate a collection"""
        if collection_name not in self.COLLECTIONS.values():
            print(f"Warning: {collection_name} is not in the recognized collections list")
            return False
        
        try:
            print(f"Dropping collection: {collection_name}")
            self._db.drop_collection(collection_name)
            
            print(f"Recreating collection: {collection_name}")
            self.setup_collection(collection_name, create=True, verbose=True)
            
            # Update the AppParameters to track recreation
            app_params_collection = self.COLLECTIONS['AppParameters']

            # Update the document
            self._db[app_params_collection].update_one(
                {"id": "app_parameters"},
            )
            
            return True
        except Exception as e:
            print(f"Error recreating collection {collection_name}: {str(e)}")
            return False

    def _ensure_index(self, collection, index_spec, unique=False, name=None, **kwargs):
        """Safely create an index if it doesn't exist or matches existing definition"""
        try:
            collection.create_index(index_spec, unique=unique, name=name, **kwargs)
        except Exception as e:
            # If index already exists with different options, drop and recreate it
            if "already exists with different options" in str(e) or "IndexKeySpecsConflict" in str(e):
                # Find the existing index name
                for idx in collection.list_indexes():
                    key_items = list(idx['key'].items())
                    index_spec_items = [(field[0], field[1]) for field in index_spec]
                    if key_items == index_spec_items:
                        idx_name = idx['name']
                        print(f"Dropping existing index {idx_name} with different options")
                        collection.drop_index(idx_name)
                        collection.create_index(index_spec, unique=unique, name=name, **kwargs)
                        return
            else:
                print(f"Error creating index: {e}")

    def get_db(self):
        return self._db
    
    def get_collection(self, collection_name):
        # Use the COLLECTIONS dictionary to get the actual collection name
        actual_collection = self.COLLECTIONS.get(collection_name, collection_name)
        return self._db[actual_collection]
    
    def setup_collection(self, collection_name, create=False, verbose=False):
        """
        Set up a MongoDB collection with proper schema validation and indexes
        
        Args:
            collection_name: Name of the collection to set up
            create: Whether to create the collection if it doesn't exist
            verbose: Whether to print verbose information about the setup
        """
        try:
            # Get the schema for this collection based on the name
            schema_map = {
                'Users': USER_SCHEMA,
                'Links': LINK_SCHEMA,
                'MessagesDays': MESSAGE_DAY_SCHEMA,
                'PasswordResets': PASSWORD_RESET_SCHEMA,
                'TokenBlacklist': TOKEN_BLACKLIST_SCHEMA,
                'DebugLogs': DEBUG_LOGS_SCHEMA,
                'AppParameters': APP_PARAMETERS_SCHEMA
            }
            
            schema = schema_map.get(collection_name)
            if not schema:
                if verbose:
                    print(f"Warning: No schema defined for collection {collection_name}")
                return
            
            # Create collection with validation if it doesn't exist and create=True
            if create:
                if verbose:
                    print(f"Creating collection {collection_name} with schema validation")
                
                try:
                    self._db.create_collection(collection_name, validator=schema)
                except Exception as e:
                    if "already exists" in str(e):
                        if verbose:
                            print(f"Collection {collection_name} already exists, updating schema")
                        # Update validation for existing collection
                        self._db.command({
                            'collMod': collection_name,
                            'validator': schema,
                            'validationLevel': 'moderate'  # 'strict' or 'moderate'
                        })
                    else:
                        raise
            else:
                # Just update validation for existing collection
                if verbose:
                    print(f"Updating schema validation for collection {collection_name}")
                try:
                    self._db.command({
                        'collMod': collection_name,
                        'validator': schema,
                        'validationLevel': 'moderate'  # 'strict' or 'moderate'
                    })
                except Exception as e:
                    if "not found" in str(e) and create:
                        # Collection doesn't exist but create=True, so create it
                        self._db.create_collection(collection_name, validator=schema)
                    elif "not found" in str(e):
                        if verbose:
                            print(f"Collection {collection_name} not found and create=False")
                    else:
                        raise
            
            # Set up indexes based on collection
            collection = self._db[collection_name]
            
            if collection_name == 'Users':
                # Create unique indexes for Users collection
                self._ensure_index(collection, [('email', ASCENDING)], unique=True)
                self._ensure_index(collection, [('BLEOId', ASCENDING)], unique=True)
                if verbose:
                    print(f"Created unique indexes on email and BLEOId for Users collection")
                    
            elif collection_name == 'Links':
                # Create indexes for Links collection
                self._ensure_index(collection, [('BLEOIdPartner1', ASCENDING)])
                self._ensure_index(collection, [('BLEOIdPartner2', ASCENDING)])
                self._ensure_index(collection, [('status', ASCENDING)])
                if verbose:
                    print(f"Created indexes on BLEOIdPartner1, BLEOIdPartner2, and status for Links collection")
                    
            elif collection_name == 'MessagesDays':
                # Create indexes for MessagesDays collection
                self._ensure_index(collection, [('fromBLEOId', ASCENDING)])
                self._ensure_index(collection, [('toBLEOId', ASCENDING)])
                self._ensure_index(collection, [('date', ASCENDING)])
                self._ensure_index(collection, [('fromBLEOId', ASCENDING), ('date', ASCENDING)], unique=True)
                if verbose:
                    print(f"Created indexes on fromBLEOId, toBLEOId, and date for MessagesDays collection")
                    
            elif collection_name == 'PasswordResets':
                # Create indexes for PasswordResets collection
                self._ensure_index(collection, [('email', ASCENDING)])
                self._ensure_index(collection, [('token', ASCENDING)], unique=True)
                self._ensure_index(collection, [('expires', ASCENDING)])  # For expiry cleanup
                if verbose:
                    print(f"Created indexes on email, token, and expires for PasswordResets collection")
                    
            elif collection_name == 'TokenBlacklist':
                # Create indexes for TokenBlacklist collection
                self._ensure_index(collection, [('token', ASCENDING)], unique=True)
                self._ensure_index(collection, [('expires_at', ASCENDING)])  # For expiry cleanup
                if verbose:
                    print(f"Created indexes on token and expires_at for TokenBlacklist collection")
                    
            elif collection_name == 'DebugLogs':
                # Create indexes for DebugLogs collection
                self._ensure_index(collection, [('timestamp', ASCENDING)])
                self._ensure_index(collection, [('level', ASCENDING)])
                self._ensure_index(collection, [('bleoid', ASCENDING)])
                if verbose:
                    print(f"Created indexes on timestamp, level, and bleoid for DebugLogs collection")
                    
            elif collection_name == 'AppParameters':
                # Create indexes for AppParameters collection
                self._ensure_index(collection, [('id', ASCENDING)], unique=True)
                if verbose:
                    print(f"Created unique index on id for AppParameters collection")
                    
            if verbose:
                print(f"Collection {collection_name} setup complete")
                
        except Exception as e:
            print(f"Error setting up collection {collection_name}: {str(e)}")
            raise

    def _migrate_from_1_1_0(self):
        """Example migration from version 1.1.0"""
        print("Running migration from version 1.1.0...")
        # Implement your migration logic here
        
        # Finally, update the version
        self.update_app_version("1.2.0")

    def _migrate_from_1_2_0(self):
        """Example migration from version 1.2.0"""
        print("Running migration from version 1.2.0...")
        # Implement your migration logic here
        
        # Finally, update the version
        self.update_app_version("1.3.0")
    
    def _get_next_param_id(self):
        """Get next parameter ID using max(id) + 1"""
        try:
            db = self._db[self.COLLECTIONS['AppParameters']]
            # Find the document with the highest ID
            result = db.find_one(sort=[("id", -1)])
            
            if result and "id" in result:
                return result["id"] + 1
            else:
                return 0
        except Exception as e:
            print(f"Error getting next parameter ID: {str(e)}")
            return 0