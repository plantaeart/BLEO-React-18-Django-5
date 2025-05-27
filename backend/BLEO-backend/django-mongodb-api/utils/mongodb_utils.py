import os
from pymongo import MongoClient, ASCENDING
from environs import Env
from .mongodb_schemas import USER_SCHEMA, LINK_SCHEMA, MESSAGE_DAY_SCHEMA, PASSWORD_RESET_SCHEMA, TOKEN_BLACKLIST_SCHEMA

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
        'TokenBlacklist': 'TokenBlacklist'
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

        except Exception as e:
            print(f"MongoDB connection error: {str(e)}")
            raise

    def _initialize_collections(self):
        """Initialize MongoDB collections with schema validation"""
        # Check if collections exist, if not create them with validators
        collection_names = self._db.list_collection_names()
        
        # Initialize each collection if it doesn't exist
        for collection in self.COLLECTIONS.values():
            if collection not in collection_names:
                self.setup_collection(collection, create=True)
            else:
                self.setup_collection(collection, create=False)
    
    def setup_collection(self, collection_name, create=True, verbose=False):
        """Set up a collection with its schema and indexes
        
        Args:
            collection_name: Name of the collection to set up
            create: Whether to create the collection (True) or just update schema/indexes (False)
            verbose: Whether to print verbose output
        """
        if verbose:
            print(f"Setting up collection: {collection_name}")
            
        # Create the collection if requested
        if create:
            if verbose:
                print(f"Creating collection: {collection_name}")
            
            # Select the right schema based on collection name
            if collection_name == self.COLLECTIONS['Users']:
                self._db.create_collection(collection_name, validator=USER_SCHEMA)
            elif collection_name == self.COLLECTIONS['Links']:
                self._db.create_collection(collection_name, validator=LINK_SCHEMA)
            elif collection_name == self.COLLECTIONS['MessagesDays']:
                self._db.create_collection(collection_name, validator=MESSAGE_DAY_SCHEMA)
            elif collection_name == self.COLLECTIONS['PasswordResets']:
                self._db.create_collection(collection_name, validator=PASSWORD_RESET_SCHEMA)
            elif collection_name == self.COLLECTIONS['TokenBlacklist']:
                self._db.create_collection(collection_name, validator=TOKEN_BLACKLIST_SCHEMA)
        else:
            # Just update the schema validation
            if collection_name == self.COLLECTIONS['Users']:
                self._db.command("collMod", collection_name, validator=USER_SCHEMA)
            elif collection_name == self.COLLECTIONS['Links']:
                self._db.command("collMod", collection_name, validator=LINK_SCHEMA)
            elif collection_name == self.COLLECTIONS['MessagesDays']:
                self._db.command("collMod", collection_name, validator=MESSAGE_DAY_SCHEMA)
            elif collection_name == self.COLLECTIONS['PasswordResets']:
                self._db.command("collMod", collection_name, validator=PASSWORD_RESET_SCHEMA)
            elif collection_name == self.COLLECTIONS['TokenBlacklist']:
                self._db.command("collMod", collection_name, validator=TOKEN_BLACKLIST_SCHEMA)
        
        # Create indexes (same regardless of create mode)
        if collection_name == self.COLLECTIONS['Users']:
            self._ensure_index(self._db[collection_name], [("BLEOId", ASCENDING)], unique=True)
            self._ensure_index(self._db[collection_name], [("email", ASCENDING)], unique=True)
            if verbose:
                print("  - Created indexes on BLEOId and email")
                
        elif collection_name == self.COLLECTIONS['Links']:
            self._ensure_index(self._db[collection_name], [("BLEOIdPartner1", ASCENDING)], unique=True)
            if verbose:
                print("  - Created index on BLEOIdPartner1")
                
        elif collection_name == self.COLLECTIONS['MessagesDays']:
            self._ensure_index(
                self._db[collection_name],
                [("BLEOId", ASCENDING), ("date", ASCENDING)],
                unique=True
            )
            if verbose:
                print("  - Created compound index on BLEOId and date")
                
        elif collection_name == self.COLLECTIONS['PasswordResets']:
            self._ensure_index(self._db[collection_name], [("token", ASCENDING)], unique=True)
            self._ensure_index(self._db[collection_name], [("expires", ASCENDING)], expireAfterSeconds=0)
            if verbose:
                print("  - Created indexes on token and expires")
                
        elif collection_name == self.COLLECTIONS['TokenBlacklist']:
            self._ensure_index(self._db[collection_name], [("token", ASCENDING)], unique=True)
            self._ensure_index(self._db[collection_name], [("expires_at", ASCENDING)], expireAfterSeconds=0)
            if verbose:
                print("  - Created indexes on token and expires_at")
    
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