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
        
        # Store original collection names to restore later
        cls.original_users_collection = MongoDB.COLLECTIONS['Users']
        cls.original_messages_days_collection = MongoDB.COLLECTIONS['MessagesDays']
        
        # Override collection names for testing
        MongoDB.COLLECTIONS['Users'] = cls.users_collection_name
        MongoDB.COLLECTIONS['MessagesDays'] = cls.messages_days_collection_name
        
        print(f"🔧 Created test collections: {cls.users_collection_name}, {cls.messages_days_collection_name}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Use the MongoDB instance to get the database
            db = MongoDB.get_instance().get_db()
            
            # Drop test collections
            db.drop_collection(cls.users_collection_name)
            db.drop_collection(cls.messages_days_collection_name)
            
            # Restore original collection names
            MongoDB.COLLECTIONS['Users'] = cls.original_users_collection
            MongoDB.COLLECTIONS['MessagesDays'] = cls.original_messages_days_collection
            
            print(f"🧹 Dropped test collections: {cls.users_collection_name}, {cls.messages_days_collection_name}")
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
            
            # Clear collections before each test
            self.db_users.delete_many({})
            self.db_messages_days.delete_many({})
            
            # Create sample test users
            self.test_users = [
                {
                    'BLEOId': 'ABC123',
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
                    'BLEOId': 'DEF456',
                    'email': 'user2@example.com',
                    'password': make_password('Password456'),
                    'userName': 'TestUser2',
                    'bio': 'Test bio 2',
                    'email_verified': False,
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
                    print(f"  ✅ Created test user {i+1}: {user['BLEOId']} / {user['email']}")
                except Exception as e:
                    print(f"  ❌ Failed to create test user {i+1}: {str(e)}")
                    raise
            
            # Create sample messages days
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_date = datetime(yesterday.year, yesterday.month, yesterday.day)
            today_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
            
            self.test_messages_days = [
                {
                    'BLEOId': 'ABC123',
                    'date': yesterday_date,
                    'messages': [
                        {
                            'id': 1,
                            'title': 'Test Message 1',
                            'text': 'Content of test message 1',
                            'type': MessageType.THOUGHTS,
                            'created_at': yesterday
                        },
                        {
                            'id': 2,
                            'title': 'Test Message 2',
                            'text': 'Content of test message 2',
                            'type': MessageType.SOUVENIR,
                            'created_at': yesterday + timedelta(hours=2)
                        }
                    ],
                    'mood': 'Happy',
                    'energy_level': 'high',
                    'pleasantness': 'pleasant'
                },
                {
                    'BLEOId': 'DEF456',
                    'date': today_date,
                    'messages': [
                        {
                            'id': 1,
                            'title': 'Test Message 3',
                            'text': 'Content of test message 3',
                            'type': MessageType.LOVE_MESSAGE,
                            'created_at': datetime.now() - timedelta(hours=3)
                        }
                    ],
                    'mood': 'Calm',
                    'energy_level': 'low',
                    'pleasantness': 'pleasant'
                }
            ]
            
            # Insert test messages days
            self.message_day_ids = []
            for i, message_day in enumerate(self.test_messages_days):
                try:
                    result = self.db_messages_days.insert_one(message_day)
                    self.message_day_ids.append(result.inserted_id)
                    print(f"  ✅ Created test message day {i+1} for user: {message_day['BLEOId']}")
                except Exception as e:
                    print(f"  ❌ Failed to create test message day {i+1}: {str(e)}")
                    raise
            
            print(f"🔧 Test environment setup with {len(self.user_ids)} users and {len(self.message_day_ids)} messages days")
            
        except Exception as e:
            print(f"❌ Test setup failed: {str(e)}")
            raise
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear collections
        self.db_users.delete_many({})
        self.db_messages_days.delete_many({})
        super().tearDown()
    
    # ====== Helper Methods ======
    
    def format_date(self, date):
        """Format a datetime object to DD-MM-YYYY string"""
        return date.strftime('%d-%m-%Y')
    
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
        self.assertEqual(response.data['successMessage'], 'Message days retrieved successfully')
        
        # Verify both messages days are returned
        bleoids = [day['BLEOId'] for day in response.data['data']]
        self.assertIn('ABC123', bleoids)
        self.assertIn('DEF456', bleoids)
        
        print("  🔹 Successfully retrieved all messages days")
    
    def test_get_messages_days_by_bleoid(self):
        """Test getting messages days filtered by BLEOId"""
        # Make request
        response = self.client.get('/messagesdays/', {'bleoid': 'ABC123'})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['BLEOId'], 'ABC123')
        self.assertEqual(response.data['data'][0]['mood'], 'Happy')
        self.assertEqual(response.data['data'][0]['quadrant'], 'yellow')
        
        print("  🔹 Successfully retrieved messages days filtered by BLEOId")
    
    def test_get_messages_days_by_date(self):
        """Test getting messages days filtered by date"""
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.get('/messagesdays/', {'date': yesterday_str})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['BLEOId'], 'ABC123')
        self.assertEqual(response.data['data'][0]['date'], yesterday_str)
        
        print("  🔹 Successfully retrieved messages days filtered by date")
    
    def test_get_messages_days_by_mood(self):
        """Test getting messages days filtered by mood"""
        # Make request
        response = self.client.get('/messagesdays/', {'mood': 'Happy'})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['mood'], 'Happy')
        
        print("  🔹 Successfully retrieved messages days filtered by mood")
    
    def test_get_messages_days_by_energy_level(self):
        """Test getting messages days filtered by energy level"""
        # Make request
        response = self.client.get('/messagesdays/', {'energy_level': 'high'})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['energy_level'], 'high')
        
        print("  🔹 Successfully retrieved messages days filtered by energy level")
    
    def test_create_message_day_success(self):
        """Test creating a new message day"""
        # Request data
        today = datetime.now()
        message_day_data = {
            'BLEOId': 'ABC123',
            'date': self.format_date(today + timedelta(days=1)),  # Tomorrow
            'messages': [
                {
                    'title': 'New Message',
                    'text': 'Content of new message',
                    'type': 'Thoughts'
                }
            ],
            'mood': 'Excited',
            'energy_level': 'high',
            'pleasantness': 'pleasant'
        }
        
        # Make request
        response = self.client.post('/messagesdays/', message_day_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['BLEOId'], 'ABC123')
        self.assertEqual(response.data['data']['mood'], 'Excited')
        self.assertEqual(response.data['data']['quadrant'], 'yellow')
        self.assertEqual(len(response.data['data']['messages']), 1)
        self.assertEqual(response.data['data']['messages'][0]['title'], 'New Message')
        self.assertEqual(response.data['successMessage'], 'Message day created successfully')
        
        # Verify message IDs were generated
        self.assertIsNotNone(response.data['data']['messages'][0]['id'])
        
        # Verify message day was created in database
        created_message_day = self.db_messages_days.find_one({'BLEOId': 'ABC123', 'mood': 'Excited'})
        self.assertIsNotNone(created_message_day)
        
        print("  🔹 Successfully created message day")
    
    def test_create_message_day_duplicate_error(self):
        """Test error when creating duplicate message day for same date"""
        # Get today's date for the message day that already exists for DEF456
        today = datetime.now()
        today_str = self.format_date(today)
        
        # Request data with same date
        message_day_data = {
            'BLEOId': 'DEF456',
            'date': today_str,
            'messages': [
                {
                    'title': 'Duplicate Message',
                    'text': 'This should fail',
                    'type': 'Thoughts'
                }
            ],
            'mood': 'Sad',
            'energy_level': 'low',
            'pleasantness': 'unpleasant'
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
            'BLEOId': 'NONEXISTENT',
            'date': self.get_today_date_str(),
            'messages': [
                {
                    'title': 'Invalid User Message',
                    'text': 'This should fail',
                    'type': 'Thoughts'
                }
            ],
            'mood': 'Confused'
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
            'BLEOId': 'ABC123',
            'date': self.get_today_date_str(),
            'energy_level': 'invalid_level'  # Invalid energy level
        }
        
        # Make request
        response = self.client.post('/messagesdays/', message_day_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertIn('energy_level', response.data['data']['validation_errors'])
        
        print("  🔹 Properly rejected invalid message day data")
    
    # ====== MessageDayDetailView Tests ======
    
    def test_get_message_day_by_bleoid_and_date(self):
        """Test getting a specific message day by BLEOId and date"""
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.get(f'/messagesdays/ABC123/{yesterday_str}/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['BLEOId'], 'ABC123')
        self.assertEqual(response.data['data']['date'], yesterday_str)
        self.assertEqual(response.data['data']['mood'], 'Happy')
        self.assertEqual(len(response.data['data']['messages']), 2)
        self.assertEqual(response.data['successMessage'], 'Message day retrieved successfully')
        
        print("  🔹 Successfully retrieved message day by BLEOId and date")
    
    def test_get_nonexistent_message_day(self):
        """Test error when getting a nonexistent message day"""
        # Make request with valid BLEOId but future date
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
            'mood': 'Relaxed',
            'energy_level': 'low',
            'pleasantness': 'pleasant'
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.put(f'/messagesdays/ABC123/{yesterday_str}/', update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['mood'], 'Relaxed')
        self.assertEqual(response.data['data']['energy_level'], 'low')
        self.assertEqual(response.data['data']['pleasantness'], 'pleasant')
        self.assertEqual(response.data['data']['quadrant'], 'green')
        self.assertEqual(response.data['successMessage'], 'Message day updated successfully')
        
        # Verify changes in database
        yesterday_date = datetime.now() - timedelta(days=1)
        yesterday_midnight = datetime(yesterday_date.year, yesterday_date.month, yesterday_date.day)
        updated_message_day = self.db_messages_days.find_one({
            'BLEOId': 'ABC123',
            'date': yesterday_midnight
        })
        self.assertEqual(updated_message_day['mood'], 'Relaxed')
        
        print("  🔹 Successfully updated message day")
    
    # ====== MessageDayCreateView Tests ======
    
    def test_create_message_day_with_bleoid_in_url(self):
        """Test creating a message day with BLEOId in URL path"""
        # Request data (without BLEOId, will be taken from URL)
        message_data = {
            'date': self.format_date(datetime.now() + timedelta(days=1)),  # Tomorrow
            'messages': [
                {
                    'title': 'Path-based Message',
                    'text': 'Created via URL path',
                    'type': 'Thoughts'
                }
            ],
            'mood': 'Energetic',
            'energy_level': 'high',
            'pleasantness': 'pleasant'
        }
        
        # Make request
        response = self.client.post('/messagesdays/ABC123/', message_data, format='json')

        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['BLEOId'], 'ABC123')
        self.assertEqual(response.data['data']['mood'], 'Energetic')
        self.assertEqual(response.data['data']['messages'][0]['title'], 'Path-based Message')
        
        print("  🔹 Successfully created message day with BLEOId in path")
    
    def test_delete_all_user_messages_days(self):
        """Test deleting all messages days for a user"""
        # Add a second message day for the same user
        today_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
        second_message_day = {
            'BLEOId': 'ABC123',
            'date': today_date,
            'messages': [
                {
                    'id': 1,
                    'title': 'Another Test Message',
                    'text': 'Another test content',
                    'type': 'Notes',
                    'created_at': datetime.now()
                }
            ],
            'mood': 'Calm'
        }
        self.db_messages_days.insert_one(second_message_day)
        
        # Verify two messages days exist
        count_before = self.db_messages_days.count_documents({'BLEOId': 'ABC123'})
        self.assertEqual(count_before, 2)
        
        # Make delete request
        response = self.client.delete('/messagesdays/ABC123/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['deleted_count'], 2)
        
        # Verify both messages days were deleted
        count_after = self.db_messages_days.count_documents({'BLEOId': 'ABC123'})
        self.assertEqual(count_after, 0)
        
        print("  🔹 Successfully deleted all messages days for a user")
    
    def test_delete_all_messages_days_nonexistent_user(self):
        """Test error when deleting messages days for nonexistent user"""
        # Make request
        response = self.client.delete('/messagesdays/NONEXISTENT/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled deleting messages days for nonexistent user")
    
    # ====== MoodOptionsView Tests ======
    
    def test_get_mood_options(self):
        """Test getting mood options"""
        # Make request
        response = self.client.get('/mood-options/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn('energy_levels', response.data['data'])
        self.assertIn('pleasantness_options', response.data['data'])
        self.assertIn('mood_quadrants', response.data['data'])
        self.assertIn('all_moods', response.data['data'])
        
        # Check content
        self.assertIn({'value': 'high', 'label': 'High'}, response.data['data']['energy_levels'])
        self.assertIn({'value': 'pleasant', 'label': 'Pleasant'}, response.data['data']['pleasantness_options'])
        
        print("  🔹 Successfully retrieved mood options")
    
    def test_get_filtered_moods(self):
        """Test getting filtered moods by energy and pleasantness"""
        # Make request
        response = self.client.get('/mood-options/', {
            'energy': 'high',
            'pleasantness': 'pleasant'
        })
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn('filtered_moods', response.data['data'])
        self.assertEqual(response.data['data']['selected_quadrant'], 'yellow')
        
        # High pleasant moods should include 'Happy' and 'Excited'
        mood_values = [mood['value'] for mood in response.data['data']['filtered_moods']]
        self.assertTrue('Happy' in mood_values or 'Excited' in mood_values)
        
        print("  🔹 Successfully retrieved filtered moods")
    
    def test_get_filtered_moods_invalid_params(self):
        """Test getting filtered moods with invalid parameters"""
        # Make request with invalid energy
        response = self.client.get('/mood-options/', {
            'energy': 'invalid',
            'pleasantness': 'pleasant'
        })
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.data['data'])
        self.assertEqual(response.data['data']['filtered_moods'], [])
        
        print("  🔹 Properly handled invalid mood filter parameters")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(MessagesDaysViewTest)