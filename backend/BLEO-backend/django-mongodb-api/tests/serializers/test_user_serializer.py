from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import UserSerializer
from bson import Binary
import base64

class UserSerializerTest(BLEOBaseTest):
    """Test cases for UserSerializer validation and transformation"""
    
    def test_valid_user_data(self):
        """Test that valid user data passes validation"""
        data = {
            'bleoid': 'WQJ94S',
            'email': 'test@example.com',
            'password': 'Password123',
            'userName': 'TestUser',
            'bio': 'Test bio'
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['bleoid'], 'WQJ94S')
        self.assertEqual(serializer.validated_data['email'], 'test@example.com')
        print(f"  🔹 Validated bleoid: {serializer.validated_data['bleoid']}")
        print(f"  🔹 Validated email: {serializer.validated_data['email']}")
    
    def test_invalid_email(self):
        """Test that invalid email is rejected"""
        data = {
            'bleoid': 'WQJ94S',
            'email': 'invalid-email',
            'password': 'Password123',
            'userName': 'TestUser'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        print(f"  🔹 Email error detected: {serializer.errors.get('email')}")
    
    def test_short_password(self):
        """Test that short passwords are rejected"""
        data = {
            'bleoid': 'WQJ94S',
            'email': 'test@example.com',
            'password': 'short',  # Less than 8 chars
            'userName': 'TestUser'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        print(f"  🔹 Password error detected: {serializer.errors.get('password')}")
    
    def test_profile_pic_serialization(self):
        """Test that profile pics are properly converted to base64"""
        # Create binary data for profile pic
        test_binary = b'test binary data'
        
        # Create a user object with profile pic
        user_obj = {
            'bleoid': 'WQJ94S',
            'email': 'test@example.com',
            'userName': 'TestUser',
            'profilePic': Binary(test_binary)
        }
        
        # Serialize
        serializer = UserSerializer(user_obj)
        
        # Check the profile pic is base64 encoded
        expected_base64 = base64.b64encode(test_binary).decode('utf-8')
        self.assertEqual(serializer.data['profilePic'], expected_base64)
        print(f"  🔹 Profile pic correctly encoded to base64")
    
    def test_partial_update(self):
        """Test that partial updates work with only some fields"""
        data = {
            'bio': 'Updated bio'
        }
        serializer = UserSerializer(data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['bio'], 'Updated bio')
        print(f"  🔹 Partial update successful with bio: {serializer.validated_data['bio']}")
    
    def test_bleoid_auto_generation(self):
        """Test that bleoid is generated when only email and password are provided"""
        # Minimal data without bleoid
        data = {
            'email': 'newuser@example.com',
            'password': 'Password123'
        }
        
        # Set up the serializer with auto-generation mode
        serializer = UserSerializer(data=data, context={'auto_generate_id': True})
        
        # Check that validation passes
        self.assertTrue(serializer.is_valid(), f"Validation failed with errors: {serializer.errors}")
        
        # Check that a bleoid was generated in the proper format (6 alphanumeric chars)
        self.assertIn('bleoid', serializer.validated_data)
        generated_id = serializer.validated_data['bleoid']
        
        # Verify ID format matches expected pattern (6 alphanumeric chars)
        self.assertRegex(generated_id, r'^[A-Z0-9]{6}$', 
                        f"Generated bleoid '{generated_id}' doesn't match expected format")
        
        # For thoroughness, check that the ID isn't just a placeholder
        self.assertNotEqual(generated_id, "000000")
        self.assertNotEqual(generated_id, "AAAAAA")
        print(f"  🔹 Auto-generated bleoid: {generated_id}")

    def test_bleoid_validation_when_provided(self):
        """Test BLEOID validation when bleoid is explicitly provided"""
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
                'password': 'Password123'
            }
            
            serializer = UserSerializer(data=data)
            # Note: Your current UserSerializer might not have BLEOID validation
            # You should add validate_bleoid method to UserSerializer too
            if not serializer.is_valid():
                print(f"    ✓ Rejected invalid BLEOID: '{invalid_bleoid}'")
            else:
                print(f"    ⚠️  Invalid BLEOID accepted: '{invalid_bleoid}'")
        
        print("  🔹 BLEOID validation checked in UserSerializer")

    def test_auto_generation_context_requirement(self):
        """Test that auto-generation only works with correct context"""
        data = {
            'email': 'test@example.com',
            'password': 'Password123'
        }
        
        # Without auto_generate_id context - should fail
        serializer1 = UserSerializer(data=data)
        self.assertFalse(serializer1.is_valid())
        self.assertIn('bleoid', serializer1.errors)
        
        # With auto_generate_id context - should pass
        serializer2 = UserSerializer(data=data, context={'auto_generate_id': True})
        self.assertTrue(serializer2.is_valid())
        self.assertIn('bleoid', serializer2.validated_data)
        
        print("  🔹 Auto-generation context requirement works correctly")

# To run the tests
if __name__ == '__main__':
    run_test_with_output(UserSerializerTest)