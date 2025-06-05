from tests.base_test import BLEOBaseTest, run_test_with_output
from models.User import User
from datetime import datetime
from bson.binary import Binary
import re

class UserModelTest(BLEOBaseTest):
    """Test cases for User model"""
    
    def test_initialization_with_required_fields(self):
        """Test User initialization with only required fields"""
        user = User(
            bleoid="ABC123",
            email="test@example.com",
            password="password123"
        )
        
        # Check required fields
        self.assertEqual(user.bleoid, "ABC123")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.password, "password123")
        
        # Check default values
        self.assertEqual(user.userName, "NewUser")
        self.assertIsNone(user.profilePic)
        self.assertFalse(user.email_verified)
        self.assertIsNotNone(user.last_login)
        self.assertIsNotNone(user.created_at)
        self.assertIsNone(user.bio)
        self.assertEqual(user.preferences, {})
        
        print("  🔹 User initialized with default values for optional fields")
    
    def test_initialization_with_all_fields(self):
        """Test User initialization with all fields provided"""
        profile_pic = Binary(b"test_image_data")
        last_login = datetime(2023, 5, 15)
        created_at = datetime(2023, 5, 14)
        preferences = {"theme": "dark", "notifications": True}
        
        user = User(
            bleoid="DEF456",
            email="full@example.com",
            password="fullpassword",
            userName="FullUser",
            profilePic=profile_pic,
            email_verified=True,
            last_login=last_login,
            created_at=created_at,
            bio="This is my bio",
            preferences=preferences
        )
        
        # Check all fields were set correctly
        self.assertEqual(user.bleoid, "DEF456")
        self.assertEqual(user.email, "full@example.com")
        self.assertEqual(user.userName, "FullUser")
        self.assertEqual(user.profilePic, profile_pic)
        self.assertTrue(user.email_verified)
        self.assertEqual(user.last_login, last_login)
        self.assertEqual(user.created_at, created_at)
        self.assertEqual(user.bio, "This is my bio")
        self.assertEqual(user.preferences, preferences)
        
        print("  🔹 User initialized with all custom values")
    
    def test_to_dict_method(self):
        """Test User to_dict method returns all fields"""
        user = User(
            bleoid="GHI789",
            email="dict@example.com",
            password="dictpassword",
            userName="DictUser",
            bio="Dictionary bio"
        )
        
        user_dict = user.to_dict()
        
        # Check all fields are in the dict
        self.assertEqual(user_dict["bleoid"], "GHI789")
        self.assertEqual(user_dict["email"], "dict@example.com")
        self.assertEqual(user_dict["password"], "dictpassword")
        self.assertEqual(user_dict["userName"], "DictUser")
        self.assertEqual(user_dict["bio"], "Dictionary bio")
        self.assertIsNone(user_dict["profilePic"])
        
        print("  🔹 to_dict method returns complete dictionary with all fields")
    
    def test_from_dict_method(self):
        """Test User from_dict method creates correct object"""
        input_dict = {
            "bleoid": "JKL012",
            "email": "from_dict@example.com",
            "password": "fromdictpass",
            "userName": "FromDictUser",
            "bio": "Created from dictionary",
            "email_verified": True
        }
        
        user = User.from_dict(input_dict)
        
        # Check all fields were set correctly
        self.assertEqual(user.bleoid, "JKL012")
        self.assertEqual(user.email, "from_dict@example.com")
        self.assertEqual(user.password, "fromdictpass")
        self.assertEqual(user.userName, "FromDictUser")
        self.assertEqual(user.bio, "Created from dictionary")
        self.assertTrue(user.email_verified)
        
        print("  🔹 from_dict method creates User object with correct values")
    
    def test_generate_bleoid_method(self):
        """Test User.generate_bleoid method creates valid ID"""
        bleoid = User.generate_bleoid()
        
        # Check format is correct (6 alphanumeric characters)
        self.assertRegex(bleoid, r'^[A-Z0-9]{6}$')
        
        # Check uniqueness (generate multiple and verify they're different)
        ids = {User.generate_bleoid() for _ in range(10)}
        self.assertEqual(len(ids), 10)  # All should be unique
        
        print(f"  🔹 Generated bleoid: {bleoid} with correct format")
    
    def test_bleoid_format_validation(self):
        """Test BLEOID format validation in User model"""
        # Valid BLEOID should work
        valid_user = User(
            bleoid="ABC123",
            email="test@example.com",
            password="password123"
        )
        self.assertEqual(valid_user.bleoid, "ABC123")
        
        # Invalid BLEOIDs should raise ValueError
        invalid_bleoids = [
            "abc123",    # Lowercase
            "ABC-123",   # Contains hyphen
            "ABC@123",   # Contains special char
            "ABC12",     # Too short
            "ABCDEFG",   # Too long
            "",          # Empty
            None,        # Null
        ]
        
        for invalid_bleoid in invalid_bleoids:
            with self.assertRaises(ValueError) as context:
                User(
                    bleoid=invalid_bleoid,
                    email="test@example.com",
                    password="password123"
                )
            
            self.assertIn("bleoid", str(context.exception).lower())
            print(f"    ✓ Rejected invalid BLEOID: {invalid_bleoid}")
        
        print("  🔹 User BLEOID format validation works correctly")
    
    def test_generate_bleoid_format(self):
        """Test generated BLEOID follows correct format"""
        for _ in range(10):
            bleoid = User.generate_bleoid()
            
            # Check format matches pattern ^[A-Z0-9]{6}$
            self.assertRegex(bleoid, r'^[A-Z0-9]{6}$')
            self.assertEqual(len(bleoid), 6)
        
        print("  🔹 Generated BLEOIDs follow correct format pattern")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(UserModelTest)