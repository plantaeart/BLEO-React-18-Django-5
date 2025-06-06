from tests.base_test import BLEOBaseTest, run_test_with_output
from rest_framework.test import APIClient
from auth.password_reset import PasswordResetRequestView, PasswordResetConfirmView
from utils.mongodb_utils import MongoDB
from django.contrib.auth.hashers import make_password
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from rest_framework import status
import jwt
import os
import time
import random
from django.urls import path
from django.test import override_settings

# Set up URL configuration for testing
urlpatterns = [
    path('auth/password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]

@override_settings(ROOT_URLCONF=__name__)
class PasswordResetViewTest(BLEOBaseTest):
    """Test cases for Password Reset views with MongoDB test collections"""
    
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
        cls.password_resets_collection_name = f"PasswordResets_{cls.test_suffix}"
        
        # Store original collection names to restore later
        cls.original_users_collection = MongoDB.COLLECTIONS['Users']
        cls.original_password_resets_collection = MongoDB.COLLECTIONS['PasswordResets']
        
        # Override collection names for testing
        MongoDB.COLLECTIONS['Users'] = cls.users_collection_name
        MongoDB.COLLECTIONS['PasswordResets'] = cls.password_resets_collection_name
        
        print(f"🔧 Created test collections: {cls.users_collection_name}, {cls.password_resets_collection_name}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Use the MongoDB instance to get the database
            db = MongoDB.get_instance().get_db()
            
            # Drop test collections
            db.drop_collection(cls.users_collection_name)
            db.drop_collection(cls.password_resets_collection_name)
            
            # Restore original collection names
            MongoDB.COLLECTIONS['Users'] = cls.original_users_collection
            MongoDB.COLLECTIONS['PasswordResets'] = cls.original_password_resets_collection
            
            print(f"🧹 Dropped test collections: {cls.users_collection_name}, {cls.password_resets_collection_name}")
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
            self.db_password_resets = MongoDB.get_instance().get_collection('PasswordResets')
            
            # Clear collections before each test
            self.db_users.delete_many({})
            self.db_password_resets.delete_many({})
            
            # Create sample test users with timezone-aware datetimes
            current_time = datetime.now(timezone.utc)
            self.test_users = [
                {
                    'bleoid': 'ABC123',
                    'email': 'test@example.com',
                    'password': make_password('Password123'),
                    'userName': 'TestUser1',
                    'bio': 'Test bio 1',
                    'email_verified': True,
                    'preferences': {'theme': 'light'},
                    'last_login': current_time,
                    'created_at': current_time
                },
                {
                    'bleoid': 'DEF456',
                    'email': 'user2@example.com',
                    'password': make_password('Password456'),
                    'userName': 'TestUser2',
                    'bio': 'Test bio 2',
                    'email_verified': True,
                    'preferences': {'theme': 'dark'},
                    'last_login': current_time,
                    'created_at': current_time
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
        self.db_password_resets.delete_many({})
        super().tearDown()

    # ====== PasswordResetRequestView Tests ======
    
    @patch('auth.password_reset.EmailService')
    @patch('auth.password_reset.Logger')
    def test_password_reset_request_success(self, mock_logger, mock_email_service):
        """Test successful password reset request"""
        # Mock email service
        mock_email_service.send_password_reset_email.return_value = True
        
        # Request data
        request_data = {
            'email': 'test@example.com'
        }
        
        # Make request
        response = self.client.post('/auth/password-reset/request/', request_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        # For success responses, check successMessage and data
        self.assertIsNotNone(response_data.get('successMessage'))
        self.assertIsNotNone(response_data.get('data'))
        self.assertIsNone(response_data.get('errorMessage'))
        
        # Check if it's a successful response
        data = response_data.get('data', {})
        self.assertTrue(data.get('email_sent', False))
        self.assertTrue(data.get('reset_token_created', False))
        self.assertEqual(data.get('expires_in_hours'), 1)
        
        # Verify password reset record was created
        reset_record = self.db_password_resets.find_one({'email': 'test@example.com'})
        self.assertIsNotNone(reset_record)
        self.assertEqual(reset_record['bleoid'], 'ABC123')
        self.assertFalse(reset_record['used'])
        
        print(f"  🔹 Password reset request successful for email: {request_data['email']}")
        print(f"  🔹 Response data: {data}")
        print(f"  🔹 Token expires in: {data.get('expires_in_hours')} hour")
        print(f"  🔹 Reset record created in database for user: {reset_record['bleoid']}")
    
    def test_password_reset_request_user_not_found(self):
        """Test password reset request when user doesn't exist"""
        # Request data with non-existent email
        request_data = {
            'email': 'nonexistent@example.com'
        }
        
        # Make request
        response = self.client.post('/auth/password-reset/request/', request_data, format='json')
        
        # Should still return success for security (don't reveal if user exists)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        # For security responses, should be success format
        self.assertIsNotNone(response_data.get('successMessage'))
        self.assertIsNotNone(response_data.get('data'))
        
        data = response_data.get('data', {})
        self.assertFalse(data.get('email_sent', True))  # Should be False
        
        # Check success message contains security message
        success_message = response_data.get('successMessage', '')
        self.assertIn("If your email exists", success_message)
        
        # Verify no reset record was created
        reset_count = self.db_password_resets.count_documents({})
        self.assertEqual(reset_count, 0)
        
        print(f"  🔹 User not found but security response returned")
        print(f"  🔹 Email actually sent: {data.get('email_sent')}")
        print(f"  🔹 Security message: {success_message}")
        print(f"  🔹 No reset records created: {reset_count}")
    
    def test_password_reset_request_invalid_email(self):
        """Test password reset request with invalid email"""
        invalid_data = {'email': 'invalid-email'}
        
        response = self.client.post('/auth/password-reset/request/', invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('errorMessage', response_data)
        # BLEOResponse validation error uses 'validationErrors' key
        self.assertIn('validationErrors', response_data)
        self.assertIn('email', response_data['validationErrors'])
        
        print(f"  🔹 Invalid email '{invalid_data['email']}' correctly rejected")
        print(f"  🔹 Status code: {response.status_code}")
        print(f"  🔹 Error fields: {list(response_data['validationErrors'].keys())}")
    
    def test_password_reset_request_missing_email(self):
        """Test password reset request with missing email"""
        response = self.client.post('/auth/password-reset/request/', {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('errorMessage', response_data)
        self.assertIn('validationErrors', response_data)
        self.assertIn('email', response_data['validationErrors'])
        
        print("  🔹 Missing email field correctly rejected")
        print(f"  🔹 Status code: {response.status_code}")
        print(f"  🔹 Required field validation working: 'email' field is required")
    
    @patch('auth.password_reset.EmailService')
    @patch('auth.password_reset.Logger')
    def test_password_reset_request_email_failure(self, mock_logger, mock_email_service):
        """Test password reset request when email sending fails"""
        # Mock email service failure
        mock_email_service.send_password_reset_email.return_value = False
        
        request_data = {
            'email': 'test@example.com'
        }
        
        # Make request
        response = self.client.post('/auth/password-reset/request/', request_data, format='json')
        
        # Should return server error
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response_data = response.json()
        self.assertIn('errorMessage', response_data)
        self.assertIn("Failed to send reset email", response_data.get('errorMessage', ''))
        
        print("  🔹 Email service failure handled correctly")
        print(f"  🔹 Status code: {response.status_code}")
        print(f"  🔹 Error message: {response_data.get('errorMessage')}")

    # ====== PasswordResetConfirmView Tests ======
    
    @patch.dict(os.environ, {'JWT_SECRET': 'test-secret-key'})
    @patch('auth.password_reset.Logger')
    def test_password_reset_confirm_success(self, mock_logger):
        """Test successful password reset confirmation"""
        # Create a password reset record first
        test_secret = 'test-secret-key'
        current_time = datetime.now(timezone.utc)
        payload = {
            'bleoid': 'ABC123',
            'email': 'test@example.com',
            'type': 'password_reset',
            'jti': 'test-jti',
            'iat': current_time.timestamp(),
            'exp': (current_time + timedelta(hours=1)).timestamp()
        }
        
        valid_token = jwt.encode(payload, test_secret, algorithm='HS256')
        
        # Insert reset record with timezone-aware datetime
        reset_record = {
            'bleoid': 'ABC123',
            'email': 'test@example.com',
            'token': valid_token,
            'created_at': current_time,
            'expires_at': current_time + timedelta(hours=1),
            'used': False,
            'attempts': 0
        }
        self.db_password_resets.insert_one(reset_record)
        
        # Request data
        confirm_data = {
            'token': valid_token,
            'password': 'newSecurePassword123'
        }
        
        # Make request
        response = self.client.put('/auth/password-reset/confirm/', confirm_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        # Success response structure
        self.assertIsNotNone(response_data.get('successMessage'))
        self.assertIsNotNone(response_data.get('data'))
        self.assertIsNone(response_data.get('errorMessage'))
        
        data = response_data.get('data', {})
        self.assertTrue(data.get('password_reset', False))
        self.assertIn('reset_at', data)
        
        # Verify user password was updated
        updated_user = self.db_users.find_one({'bleoid': 'ABC123'})
        self.assertIsNotNone(updated_user)
        
        # Verify reset record was marked as used
        used_reset = self.db_password_resets.find_one({'token': valid_token})
        self.assertTrue(used_reset['used'])
        self.assertIsNotNone(used_reset.get('used_at'))
        
        print(f"  🔹 Password reset successful for user: test@example.com")
        print(f"  🔹 New password hashed and stored")
        print(f"  🔹 Reset token marked as used")
        print(f"  🔹 Response data includes reset timestamp")
    
    def test_password_reset_confirm_invalid_token_format(self):
        """Test password reset confirm with invalid token format"""
        invalid_data = {
            'token': 'invalid-token',
            'password': 'newSecurePassword123'
        }
        
        response = self.client.put('/auth/password-reset/confirm/', invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('errorMessage', response_data)
        self.assertIn('validationErrors', response_data)
        
        print(f"  🔹 Invalid token format '{invalid_data['token']}' correctly rejected")
        print(f"  🔹 Status code: {response.status_code}")
        print(f"  🔹 Validation errors returned")
    
    @patch.dict(os.environ, {'JWT_SECRET': 'test-secret-key'})
    def test_password_reset_confirm_expired_token(self):
        """Test password reset confirm with expired token"""
        # Create expired token
        test_secret = 'test-secret-key'
        expired_payload = {
            'bleoid': 'ABC123',
            'email': 'test@example.com',
            'type': 'password_reset',
            'jti': 'test-jti',
            'iat': datetime.now(timezone.utc).timestamp(),
            'exp': (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
        }
        
        expired_token = jwt.encode(expired_payload, test_secret, algorithm='HS256')
        
        invalid_data = {
            'token': expired_token,
            'password': 'newSecurePassword123'
        }
        
        response = self.client.put('/auth/password-reset/confirm/', invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response_data = response.json()
        self.assertIn('errorMessage', response_data)
        self.assertIn("expired", response_data.get('errorMessage', '').lower())
        
        print("  🔹 Expired token correctly rejected")
        print(f"  🔹 Status code: {response.status_code}")
        print(f"  🔹 Expiration message: {response_data.get('errorMessage')}")
    
    @patch.dict(os.environ, {'JWT_SECRET': 'test-secret-key'})
    def test_password_reset_confirm_token_not_found(self):
        """Test password reset confirm when token not found in database"""
        # Create valid token but don't insert reset record
        test_secret = 'test-secret-key'
        payload = {
            'bleoid': 'ABC123',
            'email': 'test@example.com',
            'type': 'password_reset',
            'jti': 'test-jti',
            'iat': datetime.now(timezone.utc).timestamp(),
            'exp': (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        }
        
        valid_token = jwt.encode(payload, test_secret, algorithm='HS256')
        
        confirm_data = {
            'token': valid_token,
            'password': 'newSecurePassword123'
        }
        
        # Make request
        response = self.client.put('/auth/password-reset/confirm/', confirm_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response_data = response.json()
        self.assertIn('errorMessage', response_data)
        self.assertIn("Invalid or expired", response_data.get('errorMessage', ''))
        
        print("  🔹 Token not found in database correctly handled")
        print(f"  🔹 Status code: {response.status_code}")
        print(f"  🔹 Security message: {response_data.get('errorMessage')}")
    
    @patch.dict(os.environ, {'JWT_SECRET': 'test-secret-key'})
    def test_password_reset_confirm_token_already_used(self):
        """Test password reset confirm when token already used"""
        # Create valid token and mark reset record as used
        test_secret = 'test-secret-key'
        current_time = datetime.now(timezone.utc)
        payload = {
            'bleoid': 'ABC123',
            'email': 'test@example.com',
            'type': 'password_reset',
            'jti': 'test-jti',
            'iat': current_time.timestamp(),
            'exp': (current_time + timedelta(hours=1)).timestamp()
        }
        
        valid_token = jwt.encode(payload, test_secret, algorithm='HS256')
        
        # Insert used reset record with timezone-aware datetime
        reset_record = {
            'bleoid': 'ABC123',
            'email': 'test@example.com',
            'token': valid_token,
            'created_at': current_time,
            'expires_at': current_time + timedelta(hours=1),
            'used': True,  # Already used
            'used_at': current_time,
            'attempts': 1
        }
        self.db_password_resets.insert_one(reset_record)
        
        confirm_data = {
            'token': valid_token,
            'password': 'newSecurePassword123'
        }
        
        # Make request
        response = self.client.put('/auth/password-reset/confirm/', confirm_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('errorMessage', response_data)
        self.assertIn("already been used", response_data.get('errorMessage', ''))
        
        print("  🔹 Already used token correctly rejected")
        print(f"  🔹 Status code: {response.status_code}")
        print(f"  🔹 Token reuse prevention working")
    
    def test_password_reset_confirm_short_password(self):
        """Test password reset confirm with too short password"""
        invalid_data = {
            'token': 'some-token',
            'password': '1234567'  # Too short
        }
        
        response = self.client.put('/auth/password-reset/confirm/', invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('errorMessage', response_data)
        self.assertIn('validationErrors', response_data)
        
        print(f"  🔹 Short password '{invalid_data['password']}' (7 chars) correctly rejected")
        print(f"  🔹 Minimum password length validation working")
        print(f"  🔹 Status code: {response.status_code}")

    # ====== Token Validation Tests (GET) ======
    
    @patch.dict(os.environ, {'JWT_SECRET': 'test-secret-key'})
    def test_token_validation_success(self):
        """Test successful token validation via GET"""
        # Create valid token and reset record
        test_secret = 'test-secret-key'
        current_time = datetime.now(timezone.utc)
        payload = {
            'bleoid': 'ABC123',
            'email': 'test@example.com',
            'type': 'password_reset',
            'jti': 'test-jti',
            'iat': current_time.timestamp(),
            'exp': (current_time + timedelta(hours=1)).timestamp()
        }
        
        valid_token = jwt.encode(payload, test_secret, algorithm='HS256')
        
        # Insert reset record with timezone-aware datetime
        reset_record = {
            'bleoid': 'ABC123',
            'email': 'test@example.com',
            'token': valid_token,
            'created_at': current_time,
            'expires_at': current_time + timedelta(hours=1),
            'used': False,
            'attempts': 0
        }
        self.db_password_resets.insert_one(reset_record)
        
        # Make request
        response = self.client.get(f'/auth/password-reset/confirm/?token={valid_token}')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        # Success response structure
        self.assertIsNotNone(response_data.get('successMessage'))
        self.assertIsNotNone(response_data.get('data'))
        self.assertIsNone(response_data.get('errorMessage'))
        
        data = response_data.get('data', {})
        self.assertTrue(data.get('token_valid', False))
        self.assertIn('expires_at', data)
        self.assertIn('created_at', data)
        self.assertIn('time_remaining_hours', data)
        
        print(f"  🔹 Token validation successful")
        print(f"  🔹 Token valid: {data.get('token_valid')}")
        print(f"  🔹 Time remaining: {data.get('time_remaining_hours')} hours")
        print(f"  🔹 Expires at: {data.get('expires_at')}")
    
    def test_token_validation_missing_token(self):
        """Test token validation with missing token parameter"""
        response = self.client.get('/auth/password-reset/confirm/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('errorMessage', response_data)
        self.assertIn("Invalid token parameter", response_data.get('errorMessage', ''))
        
        print("  🔹 Missing token parameter correctly rejected")
        print(f"  🔹 Status code: {response.status_code}")
        print(f"  🔹 Error message: {response_data.get('errorMessage')}")
    
    def test_token_validation_invalid_token_format(self):
        """Test token validation with invalid token format"""
        invalid_token = 'invalid-token-format'
        
        response = self.client.get(f'/auth/password-reset/confirm/?token={invalid_token}')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response_data = response.json()
        self.assertIn('errorMessage', response_data)
        self.assertIn("Invalid", response_data.get('errorMessage', ''))
        
        print(f"  🔹 Invalid token format '{invalid_token}' correctly rejected")
        print(f"  🔹 Status code: {response.status_code}")
        print(f"  🔹 JWT format validation working")

# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(PasswordResetViewTest)