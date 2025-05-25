import os
from pymongo import MongoClient, ASCENDING
from environs import Env
from .mongodb_schemas import USER_SCHEMA, LINK_SCHEMA, MESSAGE_DAY_SCHEMA

env = Env()
env.read_env()

class MongoDB:
    """MongoDB connection utility class"""
    
    _instance = None
    _client = None
    _db = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MongoDB()
        return cls._instance

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
        
        # Users collection
        if "Users" not in collection_names:
            self._db.create_collection("Users", validator=USER_SCHEMA)
            # Create unique index on BLEOId instead of id
            self._db.users.create_index([("BLEOId", ASCENDING)], unique=True)
            self._db.users.create_index([("mail", ASCENDING)], unique=True)
        
        # Links collection
        if "Links" not in collection_names:
            self._db.create_collection("Links", validator=LINK_SCHEMA)
            # Create compound index for both partner IDs
            self._db.links.create_index(
                [("BLEOIdPartner1", ASCENDING), ("BLEOIdPartner2", ASCENDING)], 
                unique=True
            )
        
        # Message days collection
        if "Messages_day" not in collection_names:
            self._db.create_collection("Messages_day", validator=MESSAGE_DAY_SCHEMA)
            # Create compound index for BLEOId and date
            self._db.message_days.create_index(
                [("BLEOId", ASCENDING), ("date", ASCENDING)], 
                unique=True
            )
    
    def get_db(self):
        return self._db
    
    def get_collection(self, collection_name):
        return self._db[collection_name]