from tests.base_test import BLEOBaseTest, run_test_with_output
from rest_framework.test import APIClient
from api.Views.User.UserView import UserListCreateView, UserDetailView
from models.User import User
from utils.mongodb_utils import MongoDB
from django.contrib.auth.hashers import make_password, check_password
import json
import time
import random
from datetime import datetime
from django.urls import path
from django.test import override_settings

# Set up URL configuration for testing
urlpatterns = [
    path('users/', UserListCreateView.as_view(), name='user-list'),
    path('users/<str:bleoid>/', UserDetailView.as_view(), name='user-detail'),
]

@override_settings(ROOT_URLCONF=__name__)
class UserViewTest(BLEOBaseTest):
    """Test cases for UserListCreateView and UserDetailView with MongoDB test collection"""
    
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
        
        # Store original collection name to restore later
        cls.original_users_collection = MongoDB.COLLECTIONS['Users']
        
        # Override collection name for testing
        MongoDB.COLLECTIONS['Users'] = cls.users_collection_name
        
        print(f"🔧 Created test collection: {cls.users_collection_name}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Use the MongoDB instance to get the database instead of direct client access
            db = MongoDB.get_instance().get_db()
            
            # Drop test collection
            db.drop_collection(cls.users_collection_name)
            
            # Restore original collection name
            MongoDB.COLLECTIONS['Users'] = cls.original_users_collection
            
            print(f"🧹 Dropped test collection: {cls.users_collection_name}")
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
            # Get test collection
            self.db_users = MongoDB.get_instance().get_collection('Users')
            
            # Clear collection before each test
            self.db_users.delete_many({})
            
            # Create sample test users with all required fields
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
            
            print(f"🔧 Test environment setup with {len(self.user_ids)} sample users")
            
        except Exception as e:
            print(f"❌ Test setup failed: {str(e)}")
            raise
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear collection
        self.db_users.delete_many({})
        super().tearDown()
    
    # ====== UserListCreateView Tests ======
    
    def test_get_all_users(self):
        """Test getting all users"""
        # Make request - APIClient automatically handles DRF details
        response = self.client.get('/users/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(response.data['data'][0]['BLEOId'], 'ABC123')
        self.assertEqual(response.data['data'][1]['BLEOId'], 'DEF456')
        self.assertEqual(response.data['successMessage'], 'Users retrieved successfully')
        
        # Verify no passwords are returned
        self.assertNotIn('password', response.data['data'][0])
        self.assertNotIn('password', response.data['data'][1])
        
        print("  🔹 Successfully retrieved all users")
    
    def test_create_user_success(self):
        """Test creating a new user successfully"""
        # Request data
        user_data = {
            'email': 'newuser@example.com',
            'password': 'Password789',
            'userName': 'NewUser',
            'bio': 'New user bio'
        }
        
        # Make request - format='json' handles content type and serialization
        response = self.client.post('/users/', user_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['email'], 'newuser@example.com')
        self.assertIsNotNone(response.data['data']['BLEOId'])
        self.assertNotIn('password', response.data['data'])
        self.assertEqual(response.data['successMessage'], 'User created successfully')
        
        # Verify user was created in database
        created_user = self.db_users.find_one({'email': 'newuser@example.com'})
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user['userName'], 'NewUser')
        self.assertEqual(created_user['bio'], 'New user bio')
        
        # Verify password was hashed
        self.assertTrue(created_user['password'].startswith('pbkdf2_'))
        
        print(f"  🔹 Successfully created user with BLEOId: {response.data['data']['BLEOId']}")
    
    def test_create_user_duplicate_email(self):
        """Test error when creating user with existing email"""
        # Request data with existing email
        user_data = {
            'email': 'user1@example.com',  # Already exists
            'password': 'Password789',
            'userName': 'NewUser'
        }
        
        # Make request
        response = self.client.post('/users/', user_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'DuplicateError')
        self.assertEqual(response.data['errorMessage'], 'Email already exists')
        
        # Verify no new user was created
        user_count = self.db_users.count_documents({})
        self.assertEqual(user_count, 2)
        print("  🔹 Properly rejected duplicate email")
    
    def test_create_user_invalid_data(self):
        """Test error when creating user with invalid data"""
        # Request data (missing email)
        user_data = {
            'password': 'Password789',
            'userName': 'NewUser'
        }
        
        # Make request
        response = self.client.post('/users/', user_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertIn('email', response.data['data']['validation_errors'])
        
        print("  🔹 Properly rejected invalid data (missing email)")
    
    def test_create_user_empty_request(self):
        """Test error when creating user with empty request"""
        # Make request with empty data
        response = self.client.post('/users/', {}, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'No data provided. Request body is empty.')
        
        print("  🔹 Properly rejected empty request")
    
    # ====== UserDetailView Tests ======
    
    def test_get_user_by_bleoid(self):
        """Test getting a user by BLEOId"""
        # Make request
        response = self.client.get('/users/ABC123/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['BLEOId'], 'ABC123')
        self.assertEqual(response.data['data']['email'], 'user1@example.com')
        self.assertNotIn('password', response.data['data'])
        self.assertEqual(response.data['successMessage'], 'User retrieved successfully')
        
        print("  🔹 Successfully retrieved user by BLEOId")
    
    def test_get_nonexistent_user(self):
        """Test error when getting a nonexistent user"""
        # Make request with nonexistent BLEOId
        response = self.client.get('/users/NONEXISTENT/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        self.assertEqual(response.data['errorMessage'], 'User not found')
        
        print("  🔹 Properly handled nonexistent user")
    
    def test_update_user_success(self):
        """Test updating a user successfully"""
        # Update data
        update_data = {
            'userName': 'UpdatedUser',
            'bio': 'Updated bio',
            'preferences': {'theme': 'dark', 'notifications': True}
        }
        
        # Make request
        response = self.client.put('/users/ABC123/', update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['userName'], 'UpdatedUser')
        self.assertEqual(response.data['data']['bio'], 'Updated bio')
        self.assertEqual(response.data['data']['preferences']['theme'], 'dark')
        self.assertEqual(response.data['data']['preferences']['notifications'], True)
        
        # Verify changes in database
        updated_user = self.db_users.find_one({'BLEOId': 'ABC123'})
        self.assertEqual(updated_user['userName'], 'UpdatedUser')
        self.assertEqual(updated_user['bio'], 'Updated bio')
        
        print("  🔹 Successfully updated user")
    
    def test_update_user_password(self):
        """Test updating a user's password"""
        # Update data
        update_data = {
            'password': 'NewPassword123'
        }
        
        # Make request
        response = self.client.put('/users/ABC123/', update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['successMessage'], 'User updated successfully')
        
        # Verify password was hashed in database
        updated_user = self.db_users.find_one({'BLEOId': 'ABC123'})
        self.assertTrue(check_password('NewPassword123', updated_user['password']))
        
        print("  🔹 Successfully updated password with proper hashing")
    
    def test_update_nonexistent_user(self):
        """Test error when updating a nonexistent user"""
        # Update data
        update_data = {
            'userName': 'UpdatedUser'
        }
        
        # Make request with nonexistent BLEOId
        response = self.client.put('/users/NONEXISTENT/', update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled update for nonexistent user")
    
    def test_update_user_invalid_data(self):
        """Test error when updating a user with invalid data"""
        # Update data with invalid email
        update_data = {
            'email': 'invalid-email'
        }
        
        # Make request
        response = self.client.put('/users/ABC123/', update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertIn('email', response.data['data']['validation_errors'])
        
        print("  🔹 Properly rejected invalid update data")
    
    def test_delete_user_success(self):
        """Test deleting a user successfully"""
        # Make request
        response = self.client.delete('/users/ABC123/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['successMessage'].startswith('User deleted successfully'))
        
        # Verify user was deleted from database
        user = self.db_users.find_one({'BLEOId': 'ABC123'})
        self.assertIsNone(user)
        
        print("  🔹 Successfully deleted user")
    
    def test_delete_nonexistent_user(self):
        """Test error when deleting a nonexistent user"""
        # Make request with nonexistent BLEOId
        response = self.client.delete('/users/NONEXISTENT/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorType'], 'NotFoundError')
        
        print("  🔹 Properly handled delete for nonexistent user")

# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(UserViewTest)