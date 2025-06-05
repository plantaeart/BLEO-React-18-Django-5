from django.core.management.base import BaseCommand
from utils.mongodb_utils import MongoDB
from models.Link import Link
from datetime import datetime

class Command(BaseCommand):
    help = 'Creates Link records for all users who do not have one'

    def handle(self, *args, **kwargs):
        try:
            # Get database connections
            db = MongoDB.get_instance().get_db()
            users_collection = db['Users']
            links_collection = db['Links']
            
            # Find all users
            users = list(users_collection.find({}, {'bleoid': 1}))
            self.stdout.write(f"Found {len(users)} users total")
            
            # Counter for new links
            new_links_count = 0
            
            for user in users:
                bleoid = user.get('bleoid')
                
                if bleoid is None:
                    self.stdout.write(self.style.WARNING(f"User with ID {user['_id']} has no bleoid, skipping"))
                    continue
                
                # Check if link already exists for this user
                existing_link = links_collection.find_one({"bleoidPartner1": bleoid})
                
                if existing_link:
                    self.stdout.write(f"User bleoid={bleoid} already has a link")
                else:
                    # Create a new link
                    link = Link(
                        bleoidPartner1=bleoid,
                        bleoidPartner2=None,
                        created_at=datetime.now()
                    )
                    
                    # Insert into MongoDB
                    result = links_collection.insert_one(link.to_dict())
                    new_links_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Created link for user bleoid={bleoid}, ID: {result.inserted_id}")
                    )
            
            # Final statistics
            self.stdout.write(
                self.style.SUCCESS(f"Command completed. Created {new_links_count} new links.")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error executing command: {str(e)}")
            )