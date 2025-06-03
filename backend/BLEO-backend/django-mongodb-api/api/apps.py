import os
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        """This runs only once when Django starts"""
        # Check if this is the main process (not the reloader process)
        if os.environ.get('RUN_MAIN') == 'true':
            print("🌟 Django API app ready - initializing MongoDB...")
            
            # Import and initialize MongoDB system
            from utils.mongodb_utils import MongoDB
            try:
                MongoDB.initialize()
                print("🎉 MongoDB initialization completed successfully!")
            except Exception as e:
                print(f"💥 Failed to initialize MongoDB: {str(e)}")
                # You might want to raise this exception to prevent the server from starting
        else:
            print("🔄 Django reloader process detected, skipping MongoDB initialization...")