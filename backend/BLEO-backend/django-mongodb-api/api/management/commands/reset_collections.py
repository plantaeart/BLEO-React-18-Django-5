from django.core.management.base import BaseCommand
from utils.mongodb_utils import MongoDB
from utils.mongodb_schemas import (
    USER_SCHEMA, 
    LINK_SCHEMA, 
    MESSAGE_DAY_SCHEMA, 
    PASSWORD_RESET_SCHEMA,
    TOKEN_BLACKLIST_SCHEMA
)
from pymongo import ASCENDING
from models.AppParameters import AppParameters
from config.AppCurrentState import APP_VERSION, DEBUG_LEVEL

class Command(BaseCommand):
    help = 'Drops all collections and recreates them with proper schema validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        try:
            # Get MongoDB instance
            mongo_instance = MongoDB.get_instance()
            db = mongo_instance.get_db()
            
            # Get existing collections
            collections = db.list_collection_names()
            self.stdout.write(f"Found {len(collections)} collections: {', '.join(collections)}")
            
            # Confirm before proceeding unless --force is used
            if not options['force']:
                self.stdout.write(self.style.WARNING("⚠️ WARNING: This will delete ALL data in all collections."))
                confirm = input("Type 'yes' to continue: ")
                if confirm.lower() != 'yes':
                    self.stdout.write("Operation cancelled.")
                    return
            
            # Drop all existing collections
            for collection_name in collections:
                self.stdout.write(f"Dropping collection: {collection_name}")
                db.drop_collection(collection_name)
            
            self.stdout.write(self.style.SUCCESS("All collections dropped successfully."))
            
            # Recreate collections with schema validation using the MongoDB utility class
            # to ensure consistency across the application
            for logical_name, actual_name in MongoDB.COLLECTIONS.items():
                self.stdout.write(f"Creating {logical_name} collection...")
                # Use the setup_collection method with verbose output
                mongo_instance.setup_collection(actual_name, create=True, verbose=True)
            
            # Initialize AppParameters with config values from AppCurrentState
            self.stdout.write(self.style.NOTICE(
                f"Initializing AppParameters with configuration from AppCurrentState... "
                f"(Version: {APP_VERSION}, Debug Level: {DEBUG_LEVEL})"
            ))
            try:
                # Create AppParameters with values from AppCurrentState.py using new model structure
                default_params = [
                    AppParameters(
                        id=0,
                        param_name=AppParameters.PARAM_DEBUG_LEVEL,
                        param_value=DEBUG_LEVEL
                    ),
                    AppParameters(
                        id=1,
                        param_name=AppParameters.PARAM_APP_VERSION,
                        param_value=APP_VERSION
                    )
                ]
                
                # Insert into collection
                app_params_collection = db[MongoDB.COLLECTIONS['AppParameters']]
                for param in default_params:
                    app_params_collection.insert_one(param.to_dict())
                
                self.stdout.write(self.style.SUCCESS("AppParameters initialized successfully."))
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Warning: Could not initialize AppParameters: {str(e)}")
                )
            
            self.stdout.write(
                self.style.SUCCESS("✅ Collections reset complete. All collections have been recreated with proper schema validation.")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {str(e)}")
            )