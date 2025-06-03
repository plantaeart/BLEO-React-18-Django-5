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
    _initialized = False  # Track if system has been initialized
    
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
    def initialize(cls):
        """Initialize MongoDB once at server startup"""
        if cls._initialized:
            print("ℹ️ MongoDB system already initialized, skipping...")
            return cls._instance
            
        print("🚀 Initializing MongoDB system at server startup...")
        instance = cls.get_instance()
        
        instance.initialize_system()
        cls._initialized = True
        print("✅ MongoDB system initialization complete!")
        
        return instance
    
    @classmethod
    def get_instance(cls):
        """Get or create MongoDB instance (connection only)"""
        if cls._instance is None:
            cls._instance = MongoDB()
        return cls._instance
    
    def __init__(self):
        """Initialize MongoDB connection only (not the collections/parameters)"""
        try:
            # Get MongoDB connection details from environment variables
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            env.read_env(env_path)
            
            mongo_uri = env.str('MONGO_URI')
            mongo_password = env.str('MONGO_PASSWORD')
            db_name = env.str('MONGO_DB_NAME')
            
            print(f"Connecting to MongoDB: {mongo_uri.replace(mongo_password, '***')}")
            
            # Insert password into connection string if placeholder exists
            if '{password}' in mongo_uri:
                mongo_uri = mongo_uri.replace('{password}', mongo_password)
            
            # Create MongoDB client and connect to database
            self._client = MongoClient(mongo_uri)
            self._db = self._client[db_name]
            
            # Test connection
            self._client.admin.command('ping')
            print("✅ MongoDB connection successful!")

        except Exception as e:
            print(f"❌ MongoDB connection error: {str(e)}")
            raise

    def initialize_system(self):
        """Initialize collections and handle version updates (called only once)"""
        print("🔧 Initializing MongoDB collections and parameters...")
        
        # Step 1: Check/Create all collections with schemas
        self._ensure_collections_exist()
        
        # Step 2: Handle version updates (including AppParameters)
        self._handle_version_updates()
        
        print("✅ MongoDB system setup complete!")
    
    def _ensure_collections_exist(self):
        """Check if collections exist, create/update them with proper schemas"""
        print("📋 Checking collections...")
        collection_names = self._db.list_collection_names()
        
        for collection_key, collection_name in self.COLLECTIONS.items():
            if collection_name not in collection_names:
                print(f"  📝 Creating collection: {collection_name}")
                self.setup_collection(collection_name, create=True)
            else:
                print(f"  🔄 Updating schema for existing collection: {collection_name}")
                self.setup_collection(collection_name, create=False)
    
    def _handle_version_updates(self):
        """Handle version-based parameter updates"""
        try:
            print("🔢 Checking application version...")
            app_params_collection = self.COLLECTIONS['AppParameters']
            version_param = self._db[app_params_collection].find_one({"param_name": AppParameters.PARAM_APP_VERSION})
            
            if not version_param:
                print("  ⚠️ No version found, starting with version 1.0.0...")
                current_version = "1.0.0"
            else:
                current_version = version_param.get("param_value", "1.0.0")
                print(f"  📊 Current database version: {current_version}")
            
            # Run version updates starting from 1.0.0
            versions_to_run = ["1.0.0"]  # Add future versions here: ["1.0.0", "1.1.0", "1.2.0"]
            
            for version in versions_to_run:
                if self._should_run_version(current_version, version):
                    self._run_version_update(version)
                    
        except Exception as e:
            print(f"❌ Error handling version updates: {str(e)}")
    
    def _should_run_version(self, current_version, target_version):
        """Determine if we should run a version update"""
        # For now, always run 1.0.0 to ensure base parameters exist
        if target_version == "1.0.0":
            return True
        # Add logic for future versions
        return False
    
    def _run_version_update(self, version):
        """Run the update script for a specific version"""
        try:
            print(f"  🚀 Running version {version} updates...")
            
            if version == '1.0.0':
                from mongoDbVersionUpdate.v1_0_0.v1_0_0_AppParameters import update_app_parameters
                result = update_app_parameters()
                
                if result["success"]:
                    print(f"    ✅ {result['message']}")
                    print(f"    📊 Created: {result['created']}, Updated: {result['updated']}")
                else:
                    print(f"    ❌ {result['message']}: {result.get('error', 'Unknown error')}")
            else:
                print(f"    ⚠️ No update module found for version {version}")
                
        except ImportError as e:
            print(f"    ❌ Could not import update module for version {version}: {str(e)}")
        except Exception as e:
            print(f"    ❌ Error running version {version} update: {str(e)}")

    def setup_collection(self, collection_name, create=False, verbose=False):
        """Setup MongoDB collection with schema validation"""
        try:
            # Map collection name to schema
            schema_mapping = {
                self.COLLECTIONS['Users']: USER_SCHEMA,
                self.COLLECTIONS['Links']: LINK_SCHEMA,
                self.COLLECTIONS['MessagesDays']: MESSAGE_DAY_SCHEMA,
                self.COLLECTIONS['PasswordResets']: PASSWORD_RESET_SCHEMA,
                self.COLLECTIONS['TokenBlacklist']: TOKEN_BLACKLIST_SCHEMA,
                self.COLLECTIONS['DebugLogs']: DEBUG_LOGS_SCHEMA,
                self.COLLECTIONS['AppParameters']: APP_PARAMETERS_SCHEMA
            }
            
            if collection_name not in schema_mapping:
                if verbose:
                    print(f"Warning: No schema found for collection {collection_name}")
                return
            
            schema = schema_mapping[collection_name]
            
            if create:
                # Drop collection if it exists
                if collection_name in self._db.list_collection_names():
                    if verbose:
                        print(f"Dropping existing collection: {collection_name}")
                    self._db.drop_collection(collection_name)
                
                # Create collection with validation
                if verbose:
                    print(f"Creating collection with schema: {collection_name}")
                
                self._db.create_collection(
                    collection_name,
                    validator=schema,
                    validationLevel="strict"
                )
                
                # Set up indexes
                self._setup_collection_indexes(collection_name)
                
                if verbose:
                    print(f"✅ Collection created: {collection_name}")
            else:
                # Just update the schema without dropping
                try:
                    self._db.command({
                        "collMod": collection_name,
                        "validator": schema,
                        "validationLevel": "moderate"
                    })
                    if verbose:
                        print(f"✅ Schema updated for collection: {collection_name}")
                except Exception as e:
                    if verbose:
                        print(f"❌ Error updating schema for {collection_name}: {str(e)}")
        
        except Exception as e:
            print(f"❌ Error setting up collection {collection_name}: {str(e)}")
            raise

    def _setup_collection_indexes(self, collection_name):
        """Setup indexes for a collection"""
        if collection_name == self.COLLECTIONS['Users']:
            self._db[collection_name].create_index([("email", ASCENDING)], unique=True)
            self._db[collection_name].create_index([("username", ASCENDING)], unique=True)
            self._db[collection_name].create_index([("BLEOId", ASCENDING)], unique=True)
        elif collection_name == self.COLLECTIONS['PasswordResets']:
            self._db[collection_name].create_index([("token", ASCENDING)], unique=True)
            self._db[collection_name].create_index([("email", ASCENDING)])
        elif collection_name == self.COLLECTIONS['TokenBlacklist']:
            self._db[collection_name].create_index([("token", ASCENDING)], unique=True)
            self._db[collection_name].create_index([("expires", ASCENDING)])
        elif collection_name == self.COLLECTIONS['AppParameters']:
            self._db[collection_name].create_index([("param_name", ASCENDING)], unique=True)
        elif collection_name == self.COLLECTIONS['DebugLogs']:
            self._db[collection_name].create_index([("date", ASCENDING)])
            self._db[collection_name].create_index([("BLEOId", ASCENDING)])
            self._db[collection_name].create_index([("type", ASCENDING)])
    
    def get_collection(self, collection_key):
        """Get MongoDB collection by key"""
        if collection_key not in self.COLLECTIONS:
            raise ValueError(f"Collection key not found: {collection_key}")
        
        collection_name = self.COLLECTIONS[collection_key]
        return self._db[collection_name]

    def get_db(self):
        """Get MongoDB database instance"""
        return self._db

    @classmethod
    def get_client(cls):
        """Get MongoDB client instance"""
        if cls._instance is None:
            cls._instance = MongoDB()
        return cls._instance._client

    def get_client_instance(self):
        """Get MongoDB client instance from current instance"""
        return self._client