from tests.base_test import BLEOBaseTest, run_test_with_output
from rest_framework.test import APIClient
from auth.email_verification import EmailVerificationView
from models.EmailVerification import EmailVerification
from utils.mongodb_utils import MongoDB
from django.contrib.auth.hashers import make_password
from datetime import datetime, timedelta, timezone
from django.urls import path
from django.test import override_settings
from unittest.mock import patch, MagicMock
import jwt
import os
import time
import random

# Set up URL configuration for testing
urlpatterns = [
    path('auth/email/verify/', EmailVerificationView.as_view(), name='email-verification'),
]

@override_settings(ROOT_URLCONF=__name__)
class EmailVerificationViewTest(BLEOBaseTest):
    """Test cases for EmailVerificationView with MongoDB test collections"""
    
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
        cls.email_verifications_collection_name = f"EmailVerifications_{cls.test_suffix}"
        
        # Store original collection names to restore later
        cls.original_users_collection = MongoDB.COLLECTIONS['Users']
        cls.original_email_verifications_collection = MongoDB.COLLECTIONS['EmailVerifications']
        
        # Override collection names for testing
        MongoDB.COLLECTIONS['Users'] = cls.users_collection_name
        MongoDB.COLLECTIONS['EmailVerifications'] = cls.email_verifications_collection_name
        
        print(f"🔧 Created test collections: {cls.users_collection_name}, {cls.email_verifications_collection_name}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Use the MongoDB instance to get the database instead of direct client access
            db = MongoDB.get_instance().get_db()
            
            # Drop test collections
            db.drop_collection(cls.users_collection_name)
            db.drop_collection(cls.email_verifications_collection_name)
            
            # Restore original collection names
            MongoDB.COLLECTIONS['Users'] = cls.original_users_collection
            MongoDB.COLLECTIONS['EmailVerifications'] = cls.original_email_verifications_collection
            
            print(f"🧹 Dropped test collections: {cls.users_collection_name}, {cls.email_verifications_collection_name}")
        except Exception as e:
            print(f"Error cleaning up test collections: {e}")
    
    def setUp(self):
        super().setUp()
        
        # Create test user
        self.test_user_data = {
            'bleoid': 'TEST01',
            'email': 'test@example.com',
            'password': make_password('Password123'),
            'userName': 'TestUser',
            'email_verified': False,
            'created_at': datetime.now(timezone.utc)
        }
        
        db_users = MongoDB.get_instance().get_collection('Users')
        db_users.insert_one(self.test_user_data)
    
    @patch('services.EmailService.EmailService.send_verification_email', return_value=True)  # ← Fix path!
    def test_send_verification_email(self, mock_send_email):
        """Test sending verification email"""
        data = {'email': 'test@example.com'}
        response = self.client.post('/auth/email/verify/', data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['successMessage'], 'Verification email sent successfully. Please check your inbox.')
        
        # Check that verification record was created
        db_verification = MongoDB.get_instance().get_collection('EmailVerifications')
        verification_record = db_verification.find_one({'email': 'test@example.com'})
        
        self.assertIsNotNone(verification_record)
        self.assertEqual(verification_record['bleoid'], 'TEST01')
        self.assertFalse(verification_record['verified'])
        
        print("  🔹 Email verification request sent successfully")
    
    @patch('services.EmailService.EmailService.send_verification_email', return_value=True)  # ← Fix path!
    def test_verify_email_with_valid_token(self, mock_send_email):
        """Test email verification with valid token"""
        # First send verification email
        data = {'email': 'test@example.com'}
        post_response = self.client.post('/auth/email/verify/', data, format='json')

        # Make sure POST succeeded before proceeding
        self.assertEqual(post_response.status_code, 200)
        
        # Get the token from database
        db_verification = MongoDB.get_instance().get_collection('EmailVerifications')
        verification_record = db_verification.find_one({'email': 'test@example.com'})
        
        self.assertIsNotNone(verification_record, "Verification record should exist")
        
        token = verification_record['token']
        
        # Verify email
        verify_data = {
            'token': token
        }

        import json
        response = self.client.put(
            '/auth/email/verify/', 
            data=json.dumps(verify_data), 
            content_type='application/json'
        )        
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['successMessage'], 'Email verified successfully! Your account is now active.')
        
        # Check that user is now verified
        db_users = MongoDB.get_instance().get_collection('Users')
        user = db_users.find_one({'email': 'test@example.com'})
        self.assertTrue(user['email_verified'])
        
        print("  🔹 Email verification completed successfully")
    
    def test_verification_status_check(self):
        """Test checking verification status"""
        response = self.client.get('/auth/email/verify/?email=test@example.com')
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['data']['email_verified'])
        
        print("  🔹 Email verification status check works")
    
    @patch('services.EmailService.EmailService.send_verification_email', return_value=True)
    def test_serializer_validation_in_post(self, mock_send_email):
        """Test serializer validation in POST request"""
        # Test invalid email format
        invalid_data = {'email': 'invalid-email'}
        response = self.client.post('/auth/email/verify/', invalid_data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid request data', response.data['errorMessage'])
        
        # Test missing email
        empty_data = {}
        response = self.client.post('/auth/email/verify/', empty_data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid request data', response.data['errorMessage'])
        
        # Test valid email
        valid_data = {'email': 'test@example.com'}
        response = self.client.post('/auth/email/verify/', valid_data, format='json')
        
        self.assertEqual(response.status_code, 200)
        mock_send_email.assert_called_once()
        
        print("  🔹 POST request serializer validation works correctly")
    
    @patch('services.EmailService.EmailService.send_verification_email', return_value=True)
    def test_serializer_validation_in_put(self, mock_send_email):
        """Test serializer validation in PUT request"""
        # First create a verification
        data = {'email': 'test@example.com'}
        self.client.post('/auth/email/verify/', data, format='json')
        
        # Test invalid token format
        invalid_token_data = {'token': 'invalid'}
        import json
        response = self.client.put(
            '/auth/email/verify/',
            data=json.dumps(invalid_token_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid request data', response.data['errorMessage'])
        
        # Test missing token
        empty_data = {}
        response = self.client.put(
            '/auth/email/verify/',
            data=json.dumps(empty_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid request data', response.data['errorMessage'])
        
        print("  🔹 PUT request serializer validation works correctly")

# Run the test
if __name__ == '__main__':
    test = EmailVerificationViewTest()
    test.setUp()
    test.test_send_verification_email()
    test.test_verify_email_with_valid_token()
    test.test_verification_status_check()
    test.test_serializer_validation_in_post()
    test.test_serializer_validation_in_put()