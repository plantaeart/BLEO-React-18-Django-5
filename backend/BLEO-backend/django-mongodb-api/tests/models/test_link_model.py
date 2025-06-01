from tests.base_test import BLEOBaseTest, run_test_with_output
from models.Link import Link, ConnectionStatusType
from datetime import datetime
import time

class LinkModelTest(BLEOBaseTest):
    """Test cases for Link model"""
    
    def test_initialization_with_required_fields(self):
        """Test Link initialization with only required fields"""
        link = Link(BLEOIdPartner1="ABC123")
        
        # Check required field
        self.assertEqual(link.BLEOIdPartner1, "ABC123")
        
        # Check default values
        self.assertIsNone(link.BLEOIdPartner2)
        self.assertEqual(link.status, ConnectionStatusType.PENDING.value)
        self.assertIsNotNone(link.created_at)
        self.assertIsNotNone(link.updated_at)
        
        print("  🔹 Link initialized with default values for optional fields")
    
    def test_initialization_with_all_fields(self):
        """Test Link initialization with all fields provided"""
        created_at = datetime(2023, 5, 15)
        updated_at = datetime(2023, 5, 16)
        
        link = Link(
            BLEOIdPartner1="DEF456",
            BLEOIdPartner2="GHI789",
            status=ConnectionStatusType.ACCEPTED.value,
            created_at=created_at,
            updated_at=updated_at
        )
        
        # Check all fields were set correctly
        self.assertEqual(link.BLEOIdPartner1, "DEF456")
        self.assertEqual(link.BLEOIdPartner2, "GHI789")
        self.assertEqual(link.status, ConnectionStatusType.ACCEPTED.value)
        self.assertEqual(link.created_at, created_at)
        self.assertEqual(link.updated_at, updated_at)
        
        print("  🔹 Link initialized with all custom values")
    
    def test_timestamps_default_to_current_time(self):
        """Test that timestamps default to current time when not provided"""
        before_creation = datetime.now()
        time.sleep(0.001)  # Small delay to ensure time difference
        
        link = Link(BLEOIdPartner1="JKL012")
        
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
            BLEOIdPartner1="MNO345",
            BLEOIdPartner2="PQR678",
            status=ConnectionStatusType.REJECTED.value,
            created_at=created_at,
            updated_at=updated_at
        )
        
        link_dict = link.to_dict()
        
        # Check all fields are in the dict
        self.assertEqual(link_dict["BLEOIdPartner1"], "MNO345")
        self.assertEqual(link_dict["BLEOIdPartner2"], "PQR678")
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


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(LinkModelTest)