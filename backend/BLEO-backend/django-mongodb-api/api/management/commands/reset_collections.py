from django.core.management.base import BaseCommand
from utils.mongodb_utils import MongoDB
from utils.mongodb_schemas import USER_SCHEMA, LINK_SCHEMA, MESSAGE_DAY_SCHEMA
from pymongo import ASCENDING

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
            db = MongoDB.get_instance().get_db()
            
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
            
            # Recreate collections with schema validation
            
            # Users collection
            self.stdout.write("Creating Users collection...")
            db.create_collection("Users", validator=USER_SCHEMA)
            db.Users.create_index([("BLEOId", ASCENDING)], unique=True)
            db.Users.create_index([("mail", ASCENDING)], unique=True)
            
            # Links collection
            self.stdout.write("Creating Links collection...")
            db.create_collection("Links", validator=LINK_SCHEMA)
            # Create index on BLEOIdPartner1
            db.Links.create_index([("BLEOIdPartner1", ASCENDING)], unique=True)
            
            # Message days collection
            self.stdout.write("Creating MessagesDays collection...")
            db.create_collection("MessagesDays", validator=MESSAGE_DAY_SCHEMA)
            # Create compound index for BLEOId and date
            db.MessagesDays.create_index(
                [("BLEOId", ASCENDING), ("date", ASCENDING)], 
                unique=True
            )
            
            self.stdout.write(
                self.style.SUCCESS("✅ Collections reset complete. All collections have been recreated with proper schema validation.")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {str(e)}")
            )