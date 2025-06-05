from tests.base_test import BLEOBaseTest, run_test_with_output
from rest_framework.test import APIClient
from auth.connection import ConnectionRequestView, ConnectionResponseView, ConnectionListView
from utils.mongodb_utils import MongoDB
from django.contrib.auth.hashers import make_password
from models.enums.ConnectionStatusType import ConnectionStatusType
import time
import random
from datetime import datetime
from django.urls import path
from django.test import override_settings
from bson import ObjectId

# Set up URL configuration for testing
urlpatterns = [
    path('connections/request/', ConnectionRequestView.as_view(), name='connection-request'),
    path('connections/response/<str:connection_id>/', ConnectionResponseView.as_view(), name='connection-response'),
    path('connections/', ConnectionListView.as_view(), name='connection-list'),
]

@override_settings(ROOT_URLCONF=__name__)
class ConnectionViewTest(BLEOBaseTest):
    """Test cases for Connection views with MongoDB test collections"""
    
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
        cls.links_collection_name = f"Links_{cls.test_suffix}"
        
        # Store original collection names to restore later
        cls.original_users_collection = MongoDB.COLLECTIONS['Users']
        cls.original_links_collection = MongoDB.COLLECTIONS['Links']
        
        # Override collection names for testing
        MongoDB.COLLECTIONS['Users'] = cls.users_collection_name
        MongoDB.COLLECTIONS['Links'] = cls.links_collection_name
        
        print(f"🔧 Created test collections: {cls.users_collection_name}, {cls.links_collection_name}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Use the MongoDB instance to get the database
            db = MongoDB.get_instance().get_db()
            
            # Drop test collections
            db.drop_collection(cls.users_collection_name)
            db.drop_collection(cls.links_collection_name)
            
            # Restore original collection names
            MongoDB.COLLECTIONS['Users'] = cls.original_users_collection
            MongoDB.COLLECTIONS['Links'] = cls.original_links_collection
            
            print(f"🧹 Dropped test collections: {cls.users_collection_name}, {cls.links_collection_name}")
        except Exception as e:
            print(f"❌ Error during teardown: {str(e)}")
        finally:
            super().tearDownClass()
    
    def setUp(self):
        """Set up the test environment before each test"""
        super().setUp()
        # Use APIClient instead of APIRequestFactory
        self.client = APIClient()
        
        try:
            # Get test collections
            self.db_users = MongoDB.get_instance().get_collection('Users')
            self.db_links = MongoDB.get_instance().get_collection('Links')
            
            # Clear collections before each test
            self.db_users.delete_many({})
            self.db_links.delete_many({})
            
            # Create sample test users
            self.test_users = [
                {
                    'bleoid': 'USER01',
                    'email': 'user1@example.com',
                    'password': make_password('Password123'),
                    'userName': 'TestUser1', 
                    'bio': 'Test bio 1',
                    'email_verified': True,
                    'preferences': {'theme': 'light'},
                    'profilePic': None,
                    'last_login': datetime.now(),
                    'created_at': datetime.now()
                },
                {
                    'bleoid': 'USER02',
                    'email': 'user2@example.com',
                    'password': make_password('Password456'),
                    'userName': 'TestUser2',
                    'bio': 'Test bio 2',
                    'email_verified': True,
                    'preferences': {'theme': 'dark'},
                    'profilePic': None,
                    'last_login': datetime.now(),
                    'created_at': datetime.now()
                },
                {
                    'bleoid': 'USER03',
                    'email': 'user3@example.com',
                    'password': make_password('Password789'),
                    'userName': 'TestUser3',
                    'bio': 'Test bio 3',
                    'email_verified': True,
                    'preferences': {'theme': 'light'},
                    'profilePic': None,
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
            
            print(f"🔧 Test environment setup with {len(self.user_ids)} sample users")
            
        except Exception as e:
            print(f"❌ Test setup failed: {str(e)}")
            raise
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear collections
        self.db_users.delete_many({})
        self.db_links.delete_many({})
        super().tearDown()
    
    # ====== ConnectionRequestView Tests ======
    
    def test_send_connection_request_success(self):
        """Test sending a connection request successfully"""
        # Request data
        request_data = {
            'from_bleoid': 'USER01',
            'to_bleoid': 'USER02'
        }
        
        # Make request
        response = self.client.post('/connections/request/', request_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['bleoidPartner1'], 'USER01')
        self.assertEqual(response.data['data']['bleoidPartner2'], 'USER02')
        self.assertEqual(response.data['data']['status'], ConnectionStatusType.PENDING)
        self.assertEqual(response.data['successMessage'], 'Connection request sent')
        
        # Verify connection was created in database
        connection = self.db_links.find_one({
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02'
        })
        self.assertIsNotNone(connection)
        self.assertEqual(connection['status'], ConnectionStatusType.PENDING)
        
        print("  🔹 Successfully sent connection request")
    
    def test_send_connection_request_invalid_data(self):
        """Test error when sending connection request with invalid data"""
        # Request data (missing to_bleoid)
        request_data = {
            'from_bleoid': 'USER01'
        }
        
        # Make request
        response = self.client.post('/connections/request/', request_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertIn('to_bleoid', response.data['validationErrors'])
        
        print("  🔹 Properly rejected invalid connection request data")
    
    def test_send_connection_request_user_not_found(self):
        """Test error when sending connection request to nonexistent user"""
        # Request data with nonexistent user
        request_data = {
            'from_bleoid': 'USER01',
            'to_bleoid': 'NOP'
        }
        
        # Make request
        response = self.client.post('/connections/request/', request_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Invalid connection request data')
        
        print("  🔹 Properly handled nonexistent user in connection request")
    
    def test_send_duplicate_connection_request(self):
        """Test error when sending duplicate connection request"""
        # Create initial connection request
        initial_request = {
            'from_bleoid': 'USER01',
            'to_bleoid': 'USER02'
        }
        self.client.post('/connections/request/', initial_request, format='json')
        
        # Try to send duplicate request
        duplicate_request = {
            'from_bleoid': 'USER01',
            'to_bleoid': 'USER02'
        }
        
        # Make request
        response = self.client.post('/connections/request/', duplicate_request, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'DuplicateError')
        self.assertEqual(response.data['errorMessage'], 'You already have a connection request with this user')
        
        print("  🔹 Properly rejected duplicate connection request")
    
    def test_send_connection_request_when_already_connected(self):
        """Test error when trying to connect with someone who already has an active connection"""
        # Create an accepted connection for USER02 with USER03
        existing_connection = {
            'bleoidPartner1': 'USER02',
            'bleoidPartner2': 'USER03',
            'status': ConnectionStatusType.ACCEPTED,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        self.db_links.insert_one(existing_connection)
        
        # Try to send request to USER02 who already has an active connection
        request_data = {
            'from_bleoid': 'USER01',
            'to_bleoid': 'USER02'
        }
        
        # Make request
        response = self.client.post('/connections/request/', request_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'LimitExceeded')
        self.assertEqual(response.data['errorMessage'], 'The user you\'re trying to connect with already has an active connection')
        
        print("  🔹 Properly rejected request to user with existing connection")
    
    def test_renew_rejected_connection_request(self):
        """Test renewing a previously rejected connection request"""
        # Create a rejected connection
        rejected_connection = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.REJECTED,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        result = self.db_links.insert_one(rejected_connection)
        
        # Send new request (should renew the rejected one)
        request_data = {
            'from_bleoid': 'USER01',
            'to_bleoid': 'USER02'
        }
        
        # Make request
        response = self.client.post('/connections/request/', request_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['status'], ConnectionStatusType.PENDING)
        self.assertEqual(response.data['successMessage'], 'Connection request renewed')
        
        # Verify connection was updated in database
        updated_connection = self.db_links.find_one({'_id': result.inserted_id})
        self.assertEqual(updated_connection['status'], ConnectionStatusType.PENDING)
        
        print("  🔹 Successfully renewed rejected connection request")
    
    # ====== ConnectionResponseView Tests ======
    
    def test_accept_connection_request_success(self):
        """Test accepting a connection request successfully"""
        # Create a pending connection
        pending_connection = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.PENDING,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        result = self.db_links.insert_one(pending_connection)
        connection_id = str(result.inserted_id)
        
        # Accept the connection
        response_data = {
            'action': 'accept'
        }
        
        # Make request
        response = self.client.put(f'/connections/response/{connection_id}/', response_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['status'], ConnectionStatusType.ACCEPTED)
        self.assertEqual(response.data['successMessage'], 'Connection request accepted')
        
        # Verify connection was updated in database
        updated_connection = self.db_links.find_one({'_id': result.inserted_id})
        self.assertEqual(updated_connection['status'], ConnectionStatusType.ACCEPTED)
        
        print("  🔹 Successfully accepted connection request")
    
    def test_reject_connection_request_success(self):
        """Test rejecting a connection request successfully"""
        # Create a pending connection
        pending_connection = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.PENDING,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        result = self.db_links.insert_one(pending_connection)
        connection_id = str(result.inserted_id)
        
        # Reject the connection
        response_data = {
            'action': 'reject'
        }
        
        # Make request
        response = self.client.put(f'/connections/response/{connection_id}/', response_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['status'], ConnectionStatusType.REJECTED)
        self.assertEqual(response.data['successMessage'], 'Connection request rejected')
        
        # Verify connection was updated in database
        updated_connection = self.db_links.find_one({'_id': result.inserted_id})
        self.assertEqual(updated_connection['status'], ConnectionStatusType.REJECTED)
        
        print("  🔹 Successfully rejected connection request")
    
    def test_block_connection_request_success(self):
        """Test blocking a connection request successfully"""
        # Create a pending connection
        pending_connection = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.PENDING,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        result = self.db_links.insert_one(pending_connection)
        connection_id = str(result.inserted_id)
        
        # Block the connection
        response_data = {
            'action': 'block'
        }
        
        # Make request
        response = self.client.put(f'/connections/response/{connection_id}/', response_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['status'], ConnectionStatusType.BLOCKED)
        self.assertEqual(response.data['successMessage'], 'Connection request blocked')
        
        # Verify connection was updated in database
        updated_connection = self.db_links.find_one({'_id': result.inserted_id})
        self.assertEqual(updated_connection['status'], ConnectionStatusType.BLOCKED)
        
        print("  🔹 Successfully blocked connection request")
    
    def test_respond_to_nonexistent_connection(self):
        """Test error when responding to nonexistent connection"""
        # Use a valid ObjectId format but nonexistent
        fake_connection_id = str(ObjectId())
        
        response_data = {
            'action': 'accept'
        }
        
        # Make request
        response = self.client.put(f'/connections/response/{fake_connection_id}/', response_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        self.assertEqual(response.data['errorMessage'], 'Connection request not found')
        
        print("  🔹 Properly handled nonexistent connection response")
    
    def test_respond_with_invalid_action(self):
        """Test error when responding with invalid action"""
        # Create a pending connection
        pending_connection = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.PENDING,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        result = self.db_links.insert_one(pending_connection)
        connection_id = str(result.inserted_id)
        
        # Invalid action
        response_data = {
            'action': 'invalid_action'
        }
        
        # Make request
        response = self.client.put(f'/connections/response/{connection_id}/', response_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertIn('action', response.data['validationErrors'])
        
        print("  🔹 Properly rejected invalid action")
    
    def test_accept_when_already_connected(self):
        """Test error when trying to accept connection while already having an active one"""
        # Create an existing accepted connection for USER02
        existing_connection = {
            'bleoidPartner1': 'USER02',
            'bleoidPartner2': 'USER03',
            'status': ConnectionStatusType.ACCEPTED,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        self.db_links.insert_one(existing_connection)
        
        # Create a pending connection for USER02 with USER01
        pending_connection = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.PENDING,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        result = self.db_links.insert_one(pending_connection)
        connection_id = str(result.inserted_id)
        
        # Try to accept (should fail because USER02 already has an active connection)
        response_data = {
            'action': 'accept'
        }
        
        # Make request
        response = self.client.put(f'/connections/response/{connection_id}/', response_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'LimitExceeded')
        self.assertEqual(response.data['errorMessage'], 'You already have an active connection with someone else')
        
        print("  🔹 Properly rejected accept when already connected")
    
    # ====== ConnectionListView Tests ======
    
    def test_get_all_connections_for_user(self):
        """Test getting all connections for a user (should be max 1 active connection)"""
        # In BLEO, a user can only have ONE active connection at a time
        # Create one active connection for USER01
        active_connection = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.ACCEPTED,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Create some historical connections (rejected/blocked) for USER01
        historical_connections = [
            {
                'bleoidPartner1': 'USER01',
                'bleoidPartner2': 'USER03',
                'status': ConnectionStatusType.REJECTED,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'bleoidPartner1': 'USER03',
                'bleoidPartner2': 'USER01',
                'status': ConnectionStatusType.BLOCKED,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        ]
        
        # Insert connections
        self.db_links.insert_one(active_connection)
        for connection in historical_connections:
            self.db_links.insert_one(connection)
        
        # Make request to get all connections (including historical)
        response = self.client.get('/connections/', {'bleoid': 'USER01'})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['connections']), 3)  # 1 active + 2 historical
        self.assertEqual(response.data['data']['count'], 3)
        self.assertEqual(response.data['successMessage'], 'Connections retrieved successfully')
        
        # Verify that only ONE connection is ACCEPTED (active)
        active_connections = [conn for conn in response.data['data']['connections'] 
                             if conn['status'] == ConnectionStatusType.ACCEPTED]
        self.assertEqual(len(active_connections), 1)
        self.assertEqual(active_connections[0]['bleoidPartner2'], 'USER02')
        
        # Verify user info is included
        for connection in response.data['data']['connections']:
            self.assertIn('other_user', connection)
            self.assertIn('userName', connection['other_user'])
            self.assertIn('bleoid', connection['other_user'])
        
        print("  🔹 Successfully retrieved all connections for user (1 active, 2 historical)")
    
    def test_get_active_connection_only(self):
        """Test getting only the active connection for a user"""
        # Create one active connection for USER01
        active_connection = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.ACCEPTED,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Create some historical connections
        rejected_connection = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER03',
            'status': ConnectionStatusType.REJECTED,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Insert connections
        self.db_links.insert_one(active_connection)
        self.db_links.insert_one(rejected_connection)
        
        # Make request for active connections only
        response = self.client.get('/connections/', {
            'bleoid': 'USER01',
            'status': ConnectionStatusType.ACCEPTED
        })
        
        # Check response - should only return the one active connection
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['connections']), 1)
        self.assertEqual(response.data['data']['connections'][0]['status'], ConnectionStatusType.ACCEPTED)
        self.assertEqual(response.data['data']['connections'][0]['bleoidPartner2'], 'USER02')
        
        print("  🔹 Successfully retrieved only active connection for user")
    
    def test_user_cannot_have_multiple_active_connections(self):
        """Test that a user cannot have multiple active connections"""
        # Create one active connection for USER01
        active_connection = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.ACCEPTED,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        self.db_links.insert_one(active_connection)
        
        # Try to create another connection request for USER01
        request_data = {
            'from_bleoid': 'USER01',
            'to_bleoid': 'USER03'
        }
        
        # Make request - should fail because USER01 already has an active connection
        response = self.client.post('/connections/request/', request_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'LimitExceeded')
        self.assertEqual(response.data['errorMessage'], 'You already have an active connection or pending request with someone else')
        
        print("  🔹 Properly prevented user from having multiple active connections")
    
    def test_get_pending_requests_for_user(self):
        """Test getting pending connection requests for a user"""
        # Create pending requests TO USER02 (incoming)
        incoming_request = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.PENDING,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Create pending request FROM USER02 (outgoing)
        outgoing_request = {
            'bleoidPartner1': 'USER02',
            'bleoidPartner2': 'USER03',
            'status': ConnectionStatusType.PENDING,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Insert connections
        self.db_links.insert_one(incoming_request)
        self.db_links.insert_one(outgoing_request)
        
        # Make request for pending connections only
        response = self.client.get('/connections/', {
            'bleoid': 'USER02',
            'status': ConnectionStatusType.PENDING
        })
        
        # Check response - should return both pending requests
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['connections']), 2)
        
        # Verify both are pending
        for connection in response.data['data']['connections']:
            self.assertEqual(connection['status'], ConnectionStatusType.PENDING)
        
        print("  🔹 Successfully retrieved pending requests for user")
    
    def test_connection_history_tracking(self):
        """Test that connection history is properly tracked"""
        # Create a connection lifecycle: pending -> accepted -> rejected
        connection_data = {
            'bleoidPartner1': 'USER01',
            'bleoidPartner2': 'USER02',
            'status': ConnectionStatusType.PENDING,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        result = self.db_links.insert_one(connection_data)
        connection_id = str(result.inserted_id)
        
        # Accept the connection
        response = self.client.put(f'/connections/response/{connection_id}/', 
                                  {'action': 'accept'}, format='json')
        self.assertEqual(response.status_code, 200)
        
        # Verify it's now accepted
        response = self.client.get('/connections/', {
            'bleoid': 'USER01',
            'status': ConnectionStatusType.ACCEPTED
        })
        self.assertEqual(len(response.data['data']['connections']), 1)
        
        # Now reject/end the connection (simulate ending the relationship)
        response = self.client.put(f'/connections/response/{connection_id}/', 
                                  {'action': 'reject'}, format='json')
        self.assertEqual(response.status_code, 200)
        
        # Verify it's now rejected and USER01 can make new requests
        response = self.client.get('/connections/', {
            'bleoid': 'USER01',
            'status': ConnectionStatusType.REJECTED
        })
        self.assertEqual(len(response.data['data']['connections']), 1)
        
        # Verify USER01 can now send new requests since they have no active connection
        new_request_data = {
            'from_bleoid': 'USER01',
            'to_bleoid': 'USER03'
        }
        response = self.client.post('/connections/request/', new_request_data, format='json')
        self.assertEqual(response.status_code, 201)
        
        print("  🔹 Successfully tracked connection lifecycle and enabled new requests")

# This will run if this file is executed directly
if __name__ == '__main__':
    import os
    import django
    
    # Setup Django if not already done
    if not hasattr(django.conf.settings, 'configured') or not django.conf.settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
    
    # Import the enhanced test runner
    from tests.base_test import run_test_with_output
    
    print("🚀 Running Connection View Tests with Enhanced Summary")
    print("="*60)
    
    # Run with enhanced output
    run_test_with_output(ConnectionViewTest)