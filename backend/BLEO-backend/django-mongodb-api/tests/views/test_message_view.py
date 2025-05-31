from tests.base_test import BLEOBaseTest, run_test_with_output
from rest_framework.test import APIClient
from api.Views.MessagesDays.Message.MessageView import MessageOperationsView
from models.enums.MessageType import MessageType
from models.enums.MoodType import MoodType
from models.enums.PleasantnessType import PleasantnessType
from models.enums.EnergyLevelType import EnergyLevelType
from utils.mongodb_utils import MongoDB
from django.contrib.auth.hashers import make_password
import json
import time
import random
from datetime import datetime, timedelta
from django.urls import path
from django.test import override_settings
import bson

# Set up URL configuration for testing
urlpatterns = [
    # Message operations - GET all messages for user
    path('messagesdays/<str:bleoid>/messages/', MessageOperationsView.as_view(), name='user-messages'),  
    # Message operations - GET/POST/PUT/DELETE messages for a specific date
    path('messagesdays/<str:bleoid>/<str:date>/messages/', MessageOperationsView.as_view(), name='message-operations'),  
    # Message operations - GET/PUT/DELETE a specific message
    path('messagesdays/<str:bleoid>/<str:date>/messages/<int:message_id>/', MessageOperationsView.as_view(), name='message-detail'), 
]

@override_settings(ROOT_URLCONF=__name__)
class MessageViewTest(BLEOBaseTest):
    """Test cases for MessageOperationsView with MongoDB test collection"""
    
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
        cls.links_collection_name = f"Links_{cls.test_suffix}"
        
        # Store original collection names to restore later
        cls.original_users_collection = MongoDB.COLLECTIONS['Users']
        cls.original_messages_days_collection = MongoDB.COLLECTIONS['MessagesDays']
        cls.original_links_collection = MongoDB.COLLECTIONS['Links'] if 'Links' in MongoDB.COLLECTIONS else None  
        
        # Override collection names for testing
        MongoDB.COLLECTIONS['Users'] = cls.users_collection_name
        MongoDB.COLLECTIONS['MessagesDays'] = cls.messages_days_collection_name
        MongoDB.COLLECTIONS['Links'] = cls.links_collection_name  
        
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
            db.drop_collection(cls.links_collection_name)  
            
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
            self.db_links = MongoDB.get_instance().get_collection('Links')  
            
            # Clear collections before each test
            self.db_users.delete_many({})
            self.db_messages_days.delete_many({})
            self.db_links.delete_many({})  
            
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
            
            # Create sample links between users
            self.test_links = [
                {
                    'BLEOIdPartner1': 'ABC123',
                    'BLEOIdPartner2': 'DEF456',
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
                    print(f"  ✅ Created test link {i+1} between: {link['BLEOIdPartner1']} and {link['BLEOIdPartner2']}")
                except Exception as e:
                    print(f"  ❌ Failed to create test link {i+1}: {str(e)}")
                    raise
            
            # Create sample message days with messages
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_date = datetime(yesterday.year, yesterday.month, yesterday.day)
            today_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
            week_ago_date = datetime.now() - timedelta(days=7)
            week_ago_midnight = datetime(week_ago_date.year, week_ago_date.month, week_ago_date.day)
            
            # Update test message days data in setUp method
            self.test_message_days = [
                {
                    'fromBLEOId': 'ABC123',
                    'toBLEOId': 'DEF456',
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
                    'fromBLEOId': 'ABC123',
                    'toBLEOId': 'DEF456',
                    'date': today_date,
                    'messages': [
                        {
                            'id': 1,
                            'title': 'Today Message 1',
                            'text': 'Content of today message 1',
                            'type': MessageType.JOKING.value,
                            'created_at': datetime.now() - timedelta(hours=3)
                        },
                        {
                            'id': 2,
                            'title': 'Today Message 2',
                            'text': 'Content of today message 2',
                            'type': MessageType.LOVE_MESSAGE.value,
                            'created_at': datetime.now() - timedelta(hours=1)
                        }
                    ],
                    'mood': MoodType.ENTHUSIASTIC.value,
                    'energy_level': EnergyLevelType.HIGH.value,
                    'pleasantness': PleasantnessType.PLEASANT.value
                },
                {
                    'fromBLEOId': 'DEF456',
                    'toBLEOId': 'ABC123',
                    'date': today_date,
                    'messages': [
                        {
                            'id': 1,
                            'title': 'DEF User Message',
                            'text': 'Content of DEF user message',
                            'type': MessageType.LOVE_MESSAGE.value,
                            'created_at': datetime.now() - timedelta(hours=4)
                        }
                    ],
                    'mood': MoodType.CALM.value,
                    'energy_level': EnergyLevelType.LOW.value,
                    'pleasantness': PleasantnessType.PLEASANT.value
                },
                {
                    'fromBLEOId': 'ABC123',
                    'toBLEOId': 'DEF456',
                    'date': week_ago_midnight,
                    'messages': [
                        {
                            'id': 1,
                            'title': 'Week Ago Message',
                            'text': 'Content from a week ago',
                            'type': MessageType.THOUGHTS.value,
                            'created_at': week_ago_date + timedelta(hours=5)
                        }
                    ],
                    'mood': MoodType.CONTENT.value,
                    'energy_level': EnergyLevelType.LOW.value,
                    'pleasantness': PleasantnessType.PLEASANT.value
                }
            ]
            
            # Insert test message days
            self.message_day_ids = []
            for i, message_day in enumerate(self.test_message_days):
                try:
                    result = self.db_messages_days.insert_one(message_day)
                    self.message_day_ids.append(result.inserted_id)
                    print(f"  ✅ Created test message day {i+1} from {message_day['fromBLEOId']} to {message_day['toBLEOId']} on {message_day['date'].strftime('%d-%m-%Y')}")
                except Exception as e:
                    print(f"  ❌ Failed to create test message day {i+1}: {str(e)}")
                    raise
            
            print(f"🔧 Test environment setup with {len(self.user_ids)} users, {len(self.link_ids)} links, and {len(self.message_day_ids)} message days")
            
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
        return date.strftime('%d-%m-%Y')
    
    def get_yesterday_date_str(self):
        """Get yesterday's date as DD-MM-YYYY string"""
        yesterday = datetime.now() - timedelta(days=1)
        return self.format_date(yesterday)
    
    def get_today_date_str(self):
        """Get today's date as DD-MM-YYYY string"""
        today = datetime.now()
        return self.format_date(today)
    
    def get_week_ago_date_str(self):
        """Get date from a week ago as DD-MM-YYYY string"""
        week_ago = datetime.now() - timedelta(days=7)
        return self.format_date(week_ago)
    
    # ====== Test All Messages for User ======
    
    def test_get_all_messages_for_user(self):
        """Test getting all messages for a user across all dates"""
        # Make request to get all messages for ABC123
        response = self.client.get('/messagesdays/ABC123/messages/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['fromBLEOId'], 'ABC123')
        self.assertEqual(response.data['data']['count'], 5)  # Total 5 messages across 3 dates
        self.assertEqual(response.data['data']['date_count'], 3)  # 3 message days
        
        # Check message content
        messages = response.data['data']['messages']
        self.assertEqual(len(messages), 5)
        
        # Verify dates are included
        self.assertTrue(all('date' in message for message in messages))
        
        # Check specific message content
        message_titles = [msg['title'] for msg in messages]
        self.assertIn('Test Message 1', message_titles)
        self.assertIn('Today Message 1', message_titles)
        self.assertIn('Week Ago Message', message_titles)
        
        print("  🔹 Successfully retrieved all messages for user")
    
    def test_get_all_messages_for_nonexistent_user(self):
        """Test error when getting messages for nonexistent user"""
        # Make request for nonexistent user
        response = self.client.get('/messagesdays/NONEXISTENT/messages/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        self.assertTrue('No message days found' in response.data['errorMessage'])
        
        print("  🔹 Properly handled nonexistent user")
    
    def test_get_all_messages_for_user_with_no_messages(self):
        """Test getting messages for a user with no message days"""
        # Create a new user without messages
        new_user = {
            'BLEOId': 'NO_MSGS',
            'email': 'nomessages@example.com',
            'password': make_password('Password123'),
            'userName': 'NoMessages',
            'last_login': datetime.now(),
            'created_at': datetime.now()
        }
        self.db_users.insert_one(new_user)
        
        # Make request
        response = self.client.get('/messagesdays/NO_MSGS/messages/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled user with no messages")
    
    # ====== Test Messages for Specific Date ======
    
    def test_get_messages_for_date(self):
        """Test getting all messages for a specific date"""
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.get(f'/messagesdays/ABC123/{yesterday_str}/messages/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['fromBLEOId'], 'ABC123')
        self.assertEqual(response.data['data']['date'], yesterday_str)
        self.assertEqual(response.data['data']['count'], 2)  # 2 messages on this date
        
        # Check message content
        messages = response.data['data']['messages']
        self.assertEqual(len(messages), 2)
        
        # Check specific message content
        message_titles = [msg['title'] for msg in messages]
        self.assertIn('Test Message 1', message_titles)
        self.assertIn('Test Message 2', message_titles)
        
        # Check message types
        message_types = [msg['type'] for msg in messages]
        self.assertIn(MessageType.THOUGHTS.value, message_types)
        self.assertIn(MessageType.SOUVENIR.value, message_types)
        
        print("  🔹 Successfully retrieved messages for specific date")
    
    def test_get_messages_for_nonexistent_date(self):
        """Test error when getting messages for a nonexistent date"""
        # Make request with a date that doesn't exist
        future_date = datetime.now() + timedelta(days=30)
        future_date_str = self.format_date(future_date)
        response = self.client.get(f'/messagesdays/ABC123/{future_date_str}/messages/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled nonexistent date")
    
    def test_get_messages_for_invalid_date_format(self):
        """Test error when getting messages with invalid date format"""
        # Make request with invalid date format
        response = self.client.get('/messagesdays/ABC123/invalid-date/messages/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled invalid date format")
    
    # ====== Test Specific Message ======
    
    def test_get_specific_message(self):
        """Test getting a specific message by ID"""
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.get(f'/messagesdays/ABC123/{yesterday_str}/messages/1/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['id'], 1)
        self.assertEqual(response.data['data']['title'], 'Test Message 1')
        self.assertEqual(response.data['data']['type'], MessageType.THOUGHTS.value)
        
        print("  🔹 Successfully retrieved specific message")
    
    def test_get_nonexistent_message(self):
        """Test error when getting a nonexistent message ID"""
        # Make request with nonexistent message ID
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.get(f'/messagesdays/ABC123/{yesterday_str}/messages/999/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled nonexistent message ID")
    
    # ====== Test Adding Messages ======
    
    def test_add_message_success(self):
        """Test adding a new message to a message day"""
        # Request data
        new_message = {
            'messages': [
                {
                    'title': 'New Test Message',
                    'text': 'Content of new test message',
                    'type': MessageType.JOKING.value
                }
            ]
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.post(f'/messagesdays/ABC123/{yesterday_str}/messages/', 
                                    new_message, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        
        # Verify message was added
        messages = response.data['data']['messages']
        self.assertEqual(len(messages), 3)  # Original 2 + new 1
        
        # Find the new message in the response
        new_messages = [msg for msg in messages if msg['title'] == 'New Test Message']
        self.assertEqual(len(new_messages), 1)
        self.assertEqual(new_messages[0]['text'], 'Content of new test message')
        self.assertEqual(new_messages[0]['type'], MessageType.JOKING.value)
        
        # Verify ID was assigned
        self.assertTrue('id' in new_messages[0])
        
        # Verify in database
        message_day = self.db_messages_days.find_one({
            "fromBLEOId": "ABC123",
            "toBLEOId": "DEF456",
            "date": datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(days=1)
        })
        self.assertEqual(len(message_day['messages']), 3)
        
        print("  🔹 Successfully added new message")
    
    def test_add_multiple_messages(self):
        """Test adding multiple messages in one request"""
        # Request data
        new_messages = {
            'messages': [
                {
                    'title': 'New Message 1',
                    'text': 'Content of new message 1',
                    'type': MessageType.THOUGHTS.value
                },
                {
                    'title': 'New Message 2',
                    'text': 'Content of new message 2',
                    'type': MessageType.LOVE_MESSAGE.value
                }
            ]
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.post(f'/messagesdays/ABC123/{yesterday_str}/messages/', 
                                    new_messages, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        
        # Verify messages were added
        messages = response.data['data']['messages']
        self.assertEqual(len(messages), 4)  # Original 2 + new 2
        
        # Find the new messages in the response
        titles = [msg['title'] for msg in messages]
        self.assertIn('New Message 1', titles)
        self.assertIn('New Message 2', titles)
        
        print("  🔹 Successfully added multiple messages")
    
    def test_add_message_to_nonexistent_message_day(self):
        """Test error when adding message to nonexistent message day"""
        # Request data
        new_message = {
            'title': 'New Message',
            'text': 'Content of new message',
            'type': MessageType.THOUGHTS.value
        }
        
        # Make request with a date that doesn't exist
        future_date = datetime.now() + timedelta(days=30)
        future_date_str = self.format_date(future_date)
        response = self.client.post(f'/messagesdays/ABC123/{future_date_str}/messages/', 
                                    new_message, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled adding to nonexistent message day")
    
    def test_add_invalid_message(self):
        """Test error when adding invalid message data"""
        # Request data with invalid message type
        invalid_message = {
            'messages': [
                {
                    'title': 'Invalid Message',
                    'text': 'Content of invalid message',
                    'type': 'InvalidType'  # Not in MessageType enum
                }
            ]
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.post(f'/messagesdays/ABC123/{yesterday_str}/messages/', 
                                    invalid_message, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        
        print("  🔹 Properly rejected invalid message data")
    
    # ====== Test Updating Messages ======
    
    def test_update_specific_message(self):
        """Test updating a specific message"""
        # Update data
        update_data = {
            'title': 'Updated Message Title',
            'text': 'Updated message content'
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.put(f'/messagesdays/ABC123/{yesterday_str}/messages/1/', 
                                   update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['title'], 'Updated Message Title')
        self.assertEqual(response.data['data']['text'], 'Updated message content')
        self.assertEqual(response.data['data']['id'], 1)
        
        # Original type should be preserved
        self.assertEqual(response.data['data']['type'], MessageType.THOUGHTS.value)
        
        # Verify in database
        message_day = self.db_messages_days.find_one({
            "fromBLEOId": "ABC123",
            "toBLEOId": "DEF456",
            "date": datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(days=1)
        })
        
        message = next((msg for msg in message_day['messages'] if msg['id'] == 1), None)
        self.assertEqual(message['title'], 'Updated Message Title')
        self.assertEqual(message['text'], 'Updated message content')
        
        print("  🔹 Successfully updated specific message")
    
    def test_update_message_type(self):
        """Test updating a message's type"""
        # Update data
        update_data = {
            'type': MessageType.LOVE_MESSAGE.value
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.put(f'/messagesdays/ABC123/{yesterday_str}/messages/1/', 
                                   update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['type'], MessageType.LOVE_MESSAGE.value)
        
        # Original title should be preserved
        self.assertEqual(response.data['data']['title'], 'Test Message 1')
        
        print("  🔹 Successfully updated message type")
    
    def test_update_nonexistent_message(self):
        """Test error when updating nonexistent message"""
        # Update data
        update_data = {
            'title': 'Updated Title'
        }
        
        # Make request with nonexistent message ID
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.put(f'/messagesdays/ABC123/{yesterday_str}/messages/999/', 
                                   update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled updating nonexistent message")
    
    def test_update_with_invalid_data(self):
        """Test error when updating with invalid data"""
        # Update data with invalid type
        update_data = {
            'type': 'InvalidType'
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.put(f'/messagesdays/ABC123/{yesterday_str}/messages/1/', 
                                   update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        
        print("  🔹 Properly rejected invalid update data")
    
    def test_update_all_messages(self):
        """Test updating all messages for a date"""
        # Update data - replace all messages
        update_data = {
            'messages': [
                {
                    'id': 1,  # Keep original ID
                    'title': 'Replaced Message 1',
                    'text': 'New content for message 1',
                    'type': MessageType.JOKING.value
                },
                {
                    'title': 'Brand New Message',  # No ID, should be assigned new one
                    'text': 'Content for new message',
                    'type': MessageType.LOVE_MESSAGE.value
                }
            ]
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.put(f'/messagesdays/ABC123/{yesterday_str}/messages/', 
                                   update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['messages']), 2)
        
        # Check message content
        messages = response.data['data']['messages']
        self.assertEqual(messages[0]['title'], 'Replaced Message 1')
        self.assertEqual(messages[0]['id'], 1)
        self.assertEqual(messages[1]['title'], 'Brand New Message')
        self.assertIsNotNone(messages[1]['id'])
        
        # Verify in database
        message_day = self.db_messages_days.find_one({
            "fromBLEOId": "ABC123",
            "toBLEOId": "DEF456",
            "date": datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(days=1)
        })
        self.assertEqual(len(message_day['messages']), 2)
        
        print("  🔹 Successfully replaced all messages")
    
    def test_update_all_messages_invalid_data(self):
        """Test error when updating all messages with invalid data"""
        # Update data with invalid message
        update_data = {
            'messages': [
                {
                    'id': 1,
                    'title': 'Valid Message',
                    'text': 'This one is fine',
                    'type': MessageType.THOUGHTS.value
                },
                {
                    'title': 'Invalid Message',
                    'text': 'This one has invalid type',
                    'type': 'InvalidType'
                }
            ]
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.put(f'/messagesdays/ABC123/{yesterday_str}/messages/', 
                                   update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        
        # Original messages should be unchanged
        message_day = self.db_messages_days.find_one({
            "fromBLEOId": "ABC123",
            "toBLEOId": "DEF456",
            "date": datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(days=1)
        })
        self.assertEqual(len(message_day['messages']), 2)
        self.assertEqual(message_day['messages'][0]['title'], 'Test Message 1')
        
        print("  🔹 Properly rejected invalid data for all messages update")
    
    # ====== Test Deleting Messages ======
    
    def test_delete_specific_message(self):
        """Test deleting a specific message"""
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.delete(f'/messagesdays/ABC123/{yesterday_str}/messages/1/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['messages']), 1)  # Only message #2 remains
        
        # Verify message 1 is deleted
        messages = response.data['data']['messages']
        message_ids = [msg['id'] for msg in messages]
        self.assertNotIn(1, message_ids)
        self.assertIn(2, message_ids)
        
        # Verify in database
        message_day = self.db_messages_days.find_one({
            "fromBLEOId": "ABC123",
            "toBLEOId": "DEF456",
            "date": datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(days=1)
        })
        self.assertEqual(len(message_day['messages']), 1)
        self.assertEqual(message_day['messages'][0]['id'], 2)
        
        print("  🔹 Successfully deleted specific message")
    
    def test_delete_nonexistent_message(self):
        """Test error when deleting nonexistent message"""
        # Make request with nonexistent message ID
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.delete(f'/messagesdays/ABC123/{yesterday_str}/messages/999/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled deleting nonexistent message")
    
    def test_delete_all_messages(self):
        """Test deleting all messages for a date"""
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.delete(f'/messagesdays/ABC123/{yesterday_str}/messages/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['messages']), 0)
        
        # Verify in database
        message_day = self.db_messages_days.find_one({
            "fromBLEOId": "ABC123",
            "toBLEOId": "DEF456",
            "date": datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(days=1)
        })
        self.assertEqual(len(message_day['messages']), 0)
        
        print("  🔹 Successfully deleted all messages")
    
    # ====== Edge Cases ======
    
    def test_message_with_created_at_auto_generation(self):
        """Test that created_at is auto-generated when not provided"""
        new_message = {
            'messages': [
                {
                    'title': 'Message without created_at',
                    'text': 'This message should get created_at auto-generated',
                    'type': MessageType.THOUGHTS.value
                }
            ]
        }
        
        # Make request
        yesterday_str = self.get_yesterday_date_str()
        response = self.client.post(f'/messagesdays/ABC123/{yesterday_str}/messages/', 
                                  new_message, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        
        # Find the new message
        new_messages = [msg for msg in response.data['data']['messages'] 
                        if msg['title'] == 'Message without created_at']
        self.assertEqual(len(new_messages), 1)
        
        # Check created_at was auto-generated
        self.assertIn('created_at', new_messages[0])
        
        print("  🔹 Successfully auto-generated created_at")

# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(MessageViewTest)