from datetime import datetime
from rest_framework.exceptions import ValidationError
from api.serializers import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetResponseSerializer
)
from tests.base_test import BLEOBaseTest, run_test_with_output

class TestPasswordResetRequestSerializer(BLEOBaseTest):
    """Test cases for PasswordResetRequestSerializer"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        self.valid_data = {
            'email': 'test@example.com'
        }
    
    def test_valid_email(self):
        """Test serializer with valid email"""
        serializer = PasswordResetRequestSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['email'], 'test@example.com')
        
        print(f"  🔹 Valid email accepted: {validated_data['email']}")
    
    def test_email_normalization(self):
        """Test email is normalized to lowercase and trimmed"""
        data = {'email': '  TEST@EXAMPLE.COM  '}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['email'], 'test@example.com')
        
        print(f"  🔹 Email normalized: '  TEST@EXAMPLE.COM  ' → '{validated_data['email']}'")
    
    def test_missing_email(self):
        """Test serializer with missing email"""
        serializer = PasswordResetRequestSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        print("  🔹 Missing email correctly rejected")
    
    def test_empty_email(self):
        """Test serializer with empty email"""
        data = {'email': ''}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        print("  🔹 Empty email correctly rejected")
    
    def test_invalid_email_format(self):
        """Test serializer with invalid email format"""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'test@',
            'test..test@example.com',
            'test@example',
            'test @example.com'
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                data = {'email': email}
                serializer = PasswordResetRequestSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('email', serializer.errors)
                print(f"    ✓ Correctly rejected invalid email: '{email}'")
        
        print("  🔹 Invalid email formats correctly rejected")
    
    def test_email_max_length(self):
        """Test email maximum length validation"""
        long_email = 'a' * 250 + '@example.com'  # Over 254 chars
        data = {'email': long_email}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        print(f"  🔹 Email too long ({len(long_email)} chars) correctly rejected")


class TestPasswordResetConfirmSerializer(BLEOBaseTest):
    """Test cases for PasswordResetConfirmSerializer"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        self.valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        self.valid_data = {
            'token': self.valid_token,
            'password': 'newSecurePassword123'
        }
    
    def test_valid_data(self):
        """Test serializer with valid data"""
        serializer = PasswordResetConfirmSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['token'], self.valid_token)
        self.assertEqual(validated_data['password'], 'newSecurePassword123')
        
        print(f"  🔹 Valid token and password accepted")
        print(f"  🔹 Token length: {len(validated_data['token'])} chars")
        print(f"  🔹 Password length: {len(validated_data['password'])} chars")
    
    def test_missing_token(self):
        """Test serializer with missing token"""
        data = {'password': 'newSecurePassword123'}
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)
        
        print("  🔹 Missing token correctly rejected")
    
    def test_empty_token(self):
        """Test serializer with empty token"""
        data = {
            'token': '',
            'password': 'newSecurePassword123'
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)
        
        print("  🔹 Empty token correctly rejected")
    
    def test_invalid_token_format(self):
        """Test serializer with invalid JWT token format"""
        invalid_tokens = [
            'invalid-token',
            'header.payload',  # Missing signature
            'header.payload.signature.extra',  # Too many parts
            '...',  # Empty parts
        ]
        
        for token in invalid_tokens:
            with self.subTest(token=token):
                data = {
                    'token': token,
                    'password': 'newSecurePassword123'
                }
                serializer = PasswordResetConfirmSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('token', serializer.errors)
                print(f"    ✓ Correctly rejected invalid token format: '{token}'")
        
        print("  🔹 Invalid JWT token formats correctly rejected")
    
    def test_missing_password(self):
        """Test serializer with missing password"""
        data = {'token': self.valid_token}
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        
        print("  🔹 Missing password correctly rejected")
    
    def test_password_too_short(self):
        """Test serializer with password too short"""
        data = {
            'token': self.valid_token,
            'password': '1234567'  # 7 chars, minimum is 8
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        
        print(f"  🔹 Password too short (7 chars) correctly rejected")
    
    def test_password_minimum_length(self):
        """Test serializer with minimum valid password length"""
        data = {
            'token': self.valid_token,
            'password': '12345678'  # Exactly 8 chars
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        print(f"  🔹 Password with minimum length (8 chars) accepted")


class TestPasswordResetResponseSerializer(BLEOBaseTest):
    """Test cases for PasswordResetResponseSerializer"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        self.valid_data = {
            'password_reset': True,
            'reset_at': '2025-06-06T10:30:00Z',
            'message': 'Password reset successfully!'
        }
    
    def test_valid_data(self):
        """Test serializer with valid data"""
        serializer = PasswordResetResponseSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertTrue(validated_data['password_reset'])
        self.assertEqual(validated_data['reset_at'], '2025-06-06T10:30:00Z')
        self.assertEqual(validated_data['message'], 'Password reset successfully!')
        
        print(f"  🔹 Valid response data accepted")
        print(f"  🔹 Password reset: {validated_data['password_reset']}")
        print(f"  🔹 Reset at: {validated_data['reset_at']}")
        print(f"  🔹 Message: {validated_data['message']}")
    
    def test_missing_password_reset(self):
        """Test serializer with missing password_reset field"""
        data = {
            'reset_at': '2025-06-06T10:30:00Z',
            'message': 'Password reset successfully!'
        }
        serializer = PasswordResetResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_reset', serializer.errors)
        
        print("  🔹 Missing password_reset field correctly rejected")
    
    def test_missing_message(self):
        """Test serializer with missing message field"""
        data = {
            'password_reset': True,
            'reset_at': '2025-06-06T10:30:00Z'
        }
        serializer = PasswordResetResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('message', serializer.errors)
        
        print("  🔹 Missing message field correctly rejected")
    
    def test_optional_reset_at(self):
        """Test serializer with optional reset_at field"""
        data = {
            'password_reset': True,
            'message': 'Password reset successfully!'
        }
        serializer = PasswordResetResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertTrue(validated_data['password_reset'])
        self.assertIsNone(validated_data.get('reset_at'))
        self.assertEqual(validated_data['message'], 'Password reset successfully!')
        
        print("  🔹 Optional reset_at field works correctly when omitted")
    
    def test_valid_reset_at_formats(self):
        """Test serializer with various valid reset_at formats"""
        valid_dates = [
            '2025-06-06T10:30:00Z',
            '2025-06-06T10:30:00+00:00',
            '2025-06-06T10:30:00.123456Z',
            '2025-12-31T23:59:59Z',
        ]
        
        for valid_date in valid_dates:
            with self.subTest(date=valid_date):
                data = {
                    'password_reset': True,
                    'reset_at': valid_date,
                    'message': 'Password reset successfully!'
                }
                serializer = PasswordResetResponseSerializer(data=data)
                self.assertTrue(serializer.is_valid())
                print(f"    ✓ Valid date format accepted: '{valid_date}'")
        
        print("  🔹 Various valid datetime formats correctly accepted")

if __name__ == '__main__':
    run_test_with_output(TestPasswordResetRequestSerializer)
    run_test_with_output(TestPasswordResetConfirmSerializer)
    run_test_with_output(TestPasswordResetResponseSerializer)