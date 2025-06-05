from tests.base_test import BLEOBaseTest, run_test_with_output
from models.Link import Link, ConnectionStatusType
from datetime import datetime
import time
import re

class LinkModelTest(BLEOBaseTest):
    """Test cases for Link model"""
    
    def test_initialization_with_required_fields(self):
        """Test Link initialization with only required fields"""
        # Fix: Now both partners are required
        link = Link(
            bleoidPartner1="ABC123",
            bleoidPartner2="DEF456"
        )
        
        # Check required fields
        self.assertEqual(link.bleoidPartner1, "ABC123")
        self.assertEqual(link.bleoidPartner2, "DEF456")
        
        # Check default values
        self.assertEqual(link.status, ConnectionStatusType.PENDING.value)
        self.assertIsNotNone(link.created_at)
        self.assertIsNotNone(link.updated_at)
        
        print("  🔹 Link initialized with both required partner fields")
    
    def test_initialization_with_all_fields(self):
        """Test Link initialization with all fields provided"""
        created_at = datetime(2023, 5, 15)
        updated_at = datetime(2023, 5, 16)
        
        link = Link(
            bleoidPartner1="DEF456",
            bleoidPartner2="GHI789",
            status=ConnectionStatusType.ACCEPTED.value,
            created_at=created_at,
            updated_at=updated_at
        )
        
        # Check all fields were set correctly
        self.assertEqual(link.bleoidPartner1, "DEF456")
        self.assertEqual(link.bleoidPartner2, "GHI789")
        self.assertEqual(link.status, ConnectionStatusType.ACCEPTED.value)
        self.assertEqual(link.created_at, created_at)
        self.assertEqual(link.updated_at, updated_at)
        
        print("  🔹 Link initialized with all custom values")
    
    def test_timestamps_default_to_current_time(self):
        """Test that timestamps default to current time when not provided"""
        before_creation = datetime.now()
        time.sleep(0.001)  # Small delay to ensure time difference
        
        link = Link(
            bleoidPartner1="JKL012",
            bleoidPartner2="MNO345"
        )
        
        time.sleep(0.001)
        after_creation = datetime.now()
        
        # Check timestamps are between before and after
        self.assertGreaterEqual(link.created_at, before_creation)
        self.assertLessEqual(link.created_at, after_creation)
        self.assertGreaterEqual(link.updated_at, before_creation)
        self.assertLessEqual(link.updated_at, after_creation)
        
        print(f"  🔹 Default timestamps are current time: created_at={link.created_at}, updated_at={link.updated_at}")
    
    def test_to_dict_method(self):
        """Test Link to_dict method returns all fields"""
        created_at = datetime(2023, 5, 15)
        updated_at = datetime(2023, 5, 16)
        
        link = Link(
            bleoidPartner1="MNO345",
            bleoidPartner2="PQR678",
            status=ConnectionStatusType.REJECTED.value,
            created_at=created_at,
            updated_at=updated_at
        )
        
        link_dict = link.to_dict()
        
        # Check all fields are in the dict
        self.assertEqual(link_dict["bleoidPartner1"], "MNO345")
        self.assertEqual(link_dict["bleoidPartner2"], "PQR678")
        self.assertEqual(link_dict["status"], ConnectionStatusType.REJECTED.value)
        self.assertEqual(link_dict["created_at"], created_at)
        self.assertEqual(link_dict["updated_at"], updated_at)
        
        print("  🔹 to_dict method returns complete dictionary with all fields")
    
    def test_connection_status_enum_values(self):
        """Test ConnectionStatusType enum has correct values"""
        self.assertEqual(ConnectionStatusType.PENDING.value, "pending")
        self.assertEqual(ConnectionStatusType.ACCEPTED.value, "accepted")
        self.assertEqual(ConnectionStatusType.REJECTED.value, "rejected")
        self.assertEqual(ConnectionStatusType.BLOCKED.value, "blocked")
        
        print("  🔹 ConnectionStatusType enum has expected values")
    
    def test_null_partner2_validation(self):
        """Test that null bleoidPartner2 raises ValueError"""
        with self.assertRaises(ValueError) as context:
            Link(
                bleoidPartner1="ABC123",
                bleoidPartner2=None  # Should raise error
            )
        
        self.assertIn("bleoidPartner2 cannot be null", str(context.exception))
        print("  🔹 Link correctly rejects null bleoidPartner2")
    
    def test_empty_partner_validation(self):
        """Test that empty partner IDs raise ValueError"""
        test_cases = [
            {"bleoidPartner1": "", "bleoidPartner2": "DEF456"},
            {"bleoidPartner1": "ABC123", "bleoidPartner2": ""},
            {"bleoidPartner1": "   ", "bleoidPartner2": "DEF456"},
            {"bleoidPartner1": "ABC123", "bleoidPartner2": "   "},
        ]
        
        for case in test_cases:
            with self.assertRaises(ValueError) as context:
                Link(**case)
        
        print("  🔹 Link correctly rejects empty partner IDs")
    
    def test_bleoid_format_validation(self):
        """Test BLEOID format validation"""
        # Test valid BLEOIDs that should work
        valid_bleoids = [
            "ABC123",
            "XYZ789", 
            "A1B2C3",
            "123456",
            "ABCDEF"
        ]
        
        for valid_bleoid in valid_bleoids:
            link = Link(
                bleoidPartner1=valid_bleoid,
                bleoidPartner2="DEF456"
            )
            # Should be exactly as provided (already uppercase)
            self.assertEqual(link.bleoidPartner1, valid_bleoid)
            print(f"    ✓ Accepted valid BLEOID: {valid_bleoid}")
        
        # Test BLEOIDs that should be normalized (lowercase to uppercase)
        normalization_cases = [
            ("abc123", "ABC123"),
            ("xyz789", "XYZ789"),
            ("a1b2c3", "A1B2C3"),
            ("  abc123  ", "ABC123"),  # With whitespace
        ]
        
        for input_bleoid, expected_bleoid in normalization_cases:
            link = Link(
                bleoidPartner1=input_bleoid,
                bleoidPartner2="DEF456"
            )
            self.assertEqual(link.bleoidPartner1, expected_bleoid)
            print(f"    ✓ Normalized '{input_bleoid}' → '{expected_bleoid}'")
        
        # Test invalid BLEOIDs that should be rejected
        invalid_bleoids = [
            "abc-123",  # Contains hyphen
            "ABC@123",  # Contains special char
            "ABCDEFG",  # Too long (7 chars)
            "ABC12",    # Too short (5 chars)
            "",         # Empty
            "   ",      # Only whitespace
            "ABC 123",  # Contains space
            "ABC.123",  # Contains dot
        ]
        
        for invalid_bleoid in invalid_bleoids:
            with self.assertRaises(ValueError) as context:
                Link(
                    bleoidPartner1=invalid_bleoid,
                    bleoidPartner2="ABC123"
                )
            
            error_message = str(context.exception)
            self.assertIn("bleoidPartner1", error_message)
            print(f"    ✓ Correctly rejected invalid BLEOID: '{invalid_bleoid}' - {error_message}")
        
        # Test validation for both partners
        with self.assertRaises(ValueError) as context:
            Link(
                bleoidPartner1="ABC123",
                bleoidPartner2="invalid-format"
            )
        print(f"    ✓ Correctly validated bleoidPartner2 format")
        
        print("  🔹 BLEOID format validation and normalization works correctly")
    
    def test_bleoid_normalization_edge_cases(self):
        """Test BLEOID normalization edge cases"""
        edge_cases = [
            ("  ABC123  ", "ABC123"),      # Leading/trailing spaces
            ("abc123", "ABC123"),          # Lowercase
            ("AbC123", "ABC123"),          # Mixed case
            ("  abc123  ", "ABC123"),      # Lowercase with spaces
        ]
        
        for input_bleoid, expected_bleoid in edge_cases:
            link = Link(
                bleoidPartner1=input_bleoid,
                bleoidPartner2="DEF456"
            )
            self.assertEqual(link.bleoidPartner1, expected_bleoid)
            
            # Test both partners
            link2 = Link(
                bleoidPartner1="ABC123",
                bleoidPartner2=input_bleoid
            )
            self.assertEqual(link2.bleoidPartner2, expected_bleoid)
            
            print(f"    ✓ Both partners normalized '{input_bleoid}' → '{expected_bleoid}'")
        
        print("  🔹 BLEOID normalization edge cases handled correctly")
    
    def test_missing_bleoidPartner1_validation(self):
        """Test that missing bleoidPartner1 raises TypeError"""
        with self.assertRaises(TypeError) as context:
            Link(
                # Missing bleoidPartner1
                bleoidPartner2="DEF456"
            )
        
        error_message = str(context.exception)
        self.assertIn("bleoidPartner1", error_message)
        print(f"    ✓ Correctly rejected missing bleoidPartner1: {error_message}")

    def test_missing_bleoidPartner2_validation(self):
        """Test that missing bleoidPartner2 raises TypeError"""
        with self.assertRaises(TypeError) as context:
            Link(
                bleoidPartner1="ABC123"
                # Missing bleoidPartner2
            )
        
        error_message = str(context.exception)
        self.assertIn("bleoidPartner2", error_message)
        print(f"    ✓ Correctly rejected missing bleoidPartner2: {error_message}")

    def test_both_partners_required(self):
        """Test that both partners are required"""
        # This should work - both partners provided
        link = Link(
            bleoidPartner1="ABC123",
            bleoidPartner2="DEF456"
        )
        self.assertEqual(link.bleoidPartner1, "ABC123")
        self.assertEqual(link.bleoidPartner2, "DEF456")
        print("    ✓ Both partners provided - Link created successfully")
        
        with self.assertRaises(TypeError) as context:
            Link()  # No partners - TypeError (missing required args)
        error_message = str(context.exception)
        self.assertIn("missing", error_message.lower())
        print(f"    ✓ No partners provided - Correctly rejected with TypeError: {error_message}")
        
        with self.assertRaises(TypeError) as context:
            Link(bleoidPartner1="ABC123")  # Only partner1 - TypeError (missing partner2)
        error_message = str(context.exception)
        self.assertIn("bleoidPartner2", error_message)
        print(f"    ✓ Only partner1 provided - Correctly rejected with TypeError: {error_message}")
        
        with self.assertRaises(TypeError) as context:
            Link(bleoidPartner2="DEF456")  # Only partner2 - TypeError (missing partner1)
        error_message = str(context.exception)
        self.assertIn("bleoidPartner1", error_message)
        print(f"    ✓ Only partner2 provided - Correctly rejected with TypeError: {error_message}")
        
        print("  🔹 Both partners requirement validation works correctly")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(LinkModelTest)