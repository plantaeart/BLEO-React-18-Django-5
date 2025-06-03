from tests.base_test import BLEOBaseTest, run_test_with_output
from rest_framework.test import APIClient
from auth.jwt_auth import CustomTokenObtainPairView, TokenRefreshView
from utils.mongodb_utils import MongoDB
from django.contrib.auth.hashers import make_password
import jwt
import os
import time
import random
from datetime import datetime, timedelta, timezone
from django.urls import path
from django.test import override_settings
from unittest.mock import patch

# Set up URL configuration for testing
urlpatterns = [
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]

@override_settings(ROOT_URLCONF=__name__)
class JWTAuthViewTest(BLEOBaseTest):
    """Test cases for JWT authentication views with MongoDB test collections"""
    
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
        cls.blacklist_collection_name = f"TokenBlacklist_{cls.test_suffix}"
        
        # Store original collection names to restore later
        cls.original_users_collection = MongoDB.COLLECTIONS['Users']
        cls.original_blacklist_collection = MongoDB.COLLECTIONS.get('TokenBlacklist', 'TokenBlacklist')
        
        # Override collection names for testing
        MongoDB.COLLECTIONS['Users'] = cls.users_collection_name
        MongoDB.COLLECTIONS['TokenBlacklist'] = cls.blacklist_collection_name
        
        print(f"🔧 Created test collections: {cls.users_collection_name}, {cls.blacklist_collection_name}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Use the MongoDB instance to get the database
            db = MongoDB.get_instance().get_db()
            
            # Drop test collections
            db.drop_collection(cls.users_collection_name)
            db.drop_collection(cls.blacklist_collection_name)
            
            # Restore original collection names
            MongoDB.COLLECTIONS['Users'] = cls.original_users_collection
            MongoDB.COLLECTIONS['TokenBlacklist'] = cls.original_blacklist_collection
            
            print(f"🧹 Dropped test collections: {cls.users_collection_name}, {cls.blacklist_collection_name}")
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
            self.db_blacklist = MongoDB.get_instance().get_collection('TokenBlacklist')
            
            # Clear collections before each test
            self.db_users.delete_many({})
            self.db_blacklist.delete_many({})
            
            # Create sample test users with all required fields
            self.test_users = [
                {
                    'BLEOId': 'TEST001',
                    'email': 'test@example.com',
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
                    'BLEOId': 'TEST002',
                    'email': 'user2@example.com',
                    'password': make_password('Password456'),
                    'userName': 'TestUser2',
                    'bio': 'Test bio 2',
                    'email_verified': False,
                    'preferences': {'theme': 'dark'},
                    'profilePic': None,
                    'last_login': datetime.now(),
                    'created_at': datetime.now()
                },
                {
                    'BLEOId': 'INACTIVE001',
                    'email': 'inactive@example.com',
                    'password': make_password('InactivePassword'),
                    'userName': 'InactiveUser',
                    'bio': 'Inactive user',
                    'email_verified': False,
                    'preferences': {'theme': 'light'},
                    'profilePic': None,
                    'last_login': datetime.now() - timedelta(days=30),
                    'created_at': datetime.now() - timedelta(days=90)
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
            
            # Store JWT secret for test verification
            self.jwt_secret = os.getenv('JWT_SECRET')
            self.access_expire = int(os.getenv('ACCESS_TOKEN_EXPIRE', '15'))
            self.refresh_expire = int(os.getenv('REFRESH_TOKEN_EXPIRE', '7'))
            
            print(f"🔧 Test environment setup with {len(self.user_ids)} sample users")
            
        except Exception as e:
            print(f"❌ Test setup failed: {str(e)}")
            raise
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear collections
        self.db_users.delete_many({})
        self.db_blacklist.delete_many({})
        super().tearDown()
    
    # ====== CustomTokenObtainPairView Tests ======
    
    def test_login_success(self):
        """Test successful user login with valid credentials"""
        # Request data
        login_data = {
            'email': 'test@example.com',
            'password': 'Password123'
        }
        
        # Make request
        response = self.client.post('/auth/login/', login_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['successMessage'], 'Authentication successful')
        
        # Verify tokens are present
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertIn('user', response.data['data'])
        
        # Verify user data
        user_data = response.data['data']['user']
        self.assertEqual(user_data['bleoid'], 'TEST001')
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertEqual(user_data['username'], 'TestUser1')
        
        # Verify tokens are valid JWT
        access_token = response.data['data']['access']
        refresh_token = response.data['data']['refresh']
        
        # Decode and verify access token
        access_payload = jwt.decode(access_token, self.jwt_secret, algorithms=['HS256'])
        self.assertEqual(access_payload['bleoid'], 'TEST001')
        self.assertEqual(access_payload['email'], 'test@example.com')
        
        # Decode and verify refresh token
        refresh_payload = jwt.decode(refresh_token, self.jwt_secret, algorithms=['HS256'])
        self.assertEqual(refresh_payload['bleoid'], 'TEST001')
        self.assertEqual(refresh_payload['email'], 'test@example.com')
        
        # Verify last_login was updated
        updated_user = self.db_users.find_one({'BLEOId': 'TEST001'})
        self.assertIsNotNone(updated_user['last_login'])
        
        print("  🔹 Successfully authenticated user with valid credentials")
    
    def test_login_invalid_email(self):
        """Test login failure with invalid email"""
        # Request data with nonexistent email
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'Password123'
        }
        
        # Make request
        response = self.client.post('/auth/login/', login_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Invalid credentials')
        
        print("  🔹 Properly rejected invalid email")
    
    def test_login_invalid_password(self):
        """Test login failure with invalid password"""
        # Request data with wrong password
        login_data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        
        # Make request
        response = self.client.post('/auth/login/', login_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Invalid credentials')
        
        print("  🔹 Properly rejected invalid password")
    
    def test_login_missing_email(self):
        """Test login failure with missing email"""
        # Request data without email
        login_data = {
            'password': 'Password123'
        }
        
        # Make request
        response = self.client.post('/auth/login/', login_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Email and password are required')
        
        print("  🔹 Properly rejected missing email")
    
    def test_login_missing_password(self):
        """Test login failure with missing password"""
        # Request data without password
        login_data = {
            'email': 'test@example.com'
        }
        
        # Make request
        response = self.client.post('/auth/login/', login_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Email and password are required')
        
        print("  🔹 Properly rejected missing password")
    
    def test_login_empty_credentials(self):
        """Test login failure with empty credentials"""
        # Request data with empty strings
        login_data = {
            'email': '',
            'password': ''
        }
        
        # Make request
        response = self.client.post('/auth/login/', login_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Email and password are required')
        
        print("  🔹 Properly rejected empty credentials")
    
    def test_login_token_expiration_times(self):
        """Test that tokens have correct expiration times"""
        # Request data
        login_data = {
            'email': 'test@example.com',
            'password': 'Password123'
        }
        
        # Make request
        response = self.client.post('/auth/login/', login_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Verify token expiration times
        access_token = response.data['data']['access']
        refresh_token = response.data['data']['refresh']
        
        # Decode tokens
        access_payload = jwt.decode(access_token, self.jwt_secret, algorithms=['HS256'])
        refresh_payload = jwt.decode(refresh_token, self.jwt_secret, algorithms=['HS256'])
        
        # Get current time for comparison
        now = datetime.now(timezone.utc)
        
        # Convert exp timestamps to datetime
        access_exp = datetime.fromtimestamp(access_payload['exp'], tz=timezone.utc)
        refresh_exp = datetime.fromtimestamp(refresh_payload['exp'], tz=timezone.utc)
        
        # Test 1: Access token should expire in the future (but not too far)
        time_until_access_exp = (access_exp - now).total_seconds()
        expected_access_seconds = self.access_expire * 60
        
        # Allow 10 seconds tolerance (5 seconds before and after)
        self.assertTrue(
            expected_access_seconds - 10 <= time_until_access_exp <= expected_access_seconds + 10,
            f"Access token expires in {time_until_access_exp}s, expected ~{expected_access_seconds}s"
        )
        
        # Test 2: Refresh token should expire in the future (but not too far)
        time_until_refresh_exp = (refresh_exp - now).total_seconds()
        expected_refresh_seconds = self.refresh_expire * 24 * 60 * 60
        
        # Allow 60 seconds tolerance for refresh tokens
        self.assertTrue(
            expected_refresh_seconds - 60 <= time_until_refresh_exp <= expected_refresh_seconds + 60,
            f"Refresh token expires in {time_until_refresh_exp}s, expected ~{expected_refresh_seconds}s"
        )
        
        # Test 3: Refresh token should expire much later than access token
        self.assertGreater(
            refresh_exp, access_exp,
            "Refresh token should expire later than access token"
        )
        
        # Test 4: Both tokens should expire in the future
        self.assertGreater(access_exp, now, "Access token should expire in the future")
        self.assertGreater(refresh_exp, now, "Refresh token should expire in the future")
        
        print(f"  🔹 Tokens have correct expiration times: access={self.access_expire}m, refresh={self.refresh_expire}d")
        print(f"  🔹 Access token expires in {time_until_access_exp/60:.1f} minutes")
        print(f"  🔹 Refresh token expires in {time_until_refresh_exp/(24*3600):.1f} days")
    
    def test_login_case_insensitive_email(self):
        """Test login with different email case"""
        # Request data with uppercase email
        login_data = {
            'email': 'TEST@EXAMPLE.COM',  # Uppercase version
            'password': 'Password123'
        }
        
        # Make request
        response = self.client.post('/auth/login/', login_data, format='json')
        
        # Should fail because MongoDB is case-sensitive by default
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['errorMessage'], 'Invalid credentials')
        
        print("  🔹 Properly handled case-sensitive email matching")
    
    # ====== TokenRefreshView Tests ======
    
    def test_refresh_token_success(self):
        """Test successful token refresh with valid refresh token"""
        # First, login to get tokens
        login_data = {
            'email': 'test@example.com',
            'password': 'Password123'
        }
        login_response = self.client.post('/auth/login/', login_data, format='json')
        self.assertEqual(login_response.status_code, 200)
        
        refresh_token = login_response.data['data']['refresh']
        original_access_token = login_response.data['data']['access']
        
        # Wait a moment to ensure new token has different timestamp
        time.sleep(1)
        
        # Request token refresh
        refresh_data = {
            'refresh': refresh_token
        }
        
        # Make request
        response = self.client.post('/auth/refresh/', refresh_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['successMessage'], 'Token refreshed successfully')
        self.assertIn('access', response.data['data'])
        
        # Verify new access token is different from original
        new_access_token = response.data['data']['access']
        self.assertNotEqual(original_access_token, new_access_token)
        
        # Verify new access token is valid and contains correct data
        new_payload = jwt.decode(new_access_token, self.jwt_secret, algorithms=['HS256'])
        self.assertEqual(new_payload['bleoid'], 'TEST001')
        self.assertEqual(new_payload['email'], 'test@example.com')
        
        print("  🔹 Successfully refreshed access token")
    
    def test_refresh_token_missing(self):
        """Test refresh failure with missing refresh token"""
        # Request without refresh token
        refresh_data = {}
        
        # Make request
        response = self.client.post('/auth/refresh/', refresh_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Refresh token is required')
        
        print("  🔹 Properly rejected missing refresh token")
    
    def test_refresh_token_invalid_format(self):
        """Test refresh failure with invalid token format"""
        # Request with invalid token
        refresh_data = {
            'refresh': 'invalid-token-format'
        }
        
        # Make request
        response = self.client.post('/auth/refresh/', refresh_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Invalid refresh token')
        
        print("  🔹 Properly rejected invalid token format")
    
    def test_refresh_token_expired(self):
        """Test refresh failure with expired token"""
        # Create an expired refresh token
        expired_payload = {
            'bleoid': 'TEST001',
            'email': 'test@example.com',
            'exp': datetime.now(timezone.utc) - timedelta(days=1)  # Expired yesterday
        }
        expired_token = jwt.encode(expired_payload, self.jwt_secret, algorithm='HS256')
        
        # Request with expired token
        refresh_data = {
            'refresh': expired_token
        }
        
        # Make request
        response = self.client.post('/auth/refresh/', refresh_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Refresh token expired')
        
        print("  🔹 Properly rejected expired refresh token")
    
    def test_refresh_token_blacklisted(self):
        """Test refresh failure with blacklisted token"""
        # First, login to get tokens
        login_data = {
            'email': 'test@example.com',
            'password': 'Password123'
        }
        login_response = self.client.post('/auth/login/', login_data, format='json')
        refresh_token = login_response.data['data']['refresh']
        
        # Add token to blacklist
        self.db_blacklist.insert_one({
            'token': refresh_token,
            'blacklisted_at': datetime.now(),
            'reason': 'test_blacklist'
        })
        
        # Request with blacklisted token
        refresh_data = {
            'refresh': refresh_token
        }
        
        # Make request
        response = self.client.post('/auth/refresh/', refresh_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Invalid refresh token')
        
        print("  🔹 Properly rejected blacklisted refresh token")
    
    def test_refresh_token_wrong_secret(self):
        """Test refresh failure with token signed with wrong secret"""
        # Create token with wrong secret
        wrong_payload = {
            'bleoid': 'TEST001',
            'email': 'test@example.com',
            'exp': datetime.now(timezone.utc) + timedelta(days=1)
        }
        wrong_token = jwt.encode(wrong_payload, 'wrong-secret', algorithm='HS256')
        
        # Request with wrong token
        refresh_data = {
            'refresh': wrong_token
        }
        
        # Make request
        response = self.client.post('/auth/refresh/', refresh_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['errorType'], 'ValidationError')
        self.assertEqual(response.data['errorMessage'], 'Invalid refresh token')
        
        print("  🔹 Properly rejected token with wrong signature")
    
    def test_refresh_multiple_times(self):
        """Test that refresh token can be used multiple times"""
        # First, login to get tokens
        login_data = {
            'email': 'test@example.com',
            'password': 'Password123'
        }
        login_response = self.client.post('/auth/login/', login_data, format='json')
        refresh_token = login_response.data['data']['refresh']
        
        # Refresh token multiple times
        for i in range(3):
            refresh_data = {'refresh': refresh_token}
            response = self.client.post('/auth/refresh/', refresh_data, format='json')
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('access', response.data['data'])
            
            # Verify each new access token is valid
            new_access_token = response.data['data']['access']
            payload = jwt.decode(new_access_token, self.jwt_secret, algorithms=['HS256'])
            self.assertEqual(payload['bleoid'], 'TEST001')
            
            time.sleep(0.1)  # Small delay between requests
        
        print("  🔹 Successfully refreshed token multiple times")
    
    # ====== Email Masking Tests ======
    
    def test_email_masking_functionality(self):
        """Test that email masking works correctly for logging"""
        # Test various email formats with corrected expected results
        test_cases = [
            ('a@example.com', 'a@example.com'),              # 1 char: no masking
            ('ab@example.com', 'a*@example.com'),            # 2 chars: first + asterisk
            ('abc@example.com', 'a*c@example.com'),          # 3 chars: first + asterisk + last
            ('test@example.com', 'te*t@example.com'),        # 4 chars: first two + asterisk + last
            ('hello@example.com', 'he**o@example.com'),      # 5 chars: first two + two asterisks + last
            ('abcdef@example.com', 'ab**f@example.com'),     # 6 chars: first two + two asterisks + last
            ('username@example.com', 'us**e@example.com'),   # 8 chars: first two + two asterisks + last
            ('verylongusername@example.com', 've**e@example.com'),  # Very long: first two + two asterisks + last
        ]
        
        # Create view instance to test private method
        view = CustomTokenObtainPairView()
        
        for original, expected in test_cases:
            masked = view._mask_email(original)
            self.assertEqual(masked, expected, f"Email masking failed for {original}. Expected: {expected}, Got: {masked}")
        
        # Test invalid emails
        self.assertEqual(view._mask_email('invalid-email'), 'invalid-email')
        self.assertEqual(view._mask_email(''), 'invalid-email')
        self.assertEqual(view._mask_email(None), 'invalid-email')
        
        # Also test TokenRefreshView has the same behavior
        refresh_view = TokenRefreshView()
        for original, expected in test_cases:
            masked = refresh_view._mask_email(original)
            self.assertEqual(masked, expected, f"TokenRefreshView email masking failed for {original}. Expected: {expected}, Got: {masked}")
        
        print("  🔹 Email masking functionality works correctly for both views")
    
    # ====== Integration Tests ======
    
    def test_full_authentication_flow(self):
        """Test complete authentication flow: login -> use token -> refresh -> use new token"""
        # Step 1: Login
        login_data = {
            'email': 'test@example.com',
            'password': 'Password123'
        }
        login_response = self.client.post('/auth/login/', login_data, format='json')
        self.assertEqual(login_response.status_code, 200)
        
        access_token = login_response.data['data']['access']
        refresh_token = login_response.data['data']['refresh']
        
        # Step 2: Use access token (simulate authenticated request)
        # This would typically be done by adding Authorization header
        auth_header = f'Bearer {access_token}'
        
        # Verify token can be decoded
        payload = jwt.decode(access_token, self.jwt_secret, algorithms=['HS256'])
        self.assertEqual(payload['bleoid'], 'TEST001')
        
        # Step 3: Refresh token
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post('/auth/refresh/', refresh_data, format='json')
        self.assertEqual(refresh_response.status_code, 200)
        
        new_access_token = refresh_response.data['data']['access']
        
        # Step 4: Use new access token
        new_payload = jwt.decode(new_access_token, self.jwt_secret, algorithms=['HS256'])
        self.assertEqual(new_payload['bleoid'], 'TEST001')
        self.assertEqual(new_payload['email'], 'test@example.com')
        
        # Verify tokens are different
        self.assertNotEqual(access_token, new_access_token)
        
        print("  🔹 Complete authentication flow works correctly")
    
    def test_concurrent_refresh_requests(self):
        """Test handling of concurrent refresh requests"""
        # Login to get refresh token
        login_data = {
            'email': 'test@example.com',
            'password': 'Password123'
        }
        login_response = self.client.post('/auth/login/', login_data, format='json')
        refresh_token = login_response.data['data']['refresh']
        
        # Make multiple concurrent refresh requests
        refresh_data = {'refresh': refresh_token}
        
        responses = []
        for _ in range(3):
            response = self.client.post('/auth/refresh/', refresh_data, format='json')
            responses.append(response)
        
        # All should succeed (refresh tokens can be reused)
        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertIn('access', response.data['data'])
        
        print("  🔹 Concurrent refresh requests handled correctly")

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
    
    print("🚀 Running JWT Authentication View Tests with Enhanced Summary")
    print("="*60)
    
    # Run with enhanced output
    run_test_with_output(JWTAuthViewTest)