from tests.base_test import BLEOBaseTest, run_test_with_output
from rest_framework.test import APIClient
from api.Views.MessagesDays.MessagesDaysView import (
    MessageDayListCreateView, 
    MessageDayDetailView, 
    MoodOptionsView, 
    MessageDayCreateView
)
from models.MessagesDays import MessagesDays
from models.User import User
from utils.mongodb_utils import MongoDB
from django.contrib.auth.hashers import make_password
import json
import time
import random
from datetime import datetime, timedelta
from django.urls import path
from django.test import override_settings
from models.enums.MessageType import MessageType
from models.enums.MoodType import MoodType
from models.enums.EnergyLevelType import EnergyLevelType
from models.enums.PleasantnessType import PleasantnessType
from models.enums.MoodQuadrantType import MoodQuadrantType
from utils.validation_patterns import ValidationRules

# Set up URL configuration for testing
urlpatterns = [
    path('messagesdays/', MessageDayListCreateView.as_view(), name='message-day-list'),
    path('messagesdays/<str:bleoid>/', MessageDayCreateView.as_view(), name='message-day-create-with-id'),
    path('messagesdays/<str:bleoid>/<str:date>/', MessageDayDetailView.as_view(), name='message-day-detail'),
    path('mood-options/', MoodOptionsView.as_view(), name='mood-options'),
]

@override_settings(ROOT_URLCONF=__name__)
class MessagesDaysViewTest(BLEOBaseTest):
    """Test cases for MessagesDays views with MongoDB test collections"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        super().setUpClass()
        # Create MongoDB connection with test collections
        cls.db_client = MongoDB.get_client()
        
        # Use test collections with timestamp to avoid conflicts
        timestamp = int(time.time())
        cls.test_suffix = f"test_{timestamp}_{random.randint(1000, 9999)}"
        cls.users_collection_name = f"Users_{cls.test_suffix}"
        cls.messages_days_collection_name = f"MessagesDays_{cls.test_suffix}"
        cls.links_collection_name = f"Links_{cls.test_suffix}"  # NEW: Add Links collection
        
        # Store original collection names to restore later
        cls.original_users_collection = MongoDB.COLLECTIONS['Users']
        cls.original_messages_days_collection = MongoDB.COLLECTIONS['MessagesDays']
        cls.original_links_collection = MongoDB.COLLECTIONS['Links'] if 'Links' in MongoDB.COLLECTIONS else None  # NEW
        
        # Override collection names for testing
        MongoDB.COLLECTIONS['Users'] = cls.users_collection_name
        MongoDB.COLLECTIONS['MessagesDays'] = cls.messages_days_collection_name
        MongoDB.COLLECTIONS['Links'] = cls.links_collection_name  # NEW
        
        print(f"🔧 Created test collections: {cls.users_collection_name}, {cls.messages_days_collection_name}, {cls.links_collection_name}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Use the MongoDB instance to get the database
            db = MongoDB.get_instance().get_db()
            
            # Drop test collections
            db.drop_collection(cls.users_collection_name)
            db.drop_collection(cls.messages_days_collection_name)
            db.drop_collection(cls.links_collection_name)  # NEW
            
            # Restore original collection names
            MongoDB.COLLECTIONS['Users'] = cls.original_users_collection
            MongoDB.COLLECTIONS['MessagesDays'] = cls.original_messages_days_collection
            if cls.original_links_collection:
                MongoDB.COLLECTIONS['Links'] = cls.original_links_collection
            elif 'Links' in MongoDB.COLLECTIONS:
                del MongoDB.COLLECTIONS['Links']
            
            print(f"🧹 Dropped test collections: {cls.users_collection_name}, {cls.messages_days_collection_name}, {cls.links_collection_name}")
        except Exception as e:
            print(f"❌ Error during teardown: {str(e)}")
        finally:
            super().tearDownClass()
    
    def setUp(self):
        """Set up the test environment before each test"""
        super().setUp()
        # Use APIClient for testing
        self.client = APIClient()
        
        try:
            # Get test collections
            self.db_users = MongoDB.get_instance().get_collection('Users')
            self.db_messages_days = MongoDB.get_instance().get_collection('MessagesDays')
            self.db_links = MongoDB.get_instance().get_collection('Links')  # NEW
            
            # Clear collections before each test
            self.db_users.delete_many({})
            self.db_messages_days.delete_many({})
            self.db_links.delete_many({})  # NEW
            
            # Create sample test users
            self.test_users = [
                {
                    'bleoid': 'ABC123',
                    'email': 'user1@example.com',
                    'password': make_password('Password123'),
                    'userName': 'TestUser1', 
                    'bio': 'Test bio 1',
                    'email_verified': True,
                    'preferences': {'theme': 'light'},
                    'last_login': datetime.now(),
                    'created_at': datetime.now()
                },
                {
                    'bleoid': 'DEF456',
                    'email': 'user2@example.com',
                    'password': make_password('Password456'),
                    'userName': 'TestUser2',
                    'bio': 'Test bio 2',
                    'email_verified': False,
                    'preferences': {'theme': 'dark'},
                    'last_login': datetime.now(),
                    'created_at': datetime.now()
                },
                {
                    'bleoid': 'GHI789',  # NEW: User with no link
                    'email': 'user3@example.com',
                    'password': make_password('Password789'),
                    'userName': 'TestUser3',
                    'bio': 'Test bio 3',
                    'email_verified': True,
                    'preferences': {'theme': 'dark'},
                    'last_login': datetime.now(),
                    'created_at': datetime.now()
                }
            ]
            
            # Insert test users
            self.user_ids = []
            for i, user in enumerate(self.test_users):
                try:
                    result = self.db_users.insert_one(user)
                    self.user_ids.append(result.inserted_id)
                    print(f"  ✅ Created test user {i+1}: {user['bleoid']} / {user['email']}")
                except Exception as e:
                    print(f"  ❌ Failed to create test user {i+1}: {str(e)}")
                    raise
            
            # NEW: Create links between users
            self.test_links = [
                {
                    'bleoidPartner1': 'ABC123',
                    'bleoidPartner2': 'DEF456',
                    'status': 'accepted',
                    'created_at': datetime.now()
                }
            ]
            
            # Insert test links
            self.link_ids = []
            for i, link in enumerate(self.test_links):
                try:
                    result = self.db_links.insert_one(link)
                    self.link_ids.append(result.inserted_id)
                    print(f"  ✅ Created test link {i+1} between: {link['bleoidPartner1']} and {link['bleoidPartner2']}")
                except Exception as e:
                    print(f"  ❌ Failed to create test link {i+1}: {str(e)}")
                    raise
            
            # Update test_messages_days data setup
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_date = datetime(yesterday.year, yesterday.month, yesterday.day)
            today_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
            
            self.test_messages_days = [
                {
                    'from_bleoid': 'ABC123',
                    'to_bleoid': 'DEF456',
                    'date': yesterday_date,
                    'messages': [
                        {
                            'id': 1,
                            'title': 'Test Message 1',
                            'text': 'Content of test message 1',
                            'type': MessageType.THOUGHTS.value,
                            'created_at': yesterday
                        },
                        {
                            'id': 2,
                            'title': 'Test Message 2',
                            'text': 'Content of test message 2',
                            'type': MessageType.SOUVENIR.value,
                            'created_at': yesterday + timedelta(hours=2)
                        }
                    ],
                    'mood': MoodType.JOYFUL.value,
                    'energy_level': EnergyLevelType.HIGH.value,
                    'pleasantness': PleasantnessType.PLEASANT.value
                },
                {
                    'from_bleoid': 'DEF456',
                    'to_bleoid': 'ABC123',
                    'date': today_date,
                    'messages': [
                        {
                            'id': 1,
                            'title': 'Test Message 3',
                            'text': 'Content of test message 3',
                            'type': MessageType.LOVE_MESSAGE.value,
                            'created_at': datetime.now() - timedelta(hours=3)
                        }
                    ],
                    'mood': MoodType.CALM.value,
                    'energy_level': EnergyLevelType.LOW.value,
                    'pleasantness': PleasantnessType.PLEASANT.value
                }
            ]
            
            # Insert test messages days
            self.message_day_ids = []
            for i, message_day in enumerate(self.test_messages_days):
                try:
                    result = self.db_messages_days.insert_one(message_day)
                    self.message_day_ids.append(result.inserted_id)
                    print(f"  ✅ Created test message day {i+1} from {message_day['from_bleoid']} to {message_day['to_bleoid']}")
                except Exception as e:
                    print(f"  ❌ Failed to create test message day {i+1}: {str(e)}")
                    raise
            
            print(f"🔧 Test environment setup with {len(self.user_ids)} users, {len(self.link_ids)} links, and {len(self.message_day_ids)} messages days")
            
        except Exception as e:
            print(f"❌ Test setup failed: {str(e)}")
            raise
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear collections
        self.db_users.delete_many({})
        self.db_messages_days.delete_many({})
        self.db_links.delete_many({})
        super().tearDown()
    
    # ====== Helper Methods ======
    
    def format_date(self, date):
        """Format a datetime object to DD-MM-YYYY string"""
        return date.strftime(ValidationRules.STANDARD_DATE_FORMAT)
    
    def get_today_date_str(self):
        """Get today's date as DD-MM-YYYY string"""
        today = datetime.now()
        return self.format_date(today)
    
    def get_yesterday_date_str(self):
        """Get yesterday's date as DD-MM-YYYY string"""
        yesterday = datetime.now() - timedelta(days=1)
        return self.format_date(yesterday)
    
    # ====== MessageDayListCreateView Tests ======
    
    def test_get_all_messages_days(self):
        """Test getting all messages days"""
        # Make request
        response = self.client.get('/messagesdays/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(response.data['successMessage'], 'Messages days retrieved successfully')
        
        # Verify both messages days are returned
        from_bleoids = [day['from_bleoid'] for day in response.data['data']]
        self.assertIn('ABC123', from_bleoids)
        self.assertIn('DEF456', from_bleoids)
        
        print("  🔹 Successfully retrieved all messages days")
    
    def test_get_messages_days_by_bleoid(self):
        """Test getting messages days filtered by from_bleoid"""
        # Make request
        response = self.client.get('/messagesdays/', {'fromBleoid': 'ABC123'})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['from_bleoid'], 'ABC123')
        self.assertEqual(response.data['data'][0]['to_bleoid'], 'DEF456')
        self.assertEqual(response.data['data'][0]['mood'], MoodType.JOYFUL.value)
        self.assertEqual(response.data['data'][0]['quadrant'], MoodQuadrantType.YELLOW.value)
        self.assertEqual(response.data['data'][0]['energy_level'], EnergyLevelType.HIGH.value)
        self.assertEqual(response.data['data'][0]['pleasantness'], PleasantnessType.PLEASANT.value)
        
        print("  🔹 Successfully retrieved messages days filtered by from_bleoid")
    
    def test_get_messages_days_by_date(self):
        """Test getting messages days filtered by date"""
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.get('/messagesdays/', {'date': yesterday_str})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['from_bleoid'], 'ABC123')
        self.assertEqual(response.data['data'][0]['date'], yesterday_str)
        
        print("  🔹 Successfully retrieved messages days filtered by date")
    
    def test_get_messages_days_by_mood(self):
        """Test getting messages days filtered by mood"""
        # Make request
        response = self.client.get('/messagesdays/', {'mood': MoodType.JOYFUL.value})  
    
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['mood'], MoodType.JOYFUL.value)  
    
        print("  🔹 Successfully retrieved messages days filtered by mood")
    
    def test_get_messages_days_by_energy_level(self):
        """Test getting messages days filtered by energy level"""
        # Make request
        response = self.client.get('/messagesdays/', {'energy_level': EnergyLevelType.HIGH.value})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['energy_level'], EnergyLevelType.HIGH.value)
        
        print("  🔹 Successfully retrieved messages days filtered by energy level")
    
    def test_create_message_day_success(self):
        """Test creating a new message day"""
        # Request data
        today = datetime.now()
        message_day_data = {
            'from_bleoid': 'ABC123',
            'to_bleoid': 'DEF456',
            'date': self.format_date(today + timedelta(days=1)),  # Tomorrow
            'messages': [
                {
                    'title': 'New Message',
                    'text': 'Content of new message',
                    'type': MessageType.THOUGHTS.value
                }
            ],
            'mood': MoodType.EXCITED.value,
            'energy_level': EnergyLevelType.HIGH.value,
            'pleasantness': PleasantnessType.PLEASANT.value
        }
        
        # Make request
        response = self.client.post('/messagesdays/', message_day_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['from_bleoid'], 'ABC123')
        self.assertEqual(response.data['data']['to_bleoid'], 'DEF456')
        self.assertEqual(response.data['data']['mood'], MoodType.EXCITED.value)
        self.assertEqual(response.data['data']['quadrant'], MoodQuadrantType.YELLOW.value)
        self.assertEqual(len(response.data['data']['messages']), 1)
        self.assertEqual(response.data['data']['messages'][0]['title'], 'New Message')
        self.assertEqual(response.data['successMessage'], 'Message day created successfully')
        
        # Verify message IDs were generated
        self.assertIsNotNone(response.data['data']['messages'][0]['id'])
        
        # Verify message day was created in database
        created_message_day = self.db_messages_days.find_one({
            'from_bleoid': 'ABC123', 
            'to_bleoid': 'DEF456',
            'mood': MoodType.EXCITED
        })
        self.assertIsNotNone(created_message_day)
        
        print("  🔹 Successfully created message day")
    
    def test_create_message_day_no_link(self):
        """Test error when creating message day for user with no link"""
        # Request data for user without a link
        message_day_data = {
            'from_bleoid': 'GHI789',  # No link for this user
            'date': self.get_today_date_str(),
            'messages': [
                {
                    'title': 'No Link Message',
                    'text': 'This should fail',
                    'type': MessageType.THOUGHTS.value
                }
            ],
            'mood': MoodType.SAD.value
        }
        
        # Make request
        response = self.client.post('/messagesdays/', message_day_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertTrue('not linked' in response.data['errorMessage'])
        
        print("  🔹 Properly rejected message day for user with no link")
    
    def test_create_message_day_invalid_link(self):
        """Test error when creating message day with invalid link"""
        # Request data with invalid to_bleoid
        message_day_data = {
            'from_bleoid': 'ABC123',
            'to_bleoid': 'GHI789',  # These users are not linked
            'date': self.get_today_date_str(),
            'messages': [
                {
                    'title': 'Invalid Link Message',
                    'text': 'This should fail',
                    'type': MessageType.THOUGHTS.value
                }
            ],
            'mood': MoodType.MIXED.value
        }
        
        # Make request
        response = self.client.post('/messagesdays/', message_day_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertTrue('No accepted link found' in response.data['errorMessage'])
        
        print("  🔹 Properly rejected message day with invalid link")
    
    def test_create_message_day_auto_link_discovery(self):
        """Test creating message day where link is auto-discovered"""
        # Request data without to_bleoid - should be auto-discovered
        message_day_data = {
            'from_bleoid': 'ABC123',
            # No to_bleoid provided
            'date': self.get_today_date_str(),
            'messages': [
                {
                    'title': 'Auto Link Message',
                    'text': 'This should work',
                    'type': MessageType.THOUGHTS.value
                }
            ],
            'mood': MoodType.JOYFUL.value,
            'energy_level': EnergyLevelType.HIGH.value,
            'pleasantness': PleasantnessType.PLEASANT.value
        }
        
        # Make request
        response = self.client.post('/messagesdays/', message_day_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['from_bleoid'], 'ABC123')
        self.assertEqual(response.data['data']['to_bleoid'], 'DEF456')  
        
        print("  🔹 Successfully created message day with auto-discovered link")
    
    def test_create_message_day_duplicate_error(self):
        """Test error when creating duplicate message day for same date"""
        # Get today's date for the message day that already exists
        today = datetime.now()
        today_str = self.format_date(today)
        
        # Request data with same date, from_bleoid and to_bleoid
        message_day_data = {
            'from_bleoid': 'DEF456',
            'to_bleoid': 'ABC123',
            'date': today_str,
            'messages': [
                {
                    'title': 'Duplicate Message',
                    'text': 'This should fail',
                    'type': MessageType.THOUGHTS.value
                }
            ],
            'mood': MoodType.SAD.value,
            'energy_level': EnergyLevelType.LOW.value,
            'pleasantness': PleasantnessType.UNPLEASANT.value
        }
        
        # Make request
        response = self.client.post('/messagesdays/', message_day_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['errorType'], 'DuplicateError')
        self.assertTrue('already exists' in response.data['errorMessage'])
        
        print("  🔹 Properly rejected duplicate message day")
    
    def test_create_message_day_invalid_user(self):
        """Test error when creating message day for nonexistent user"""
        # Request data with nonexistent user
        message_day_data = {
            'from_bleoid': 'NOP001',
            'to_bleoid': 'NOP002',
            'date': self.get_today_date_str(),
            'messages': [
                {
                    'title': 'Invalid User Message',
                    'text': 'This should fail',
                    'type': MessageType.THOUGHTS.value
                }
            ],
            'mood': MoodType.MIXED.value
        }
        
        # Make request
        response = self.client.post('/messagesdays/', message_day_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        self.assertTrue('not found' in response.data['errorMessage'])
        
        print("  🔹 Properly rejected message day for nonexistent user")
    
    def test_create_message_day_invalid_data(self):
        """Test error when creating message day with invalid data"""
        # Request data with invalid mood
        message_day_data = {
            'from_bleoid': 'ABC123',
            'to_bleoid': 'DEF456',
            'date': self.get_today_date_str(),
            'energy_level': 'invalid_level'  # Invalid energy level
        }
        
        # Make request
        response = self.client.post('/messagesdays/', message_day_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertIn('energy_level', response.data['validationErrors'])
        
        print("  🔹 Properly rejected invalid message day data")
    
    # ====== MessageDayDetailView Tests ======
    
    def test_get_message_day_by_bleoid_and_date(self):
        """Test getting a specific message day by from_bleoid and date"""
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.get(f'/messagesdays/ABC123/{yesterday_str}/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['from_bleoid'], 'ABC123')
        self.assertEqual(response.data['data']['to_bleoid'], 'DEF456')
        self.assertEqual(response.data['data']['date'], yesterday_str)
        self.assertEqual(response.data['data']['mood'], MoodType.JOYFUL.value)
        self.assertEqual(len(response.data['data']['messages']), 2)
        self.assertEqual(response.data['successMessage'], 'Messages days retrieved successfully')
        
        print("  🔹 Successfully retrieved message day by from_bleoid and date")
    
    def test_get_nonexistent_message_day(self):
        """Test error when getting a nonexistent message day"""
        # Make request with valid from_bleoid but future date
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = self.format_date(tomorrow)
        response = self.client.get(f'/messagesdays/ABC123/{tomorrow_str}/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled nonexistent message day")
    
    def test_update_message_day_success(self):
        """Test updating a message day successfully"""
        # Update data
        update_data = {
            'mood': MoodType.RELAXED.value,
            'energy_level': EnergyLevelType.LOW.value,
            'pleasantness': PleasantnessType.PLEASANT.value
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.put(f'/messagesdays/ABC123/{yesterday_str}/', update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['mood'], MoodType.RELAXED.value)
        self.assertEqual(response.data['data']['energy_level'], EnergyLevelType.LOW.value)
        self.assertEqual(response.data['data']['pleasantness'], PleasantnessType.PLEASANT.value)
        self.assertEqual(response.data['data']['quadrant'], MoodQuadrantType.GREEN.value)
        self.assertEqual(response.data['successMessage'], 'Message day updated successfully')
        
        # from_bleoid/to_bleoid should remain intact
        self.assertEqual(response.data['data']['from_bleoid'], 'ABC123')
        self.assertEqual(response.data['data']['to_bleoid'], 'DEF456')
        
        # Verify changes in database
        yesterday_date = datetime.now() - timedelta(days=1)
        yesterday_midnight = datetime(yesterday_date.year, yesterday_date.month, yesterday_date.day)
        updated_message_day = self.db_messages_days.find_one({
            'from_bleoid': 'ABC123',
            'date': yesterday_midnight
        })
        self.assertEqual(updated_message_day['mood'], MoodType.RELAXED.value)  
        
        print("  🔹 Successfully updated message day")
    
    # ====== MessageDayCreateView Tests ======
    
    def test_create_message_day_with_bleoid_in_url(self):
        """Test creating a message day with from_bleoid in URL path"""
        # Request data (without from_bleoid, will be taken from URL)
        message_data = {
            'date': self.format_date(datetime.now() + timedelta(days=1)),  # Tomorrow
            'messages': [
                {
                    'title': 'Path-based Message',
                    'text': 'Created via URL path',
                    'type': MessageType.THOUGHTS.value
                }
            ],
            'mood': MoodType.ENTHUSIASTIC.value,
            'energy_level': EnergyLevelType.HIGH.value,
            'pleasantness': PleasantnessType.PLEASANT.value
        }
        
        # Make request
        response = self.client.post('/messagesdays/ABC123/', message_data, format='json')

        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['from_bleoid'], 'ABC123')
        self.assertEqual(response.data['data']['to_bleoid'], 'DEF456')  
        self.assertEqual(response.data['data']['mood'], MoodType.ENTHUSIASTIC.value)  
        self.assertEqual(response.data['data']['messages'][0]['title'], 'Path-based Message')
        
        print("  🔹 Successfully created message day with from_bleoid in path")
    
    def test_create_message_day_with_explicit_to_bleoid(self):
        """Test creating a message day with explicit to_bleoid"""
        # Request data with explicit to_bleoid
        message_data = {
            'to_bleoid': 'DEF456',  # Explicit to_bleoid
            'date': self.format_date(datetime.now() + timedelta(days=1)),  # Tomorrow
            'messages': [
                {
                    'title': 'Explicit Link Message',
                    'text': 'Created with explicit link',
                    'type': MessageType.THOUGHTS.value
                }
            ],
            'mood': MoodType.CALM.value,
            'energy_level': EnergyLevelType.LOW.value,
            'pleasantness': PleasantnessType.PLEASANT.value
        }
        
        # Make request
        response = self.client.post('/messagesdays/ABC123/', message_data, format='json')

        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['from_bleoid'], 'ABC123')
        self.assertEqual(response.data['data']['to_bleoid'], 'DEF456')
        
        print("  🔹 Successfully created message day with explicit to_bleoid")
    
    def test_create_message_day_no_link_with_url(self):
        """Test error when creating message day via URL for user with no link"""
        # Message data for path-based request
        message_data = {
            'date': self.get_today_date_str(),
            'messages': [
                {
                    'title': 'No Link Path Message',
                    'text': 'This should fail',
                    'type': MessageType.THOUGHTS.value
                }
            ],
            'mood': MoodType.SAD.value
        }
        
        # Make request with user that has no link
        response = self.client.post('/messagesdays/GHI789/', message_data, format='json')

        # Check response
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertTrue('not linked' in response.data['errorMessage'])
        
        print("  🔹 Properly rejected path-based request for user with no link")
    
    def test_delete_all_user_messages_days(self):
        """Test deleting all messages days for a user"""
        # Add a second message day for the same user
        today_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
        second_message_day = {
            'from_bleoid': 'ABC123',
            'to_bleoid': 'DEF456',
            'date': today_date,
            'messages': [
                {
                    'id': 1,
                    'title': 'Another Test Message',
                    'text': 'Another test content',
                    'type': MessageType.THOUGHTS.value,
                    'created_at': datetime.now()
                }
            ],
            'mood': MoodType.CALM.value
        }
        self.db_messages_days.insert_one(second_message_day)
        
        # Verify two messages days exist
        count_before = self.db_messages_days.count_documents({'from_bleoid': 'ABC123'})
        self.assertEqual(count_before, 2)
        
        # Make delete request
        response = self.client.delete('/messagesdays/ABC123/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['deleted_count'], 2)
        
        # Verify both messages days were deleted
        count_after = self.db_messages_days.count_documents({'from_bleoid': 'ABC123'})
        self.assertEqual(count_after, 0)
        
        print("  🔹 Successfully deleted all messages days for a user")