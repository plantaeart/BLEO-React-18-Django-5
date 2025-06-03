from django.core.management.base import BaseCommand
from utils.mongodb_utils import MongoDB

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
            # Get MongoDB instance (without initialization)
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
            
            # Reinitialize the entire system using MongoDB utils
            self.stdout.write(self.style.NOTICE("Reinitializing collections and parameters..."))
            
            try:
                # Use the same logic as MongoDB initialization
                mongo_instance.initialize_system()
                
                self.stdout.write(self.style.SUCCESS("✅ Collections and parameters reinitialized successfully."))
                
                # Show current parameter values
                from utils.parameter_manager import ParameterManager
                app_version = ParameterManager.get_app_version()
                debug_level = ParameterManager.get_debug_level()
                
                self.stdout.write(self.style.SUCCESS(
                    f"Current parameters - Version: {app_version}, Debug Level: {debug_level}"
                ))
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error during reinitialization: {str(e)}")
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS("✅ Collections reset complete.")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {str(e)}")
            )