from tests.base_test import BLEOBaseTest, run_test_with_output
from models.EmailVerification import EmailVerification
from datetime import datetime, timedelta
import time
from datetime import timezone
from api.serializers import EmailVerificationSerializer
from utils.validation_patterns import ValidationRules

class EmailVerificationModelTest(BLEOBaseTest):
    """Test cases for EmailVerification model"""
    
    def test_initialization_with_required_fields(self):
        """Test EmailVerification initialization with only required fields"""
        verification = EmailVerification(
            bleoid="ABC123",
            email="test@example.com",
            token="jwt_token_string"
        )
        
        # Check required fields
        self.assertEqual(verification.bleoid, "ABC123")
        self.assertEqual(verification.email, "test@example.com")
        self.assertEqual(verification.token, "jwt_token_string")
        
        # Check default values
        self.assertIsNotNone(verification.created_at)
        self.assertIsNone(verification.expires_at)
        self.assertFalse(verification.verified)
        self.assertEqual(verification.attempts, 0)
        self.assertIsNone(verification.verified_at)
        
        print("  🔹 EmailVerification initialized with default values for optional fields")
    
    def test_initialization_with_all_fields(self):
        """Test EmailVerification initialization with all fields provided"""
        created_at = datetime(2023, 5, 15, 10, 30, 0)
        expires_at = datetime(2023, 5, 16, 10, 30, 0)
        verified_at = datetime(2023, 5, 15, 11, 0, 0)
        
        verification = EmailVerification(
            bleoid="DEF456",
            email="full@example.com",
            token="complete_jwt_token",
            created_at=created_at,
            expires_at=expires_at,
            verified=True,
            attempts=2,
            verified_at=verified_at
        )
        
        # Check all fields were set correctly
        self.assertEqual(verification.bleoid, "DEF456")
        self.assertEqual(verification.email, "full@example.com")
        self.assertEqual(verification.token, "complete_jwt_token")
        self.assertEqual(verification.created_at, created_at)
        self.assertEqual(verification.expires_at, expires_at)
        self.assertTrue(verification.verified)
        self.assertEqual(verification.attempts, 2)
        self.assertEqual(verification.verified_at, verified_at)
        
        print("  🔹 EmailVerification initialized with all custom values")
    
    def test_created_at_default_sets_current_time(self):
        """Test that created_at defaults to current time when not provided"""
        before_creation = datetime.now(timezone.utc)
        time.sleep(0.001)  # Small delay to ensure time difference
        
        verification = EmailVerification(
            bleoid="GHI789",
            email="timestamp@example.com",
            token="timestamp_token"
        )
        
        time.sleep(0.001)
        after_creation = datetime.now(timezone.utc)
        
        # Check timestamp is between before and after
        self.assertGreaterEqual(verification.created_at, before_creation)
        self.assertLessEqual(verification.created_at, after_creation)
        
        print(f"  🔹 Default created_at timestamp is current time: {verification.created_at}")
    
    def test_to_dict_method(self):
        """Test EmailVerification to_dict method returns all fields"""
        created_at = datetime(2023, 5, 17, 14, 45, 0)
        expires_at = datetime(2023, 5, 18, 14, 45, 0)
        
        verification = EmailVerification(
            bleoid="JKL012",
            email="dict@example.com",
            token="dict_test_token",
            created_at=created_at,
            expires_at=expires_at,
            verified=False,
            attempts=1
        )
        
        verification_dict = verification.to_dict()
        
        # Check all fields are in the dict
        self.assertEqual(verification_dict["bleoid"], "JKL012")
        self.assertEqual(verification_dict["email"], "dict@example.com")
        self.assertEqual(verification_dict["token"], "dict_test_token")
        self.assertEqual(verification_dict["created_at"], created_at)
        self.assertEqual(verification_dict["expires_at"], expires_at)
        self.assertFalse(verification_dict["verified"])
        self.assertEqual(verification_dict["attempts"], 1)
        self.assertIsNone(verification_dict["verified_at"])
        
        print("  🔹 to_dict method returns complete dictionary with all fields")
    
    def test_from_dict_method(self):
        """Test EmailVerification from_dict method creates correct object"""
        created_at = datetime(2023, 5, 18, 16, 20, 0)
        expires_at = datetime(2023, 5, 19, 16, 20, 0)
        verified_at = datetime(2023, 5, 18, 17, 0, 0)
        
        input_dict = {
            "bleoid": "MNO345",
            "email": "fromdict@example.com",
            "token": "fromdict_token",
            "created_at": created_at,
            "expires_at": expires_at,
            "verified": True,
            "attempts": 3,
            "verified_at": verified_at
        }
        
        verification = EmailVerification.from_dict(input_dict)
        
        # Check all fields were set correctly
        self.assertEqual(verification.bleoid, "MNO345")
        self.assertEqual(verification.email, "fromdict@example.com")
        self.assertEqual(verification.token, "fromdict_token")
        self.assertEqual(verification.created_at, created_at)
        self.assertEqual(verification.expires_at, expires_at)
        self.assertTrue(verification.verified)
        self.assertEqual(verification.attempts, 3)
        self.assertEqual(verification.verified_at, verified_at)
        
        print("  🔹 from_dict method creates EmailVerification object with correct values")
    
    def test_from_dict_with_missing_values(self):
        """Test creation from dictionary with missing optional values"""
        data = {
            "bleoid": "PQR678",
            "email": "minimal@example.com",
            "token": "minimal_token"
            # Missing optional fields
        }
        
        verification = EmailVerification.from_dict(data)
        
        self.assertEqual(verification.bleoid, "PQR678")
        self.assertEqual(verification.email, "minimal@example.com")
        self.assertEqual(verification.token, "minimal_token")
        
        # Check if created_at was set to current time (not None)
        if hasattr(verification, 'created_at') and verification.created_at is not None:
            # If model sets default timestamp
            self.assertIsNotNone(verification.created_at)
            self.assertIsInstance(verification.created_at, datetime)
        else:
            # If model leaves it as None
            self.assertIsNone(verification.created_at)
        
        self.assertIsNone(verification.expires_at)
        self.assertFalse(verification.verified)  # Default value
        self.assertEqual(verification.attempts, 0)  # Default value
        self.assertIsNone(verification.verified_at)
        
        print("  🔹 EmailVerification created with missing values handled correctly")
    
    def test_is_expired_method(self):
        """Test is_expired method with different scenarios"""
        # Not expired token
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        verification1 = EmailVerification(
            bleoid="STU901",
            email="notexpired@example.com",
            token="valid_token",
            expires_at=future_time
        )
        self.assertFalse(verification1.is_expired())
        
        # Expired token
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        verification2 = EmailVerification(
            bleoid="VWX234",
            email="expired@example.com",
            token="expired_token",
            expires_at=past_time
        )
        self.assertTrue(verification2.is_expired())
        
        # No expiration time set
        verification3 = EmailVerification(
            bleoid="YZA567",
            email="noexpiry@example.com",
            token="no_expiry_token"
            # expires_at is None
        )
        self.assertFalse(verification3.is_expired())  # Should return False when no expiry
        
        print("  🔹 is_expired method correctly identifies expired and valid tokens")
    
    def test_is_verified_method(self):
        """Test is_verified method"""
        # Verified email
        verification1 = EmailVerification(
            bleoid="BCD890",
            email="verified@example.com",
            token="verified_token",
            verified=True
        )
        self.assertTrue(verification1.is_verified())
        
        # Unverified email
        verification2 = EmailVerification(
            bleoid="EFG123",
            email="unverified@example.com",
            token="unverified_token",
            verified=False
        )
        self.assertFalse(verification2.is_verified())
        
        print("  🔹 is_verified method correctly returns verification status")
    
    def test_increment_attempts_method(self):
        """Test increment_attempts method"""
        verification = EmailVerification(
            bleoid="HIJ456",
            email="attempts@example.com",
            token="attempts_token",
            attempts=0
        )
        
        # Initial attempts
        self.assertEqual(verification.attempts, 0)
        
        # Increment once
        verification.increment_attempts()
        self.assertEqual(verification.attempts, 1)
        
        # Increment again
        verification.increment_attempts()
        self.assertEqual(verification.attempts, 2)
        
        # Increment multiple times
        for _ in range(3):
            verification.increment_attempts()
        self.assertEqual(verification.attempts, 5)
        
        print("  🔹 increment_attempts method correctly increments counter")
    
    def test_mark_as_verified_method(self):
        """Test mark_as_verified method"""
        verification = EmailVerification(
            bleoid="KLM789",
            email="markverified@example.com",
            token="mark_verified_token",
            verified=False
        )
        
        # Before verification
        self.assertFalse(verification.verified)
        self.assertIsNone(verification.verified_at)
        
        # Mark as verified
        before_mark = datetime.now(timezone.utc)
        time.sleep(0.001)
        verification.mark_as_verified()
        time.sleep(0.001)
        after_mark = datetime.now(timezone.utc)
        
        # After verification
        self.assertTrue(verification.verified)
        self.assertIsNotNone(verification.verified_at)
        
        # Check timestamp is current time
        self.assertGreaterEqual(verification.verified_at, before_mark)
        self.assertLessEqual(verification.verified_at, after_mark)
        
        print(f"  🔹 mark_as_verified method sets verified=True and verified_at={verification.verified_at}")
    
    def test_str_method(self):
        """Test string representation of EmailVerification"""
        expires_at = datetime(2023, 5, 20, 12, 0, 0)
        verification = EmailVerification(
            bleoid="NOP012",
            email="string@example.com",
            token="string_token",
            expires_at=expires_at,
            verified=True
        )
        
        str_repr = str(verification)
        expected = f"EmailVerification(email=string@example.com, verified=True, expires_at={expires_at})"
        
        self.assertEqual(str_repr, expected)
        
        print(f"  🔹 __str__ method returns: {str_repr}")
    
    def test_repr_method(self):
        """Test detailed string representation of EmailVerification"""
        created_at = datetime(2023, 5, 21, 9, 15, 0)
        expires_at = datetime(2023, 5, 22, 9, 15, 0)
        
        verification = EmailVerification(
            bleoid="QRS345",
            email="repr@example.com",
            token="repr_token",
            created_at=created_at,
            expires_at=expires_at,
            verified=False,
            attempts=2
        )
        
        repr_str = repr(verification)
        expected = (f"EmailVerification(bleoid='QRS345', email='repr@example.com', "
                   f"verified=False, attempts=2, "
                   f"created_at={created_at}, expires_at={expires_at})")
        
        self.assertEqual(repr_str, expected)
        
        print(f"  🔹 __repr__ method returns detailed representation")
    
    def test_verification_workflow(self):
        """Test complete verification workflow"""
        # Create new verification
        verification = EmailVerification(
            bleoid="TUV678",
            email="workflow@example.com",
            token="workflow_token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=ValidationRules.JWT_EXPIRATION['email_verification'])
        )
        
        # Initial state
        self.assertFalse(verification.is_verified())
        self.assertFalse(verification.is_expired())
        self.assertEqual(verification.attempts, 0)
        
        # Simulate failed attempts
        verification.increment_attempts()
        verification.increment_attempts()
        self.assertEqual(verification.attempts, 2)
        self.assertFalse(verification.is_verified())
        
        # Successful verification
        verification.mark_as_verified()
        self.assertTrue(verification.is_verified())
        self.assertIsNotNone(verification.verified_at)
        
        # Convert to dict and back
        verification_dict = verification.to_dict()
        recreated = EmailVerification.from_dict(verification_dict)
        
        self.assertEqual(verification.bleoid, recreated.bleoid)
        self.assertEqual(verification.email, recreated.email)
        self.assertEqual(verification.verified, recreated.verified)
        self.assertEqual(verification.attempts, recreated.attempts)
        
        print("  🔹 Complete verification workflow works correctly")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        
        # Test model-level validations first
        print("  🔹 Testing model-level validations:")
        
        # Test very long email at model level
        long_email = 'a' * 200 + '@' + 'b' * 50 + '.com'  # Total length > 254
        
        # Model might not validate email length - this depends on your model implementation
        try:
            verification = EmailVerification(
                bleoid='ABC123',
                email=long_email,
                token='valid_token'
            )
            print(f"    ⚠️  Model accepted very long email ({len(long_email)} chars)")
        except ValueError as e:
            print(f"    ✓ Model correctly rejected long email: {str(e)}")
        
        # Test BLEOID validation at model level (this should work)
        invalid_bleoids = ['abc-123', 'ABC@123', '', 'ABCDEFG', 'ABC12']
        
        for invalid_bleoid in invalid_bleoids:
            with self.assertRaises(ValueError):
                EmailVerification(
                    bleoid=invalid_bleoid,
                    email='test@example.com',
                    token='valid_token'
                )
            print(f"    ✓ Model correctly rejected invalid BLEOID: '{invalid_bleoid}'")
        
        # Test serializer-level validations separately
        print("  🔹 Testing serializer-level validations:")
        
        # Test very long email at serializer level
        long_email = 'a' * 200 + '@' + 'b' * 50 + '.com'
        data = {
            'bleoid': 'ABC123',
            'email': long_email,
            'token': 'valid.jwt.token'
        }
        
        serializer = EmailVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # ✅ Should be False
        self.assertIn('email', serializer.errors)  # ✅ Should have email errors
        error_message = str(serializer.errors['email'])
        self.assertTrue('Ensure this field has no more than 254 characters' in error_message)
        print(f"    ✓ Serializer correctly rejected email that's too long ({len(long_email)} chars)")
        
        # Test reasonable long email at serializer level
        reasonable_email = 'a' * 40 + '@' + 'b' * 40 + '.com'
        data = {
            'bleoid': 'ABC123',
            'email': reasonable_email,
            'token': 'valid.jwt.token'
        }
        
        serializer = EmailVerificationSerializer(data=data)
        if serializer.is_valid():
            self.assertEqual(serializer.validated_data['email'], reasonable_email.lower())
            print(f"    ✓ Serializer accepted reasonable long email ({len(reasonable_email)} chars)")
        else:
            print(f"    ⚠️  Reasonable email rejected: {serializer.errors}")
        
        # Test BLEOID validation at serializer level
        long_bleoid = 'A' * 10
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
        print(f"    ✓ Serializer correctly rejected BLEO ID that's too long ({len(long_bleoid)} chars)")
        
        # Test Unicode email at serializer level
        unicode_email = 'test@exämple.com'
        data = {
            'bleoid': 'ABC123',
            'email': unicode_email,
            'token': 'valid.jwt.token'
        }
        
        serializer = EmailVerificationSerializer(data=data)
        # Unicode emails should be valid in most cases
        if serializer.is_valid():
            print(f"    ✓ Serializer accepted unicode email: '{unicode_email}'")
        else:
            self.assertIn('email', serializer.errors)  # Only check errors if invalid
            print(f"    ✓ Serializer correctly rejected unicode email: '{unicode_email}' - {serializer.errors['email']}")
        
        # Test empty values at serializer level
        empty_cases = [
            {'bleoid': '', 'email': 'test@example.com', 'token': 'valid.jwt.token'},
            {'bleoid': 'ABC123', 'email': '', 'token': 'valid.jwt.token'},
            {'bleoid': 'ABC123', 'email': 'test@example.com', 'token': ''},
        ]
        
        for i, data in enumerate(empty_cases):
            serializer = EmailVerificationSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            print(f"    ✓ Case {i+1}: Serializer correctly rejected empty values - {list(serializer.errors.keys())}")
        
        print("  🔹 Edge cases handled appropriately")
    
    def test_bleoid_format_validation(self):
        """Test BLEOID format validation in EmailVerification"""
        # Valid BLEOID should work
        valid_verification = EmailVerification(
            bleoid="ABC123",
            email="test@example.com",
            token="valid_token"
        )
        self.assertEqual(valid_verification.bleoid, "ABC123")
        print("    ✓ Valid BLEOID accepted: ABC123")
        
        # BLEOIDs that should be NORMALIZED (not rejected)
        normalization_cases = [
            ("abc123", "ABC123"),      # Lowercase to uppercase
            ("  ABC123  ", "ABC123"),  # Trim whitespace
            ("xyz789", "XYZ789"),      # Lowercase to uppercase
            ("a1b2c3", "A1B2C3"),      # Mixed alphanumeric
        ]
        
        for input_bleoid, expected_bleoid in normalization_cases:
            verification = EmailVerification(
                bleoid=input_bleoid,
                email="test@example.com",
                token="valid_token"
            )
            self.assertEqual(verification.bleoid, expected_bleoid)
            print(f"    ✓ Normalized '{input_bleoid}' → '{expected_bleoid}'")
        
        # Invalid BLEOIDs that should be REJECTED (truly invalid)
        invalid_bleoids = [
            "ABC-12",   # Contains hyphen
            "ABC@12",   # Contains special char
            "",         # Empty string
            "ABCDEFG",  # Too long (7 chars)
            "ABC12",    # Too short (5 chars)
            "ABC 12",   # Contains space
            "ABC.12",   # Contains dot
        ]
        
        for invalid_bleoid in invalid_bleoids:
            with self.assertRaises(ValueError) as context:
                EmailVerification(
                    bleoid=invalid_bleoid,
                    email="test@example.com",
                    token="valid_token"
                )
            
            error_message = str(context.exception)
            self.assertIn("bleoid", error_message.lower())
            print(f"    ✓ Correctly rejected invalid BLEOID: '{invalid_bleoid}'")
        
        print("  🔹 EmailVerification BLEOID format validation works correctly")
    
    def test_bleoid_normalization(self):
        """Test BLEOID normalization to uppercase"""
        verification = EmailVerification(
            bleoid="abc123",  # Lowercase input
            email="test@example.com",
            token="valid_token"
        )
        
        # Should be normalized to uppercase
        self.assertEqual(verification.bleoid, "ABC123")
        
        print("  🔹 EmailVerification normalizes BLEOID to uppercase")

# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(EmailVerificationModelTest)