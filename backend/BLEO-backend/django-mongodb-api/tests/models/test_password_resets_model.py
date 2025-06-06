import unittest
from datetime import datetime, timezone, timedelta
from models.PasswordResets import PasswordResets
import jwt
import os
from unittest.mock import patch
from tests.base_test import BLEOBaseTest, run_test_with_output

class TestPasswordResetsModel(BLEOBaseTest):
    """Test cases for PasswordResets model"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        self.test_bleoid = "ABC123"
        self.test_email = "test@example.com"
        self.test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
        self.now = datetime.now(timezone.utc)
        self.expires_at = self.now + timedelta(hours=24)
    
    def test_password_reset_creation(self):
        """Test creating a PasswordResets instance"""
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            created_at=self.now,
            expires_at=self.expires_at
        )
        
        self.assertEqual(reset.bleoid, self.test_bleoid)
        self.assertEqual(reset.email, self.test_email)
        self.assertEqual(reset.token, self.test_token)
        self.assertEqual(reset.created_at, self.now)
        self.assertEqual(reset.expires_at, self.expires_at)
        self.assertFalse(reset.used)
        self.assertEqual(reset.attempts, 0)
        self.assertIsNone(reset.used_at)
        
        print(f"  🔹 PasswordReset created with BLEOID: {reset.bleoid}, Email: {reset.email}")
        print(f"  🔹 Default values set - Used: {reset.used}, Attempts: {reset.attempts}")
    
    def test_password_reset_creation_with_defaults(self):
        """Test creating a PasswordResets instance with default values"""
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=self.expires_at
        )
        
        # created_at should be set to current time
        self.assertIsInstance(reset.created_at, datetime)
        self.assertIsNotNone(reset.created_at.tzinfo)
        self.assertFalse(reset.used)
        self.assertEqual(reset.attempts, 0)
        
        print(f"  🔹 Default created_at timestamp set to current time: {reset.created_at}")
    
    def test_to_dict_conversion(self):
        """Test converting PasswordResets to dictionary"""
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            created_at=self.now,
            expires_at=self.expires_at
        )
        
        result = reset.to_dict()
        
        expected = {
            'bleoid': self.test_bleoid,
            'email': self.test_email,
            'token': self.test_token,
            'created_at': self.now,
            'expires_at': self.expires_at,
            'used': False,
            'attempts': 0
        }
        
        self.assertEqual(result, expected)
        
        print("  🔹 to_dict method returns complete dictionary with all fields")
    
    def test_to_dict_with_used_at(self):
        """Test to_dict includes used_at when token is used"""
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            created_at=self.now,
            expires_at=self.expires_at,
            used=True,
            used_at=self.now
        )
        
        result = reset.to_dict()
        
        self.assertIn('used_at', result)
        self.assertEqual(result['used_at'], self.now)
        
        print("  🔹 to_dict includes used_at field when token is used")
    
    def test_from_dict_creation(self):
        """Test creating PasswordResets from dictionary"""
        data = {
            'bleoid': self.test_bleoid,
            'email': self.test_email,
            'token': self.test_token,
            'created_at': self.now,
            'expires_at': self.expires_at,
            'used': True,
            'attempts': 2,
            'used_at': self.now
        }
        
        reset = PasswordResets.from_dict(data)
        
        self.assertEqual(reset.bleoid, self.test_bleoid)
        self.assertEqual(reset.email, self.test_email)
        self.assertEqual(reset.token, self.test_token)
        self.assertEqual(reset.created_at, self.now)
        self.assertEqual(reset.expires_at, self.expires_at)
        self.assertTrue(reset.used)
        self.assertEqual(reset.attempts, 2)
        self.assertEqual(reset.used_at, self.now)
        
        print("  🔹 from_dict method creates PasswordResets object with correct values")
    
    def test_from_dict_with_defaults(self):
        """Test from_dict with missing optional fields"""
        data = {
            'bleoid': self.test_bleoid,
            'email': self.test_email,
            'token': self.test_token,
            'created_at': self.now,
            'expires_at': self.expires_at
        }
        
        reset = PasswordResets.from_dict(data)
        
        self.assertFalse(reset.used)
        self.assertEqual(reset.attempts, 0)
        self.assertIsNone(reset.used_at)
        
        print("  🔹 from_dict method sets default values for missing optional fields")
    
    def test_is_expired_false(self):
        """Test is_expired returns False for valid token"""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=future_time
        )
        
        self.assertFalse(reset.is_expired())
        
        print(f"  🔹 Token expires in future: {future_time}, is_expired returns False")
    
    def test_is_expired_true(self):
        """Test is_expired returns True for expired token"""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=past_time
        )
        
        self.assertTrue(reset.is_expired())
        
        print(f"  🔹 Token expired in past: {past_time}, is_expired returns True")
    
    def test_is_expired_no_expiry(self):
        """Test is_expired returns True when no expiry is set"""
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=None
        )
        
        self.assertTrue(reset.is_expired())
        
        print("  🔹 Token with no expiry date is considered expired")
    
    def test_is_expired_naive_datetime(self):
        """Test is_expired handles naive datetime correctly"""
        # Create naive datetime (no timezone)
        naive_future = datetime.now() + timedelta(hours=1)
        
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=naive_future
        )
        
        # Should not raise error and should handle timezone conversion
        result = reset.is_expired()
        self.assertIsInstance(result, bool)
        
        print("  🔹 is_expired handles naive datetime without errors")
    
    def test_is_valid_true(self):
        """Test is_valid returns True for valid, unused token"""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=future_time,
            used=False
        )
        
        self.assertTrue(reset.is_valid())
        
        print("  🔹 Valid unused token returns is_valid = True")
    
    def test_is_valid_false_used(self):
        """Test is_valid returns False for used token"""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=future_time,
            used=True
        )
        
        self.assertFalse(reset.is_valid())
        
        print("  🔹 Used token returns is_valid = False even if not expired")
    
    def test_is_valid_false_expired(self):
        """Test is_valid returns False for expired token"""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=past_time,
            used=False
        )
        
        self.assertFalse(reset.is_valid())
        
        print("  🔹 Expired token returns is_valid = False even if unused")
    
    def test_mark_as_used(self):
        """Test marking token as used"""
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=self.expires_at
        )
        
        # Initially not used
        self.assertFalse(reset.used)
        self.assertIsNone(reset.used_at)
        
        # Mark as used
        reset.mark_as_used()
        
        # Should be marked as used with timestamp
        self.assertTrue(reset.used)
        self.assertIsInstance(reset.used_at, datetime)
        self.assertIsNotNone(reset.used_at.tzinfo)
        
        print(f"  🔹 Token marked as used at: {reset.used_at}")
    
    def test_increment_attempts(self):
        """Test incrementing attempts counter"""
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=self.expires_at
        )
        
        # Initially 0 attempts
        self.assertEqual(reset.attempts, 0)
        
        # Increment attempts
        reset.increment_attempts()
        self.assertEqual(reset.attempts, 1)
        
        reset.increment_attempts()
        self.assertEqual(reset.attempts, 2)
        
        print(f"  🔹 Attempts counter incremented correctly: 0 → 1 → 2")
    
    def test_str_representation(self):
        """Test string representation"""
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=self.expires_at
        )
        
        result = str(reset)
        expected = f"PasswordReset(bleoid={self.test_bleoid}, email={self.test_email}, status=valid)"
        self.assertEqual(result, expected)
        
        print(f"  🔹 String representation: {result}")
    
    def test_str_representation_used(self):
        """Test string representation for used token"""
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=self.expires_at,
            used=True
        )
        
        result = str(reset)
        expected = f"PasswordReset(bleoid={self.test_bleoid}, email={self.test_email}, status=used)"
        self.assertEqual(result, expected)
        
        print(f"  🔹 Used token string representation: {result}")
    
    def test_str_representation_expired(self):
        """Test string representation for expired token"""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            expires_at=past_time
        )
        
        result = str(reset)
        expected = f"PasswordReset(bleoid={self.test_bleoid}, email={self.test_email}, status=expired)"
        self.assertEqual(result, expected)
        
        print(f"  🔹 Expired token string representation: {result}")
    
    def test_repr_representation(self):
        """Test detailed representation"""
        reset = PasswordResets(
            bleoid=self.test_bleoid,
            email=self.test_email,
            token=self.test_token,
            created_at=self.now,
            expires_at=self.expires_at,
            attempts=2
        )
        
        result = repr(reset)
        expected = f"PasswordResets(bleoid='{self.test_bleoid}', email='{self.test_email}', token='{self.test_token[:20]}...', created_at='{self.now}', expires_at='{self.expires_at}', used=False, attempts=2)"
        self.assertEqual(result, expected)
        
        print("  🔹 Detailed representation includes all fields with truncated token")

if __name__ == '__main__':
    run_test_with_output(TestPasswordResetsModel)