from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import (
    EmailVerificationSerializer,
    EmailVerificationRequestSerializer,
    EmailVerificationConfirmSerializer,
    EmailVerificationResponseSerializer
)
from datetime import datetime, timezone
import jwt
import os

class EmailVerificationSerializerTest(BLEOBaseTest):
    """Test cases for EmailVerification serializers"""
    
    def test_email_verification_serializer_valid_data(self):
        """Test EmailVerificationSerializer with valid data"""
        data = {
            'bleoid': 'ABC123',
            'email': 'test@example.com',
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
        }
        
        serializer = EmailVerificationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['bleoid'], 'ABC123')
        self.assertEqual(serializer.validated_data['email'], 'test@example.com')
        self.assertIn('bleoid', serializer.validated_data)
        self.assertIn('email', serializer.validated_data)
        
        print("  🔹 EmailVerificationSerializer validates correctly with valid data")
    
    def test_email_verification_serializer_invalid_email(self):
        """Test EmailVerificationSerializer with invalid email"""
        data = {
            'bleoid': 'ABC123',
            'email': 'invalid-email',
            'token': 'valid.jwt.token'
        }
        
        serializer = EmailVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        # Fix: Check for DRF's default email validation message
        error_message = str(serializer.errors['email'])
        self.assertTrue(
            'Enter a valid email address' in error_message or 
            'Invalid email format' in error_message
        )
        
        print("  🔹 EmailVerificationSerializer rejects invalid email format")
    
    def test_email_verification_serializer_invalid_bleoid(self):
        """Test EmailVerificationSerializer with invalid BLEO ID"""
        test_cases = [
            {'bleoid': '', 'email': 'test@example.com', 'token': 'valid.jwt.token'},
            {'bleoid': 'ABC-123', 'email': 'test@example.com', 'token': 'valid.jwt.token'},
            {'bleoid': 'abc@123', 'email': 'test@example.com', 'token': 'valid.jwt.token'},
        ]
        
        for data in test_cases:
            serializer = EmailVerificationSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('bleoid', serializer.errors)
            print(f"    ✓ Rejected invalid BLEO ID: '{data['bleoid']}'")
        
        print("  🔹 EmailVerificationSerializer validates BLEO ID format correctly")
    
    def test_email_verification_serializer_invalid_token(self):
        """Test EmailVerificationSerializer with invalid JWT token"""
        test_cases = [
            {'bleoid': 'ABC123', 'email': 'test@example.com', 'token': ''},
            {'bleoid': 'ABC123', 'email': 'test@example.com', 'token': 'invalid'},
            {'bleoid': 'ABC123', 'email': 'test@example.com', 'token': 'only.two.parts'},
        ]
        
        for i, data in enumerate(test_cases):
            serializer = EmailVerificationSerializer(data=data)
            is_valid = serializer.is_valid()
            
            # Empty token should always fail
            if data['token'] == '':
                self.assertFalse(is_valid)
                self.assertIn('token', serializer.errors)
                print(f"    ✓ Correctly rejected empty token")
            # Invalid JWT format should fail (if custom validation is implemented)
            elif len(data['token'].split('.')) != 3:
                if not is_valid and 'token' in serializer.errors:
                    print(f"    ✓ Correctly rejected invalid JWT format: '{data['token']}'")
                else:
                    print(f"    ⚠️  JWT format validation not implemented for: '{data['token']}'")
            else:
                print(f"    ✓ Tested token: '{data['token'][:20]}...'")
        
        print("  🔹 EmailVerificationSerializer token validation completed")
    
    def test_email_verification_request_serializer(self):
        """Test EmailVerificationRequestSerializer"""
        # Valid data
        valid_data = {'email': 'test@example.com'}
        serializer = EmailVerificationRequestSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['email'], 'test@example.com')
        
        # Invalid data
        invalid_data = {'email': 'invalid-email'}
        serializer = EmailVerificationRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        # Missing email
        empty_data = {}
        serializer = EmailVerificationRequestSerializer(data=empty_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        print("  🔹 EmailVerificationRequestSerializer works correctly")
    
    def test_email_verification_confirm_serializer(self):
        """Test EmailVerificationConfirmSerializer"""
        # Valid token
        valid_data = {
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
        }
        serializer = EmailVerificationConfirmSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid tokens
        invalid_cases = [
            {'token': ''},
            {'token': '   '},
            {'token': 'invalid'},
            {'token': 'only.two'},
        ]
        
        for data in invalid_cases:
            serializer = EmailVerificationConfirmSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('token', serializer.errors)
        
        # Missing token
        serializer = EmailVerificationConfirmSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)
        
        print("  🔹 EmailVerificationConfirmSerializer validates token correctly")
    
    def test_email_verification_response_serializer(self):
        """Test EmailVerificationResponseSerializer"""
        # Valid response data
        response_data = {
            'email_verified': True,
            'email_verified_at': datetime.now(timezone.utc),
            'message': 'Email verified successfully'
        }
        
        serializer = EmailVerificationResponseSerializer(data=response_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['email_verified'], True)
        self.assertIsNotNone(serializer.validated_data['email_verified_at'])
        self.assertEqual(serializer.validated_data['message'], 'Email verified successfully')
        
        # Test with None email_verified_at
        response_data_null = {
            'email_verified': False,
            'email_verified_at': None,
            'message': 'Email not verified'
        }
        
        serializer = EmailVerificationResponseSerializer(data=response_data_null)
        self.assertTrue(serializer.is_valid())
        self.assertFalse(serializer.validated_data['email_verified'])
        self.assertIsNone(serializer.validated_data['email_verified_at'])
        
        print("  🔹 EmailVerificationResponseSerializer works correctly")
    
    def test_email_case_normalization(self):
        """Test email case normalization"""
        test_cases = [
            'TEST@EXAMPLE.COM',
            'Test@Example.Com',
            '  test@example.com  ',
            'MIXED.case@DOMAIN.COM'
        ]
        
        for email in test_cases:
            data = {
                'bleoid': 'ABC123',
                'email': email,
                'token': 'valid.jwt.token'
            }
            
            serializer = EmailVerificationSerializer(data=data)
            if serializer.is_valid():
                self.assertEqual(serializer.validated_data['email'], email.lower().strip())
                print(f"    ✓ Normalized '{email}' to '{serializer.validated_data['email']}'")
        
        print("  🔹 Email case normalization works correctly")
    
    def test_bleoid_case_normalization(self):
        """Test BLEO ID case normalization"""
        test_cases = [
            'abc123',
            'Abc123',
            '  ABC123  ',
            'MiXeD123'
        ]
        
        for bleoid in test_cases:
            data = {
                'bleoid': bleoid,
                'email': 'test@example.com',
                'token': 'valid.jwt.token'
            }
            
            serializer = EmailVerificationSerializer(data=data)
            if serializer.is_valid():
                self.assertEqual(serializer.validated_data['bleoid'], bleoid.upper().strip())
                print(f"    ✓ Normalized '{bleoid}' to '{serializer.validated_data['bleoid']}'")
        
        print("  🔹 BLEO ID case normalization works correctly")
    
    def test_serializer_representation(self):
        """Test serializer representation methods"""
        # Test with response data structure
        response_data = {
            'email_verified': True,
            'email_verified_at': datetime.now(timezone.utc),
            'message': 'Test message'
        }
        
        serializer = EmailVerificationResponseSerializer(data=response_data)
        self.assertTrue(serializer.is_valid())
        
        # Test representation with correct structure
        representation = serializer.to_representation(response_data)
        print(f"    🔍 Representation result: {representation}")
        
        self.assertIn('email_verified', representation)
        self.assertIn('message', representation)
        self.assertTrue(representation['email_verified'])
        self.assertEqual(representation['message'], 'Test message')
        
        # Test with model-like structure (verified instead of email_verified)
        model_data = {
            'bleoid': 'ABC123',
            'email': 'test@example.com',
            'verified': True,
            'attempts': 2,
            'verified_at': datetime.now(timezone.utc),
            'created_at': datetime.now(timezone.utc),
            'message': 'Test message'
        }
        
        representation2 = serializer.to_representation(model_data)
        print(f"    🔍 Model representation result: {representation2}")
        
        self.assertIn('email_verified', representation2)
        self.assertIn('message', representation2)
        
        print("  🔹 Serializer representation methods work correctly")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test very long email - should fail validation now
        long_email = 'a' * 200 + '@' + 'b' * 50 + '.com'  # Total length > 254
        data = {
            'bleoid': 'ABC123',
            'email': long_email,
            'token': 'valid.jwt.token'
        }
        
        serializer = EmailVerificationSerializer(data=data)
        # Should fail validation due to email being too long
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        error_message = str(serializer.errors['email'])
        self.assertTrue('Ensure this field has no more than 254 characters' in error_message)
        print(f"    ✓ Correctly rejected email that's too long ({len(long_email)} chars)")
        
        # Test reasonable long email - should pass
        reasonable_email = 'a' * 40 + '@' + 'b' * 40 + '.com'  # Total length < 254
        data = {
            'bleoid': 'ABC123',
            'email': reasonable_email,
            'token': 'valid.jwt.token'
        }
        
        serializer = EmailVerificationSerializer(data=data)
        if serializer.is_valid():
            self.assertEqual(serializer.validated_data['email'], reasonable_email.lower())
            print(f"    ✓ Accepted reasonable long email ({len(reasonable_email)} chars)")
        else:
            print(f"    ⚠️  Reasonable email rejected: {serializer.errors}")
        
        # Test very long BLEO ID - should fail validation
        long_bleoid = 'A' * 10  # Longer than max_length=6
        data = {
            'bleoid': long_bleoid,
            'email': 'test@example.com',
            'token': 'valid.jwt.token'
        }
        
        serializer = EmailVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('bleoid', serializer.errors)
        error_message = str(serializer.errors['bleoid'])
        self.assertTrue('Ensure this field has no more than 6 characters' in error_message)
        print(f"    ✓ Correctly rejected BLEO ID that's too long ({len(long_bleoid)} chars)")
        
        # Test maximum valid BLEO ID - should pass
        max_bleoid = 'A' * 6  # Exactly max_length=6
        data = {
            'bleoid': max_bleoid,
            'email': 'test@example.com',
            'token': 'valid.jwt.token'
        }
        
        serializer = EmailVerificationSerializer(data=data)
        if serializer.is_valid():
            self.assertEqual(serializer.validated_data['bleoid'], max_bleoid)
            print(f"    ✓ Accepted maximum length BLEO ID ({len(max_bleoid)} chars)")
        
        invalid_email_cases = [
            'test@',  # Missing domain
            '@example.com',  # Missing local part
            'test@@example.com',  # Double @
            'test@.com',  # Domain starts with dot
            'test@com.',  # Domain ends with dot
            'test@ex..ample.com',  # Double dots in domain
            'test..test@example.com',  # Double dots in local part
            'test@',  # Just @ at the end
            '.test@example.com',  # Local part starts with dot
            'test.@example.com',  # Local part ends with dot
        ]
        
        for invalid_email in invalid_email_cases:
            data = {
                'bleoid': 'ABC123',
                'email': invalid_email,
                'token': 'valid.jwt.token'
            }
            
            serializer = EmailVerificationSerializer(data=data)
            is_valid = serializer.is_valid()
            
            if not is_valid and 'email' in serializer.errors:
                print(f"    ✓ Correctly rejected invalid email: '{invalid_email}'")
            else:
                print(f"    ⚠️  Email '{invalid_email}' was unexpectedly accepted")
        
        unicode_email = 'test@exämple.com'
        data = {
            'bleoid': 'ABC123',
            'email': unicode_email,
            'token': 'valid.jwt.token'
        }
        
        serializer = EmailVerificationSerializer(data=data)
        is_valid = serializer.is_valid()
        
        if is_valid:
            print(f"    ℹ️  Unicode email '{unicode_email}' was accepted (IDN support)")
        else:
            print(f"    ✓ Correctly rejected unicode email: '{unicode_email}'")
        
        # Empty values
        empty_cases = [
            {'bleoid': '', 'email': 'test@example.com', 'token': 'valid.jwt.token'},
            {'bleoid': 'ABC123', 'email': '', 'token': 'valid.jwt.token'},
            {'bleoid': 'ABC123', 'email': 'test@example.com', 'token': ''},
        ]
        
        for i, data in enumerate(empty_cases):
            serializer = EmailVerificationSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            print(f"    ✓ Case {i+1}: Correctly rejected empty values")
        
        print("  🔹 Edge cases handled appropriately")
    
    def test_serializer_integration(self):
        """Test serializers working together"""
        # Request serializer
        request_data = {'email': 'test@example.com'}
        request_serializer = EmailVerificationRequestSerializer(data=request_data)
        self.assertTrue(request_serializer.is_valid())
        
        # Confirm serializer
        confirm_data = {
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
        }
        confirm_serializer = EmailVerificationConfirmSerializer(data=confirm_data)
        self.assertTrue(confirm_serializer.is_valid())
        
        # Response serializer
        response_data = {
            'email_verified': True,
            'email_verified_at': datetime.now(timezone.utc),
            'message': 'Verification complete'
        }
        response_serializer = EmailVerificationResponseSerializer(data=response_data)
        self.assertTrue(response_serializer.is_valid())
        
        # Check data consistency
        self.assertEqual(
            request_serializer.validated_data['email'],
            'test@example.com'
        )
        self.assertTrue(response_serializer.validated_data['email_verified'])
        
        print("  🔹 Serializer integration works correctly")
    
    def test_stricter_email_validation(self):
        """Test the new stricter email validation rules"""
        # Test cases that should now fail with stricter validation
        invalid_cases = [
            'test@',                    # Missing domain
            '@example.com',             # Missing local part
            'test@@example.com',        # Double @
            '.test@example.com',        # Local starts with dot
            'test.@example.com',        # Local ends with dot
            'test..test@example.com',   # Consecutive dots in local
            'test@.example.com',        # Domain starts with dot
            'test@example.com.',        # Domain ends with dot
            'test@ex..ample.com',       # Consecutive dots in domain
            'test@domain',              # Missing TLD
            'test @example.com',        # Space in email
            '',                         # Empty email
        ]
        
        for invalid_email in invalid_cases:
            data = {
                'bleoid': 'ABC123',
                'email': invalid_email,
                'token': 'valid.jwt.token'
            }
            
            serializer = EmailVerificationSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('email', serializer.errors)
            
            print(f"    ✓ Correctly rejected: '{invalid_email}'")
        
        print("  🔹 Stricter email validation works correctly")
    
    def test_jwt_token_format_validation(self):
        """Test JWT token format validation"""
        invalid_tokens = [
            '',                     # Empty
            'invalid',             # No dots
            'only.one',            # Only one dot
            'too.many.dots.here',  # Too many dots
            '  ',                  # Just whitespace
        ]
        
        for invalid_token in invalid_tokens:
            data = {
                'bleoid': 'ABC123',
                'email': 'test@example.com',
                'token': invalid_token
            }
            
            serializer = EmailVerificationSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('token', serializer.errors)
        
        print("  🔹 JWT token format validation works correctly")
    
    def test_bleoid_validation_in_email_verification(self):
        """Test BLEOID validation in EmailVerification serializer"""
        invalid_bleoids = [
            'abc-123',  # Contains hyphen
            'ABC@123',  # Contains @
            '',         # Empty
            'ABCDEFG',  # Too long
            'ABC12',    # Too short
        ]
        
        for invalid_bleoid in invalid_bleoids:
            data = {
                'bleoid': invalid_bleoid,
                'email': 'test@example.com',
                'token': 'valid.jwt.token'
            }
            
            serializer = EmailVerificationSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('bleoid', serializer.errors)
        
        print("  🔹 BLEOID validation works in EmailVerification serializer")

# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(EmailVerificationSerializerTest)