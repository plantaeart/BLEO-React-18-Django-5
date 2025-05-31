from tests.base_test import BLEOBaseTest, run_test_with_output
from models.MessageInfos import MessageInfos
from models.enums.MessageType import MessageType
from datetime import datetime
import time

class MessageInfosModelTest(BLEOBaseTest):
    """Test cases for MessageInfos model"""
    
    def test_initialization_with_required_fields(self):
        """Test MessageInfos initialization with required fields"""
        message = MessageInfos(
            id=1,
            title="Test Title",
            text="Test message content",
            type=MessageType.THOUGHTS.value  # Use enum value
        )
        
        # Check required fields
        self.assertEqual(message.id, 1)
        self.assertEqual(message.title, "Test Title")
        self.assertEqual(message.text, "Test message content")
        self.assertEqual(message.type, MessageType.THOUGHTS.value)  # Compare with enum value
        
        # Check default value for created_at
        self.assertIsNotNone(message.created_at)
        
        print(f"  🔹 Message initialized with ID: {message.id}, Title: {message.title}")
        print(f"  🔹 Default created_at set to: {message.created_at}")
    
    def test_initialization_with_all_fields(self):
        """Test MessageInfos initialization with all fields"""
        created_at = datetime(2023, 5, 15, 10, 30, 0)
        
        message = MessageInfos(
            id=2,
            title="Complete Title",
            text="Complete message content",
            type=MessageType.SOUVENIR.value,
            created_at=created_at
        )
        
        # Check all fields
        self.assertEqual(message.id, 2)
        self.assertEqual(message.title, "Complete Title")
        self.assertEqual(message.text, "Complete message content")
        self.assertEqual(message.type, MessageType.SOUVENIR.value)
        self.assertEqual(message.created_at, created_at)
        
        print(f"  🔹 Message initialized with custom created_at: {message.created_at}")
    
    def test_created_at_default_sets_current_time(self):
        """Test that created_at defaults to current time when not provided"""
        before_creation = datetime.now()
        time.sleep(0.001)  # Small delay to ensure time difference
        
        message = MessageInfos(
            id=3,
            title="Timestamp Test",
            text="Testing timestamp",
            type=MessageType.THOUGHTS.value
        )
        
        time.sleep(0.001)
        after_creation = datetime.now()
        
        # Check timestamp is between before and after
        self.assertGreaterEqual(message.created_at, before_creation)
        self.assertLessEqual(message.created_at, after_creation)
        
        print(f"  🔹 Default created_at timestamp is current time: {message.created_at}")
    
    def test_to_dict_method(self):
        """Test MessageInfos to_dict method returns all fields"""
        created_at = datetime(2023, 5, 15, 10, 30, 0)
        
        message = MessageInfos(
            id=4,
            title="Dict Test",
            text="Testing to_dict",
            type=MessageType.SOUVENIR.value,
            created_at=created_at
        )
        
        message_dict = message.to_dict()
        
        # Check all fields are in the dict
        self.assertEqual(message_dict["id"], 4)
        self.assertEqual(message_dict["title"], "Dict Test")
        self.assertEqual(message_dict["text"], "Testing to_dict")
        self.assertEqual(message_dict["type"], MessageType.SOUVENIR.value)
        self.assertEqual(message_dict["created_at"], created_at)
        
        print("  🔹 to_dict method returns complete dictionary with all fields")
    
    def test_from_dict_method(self):
        """Test MessageInfos from_dict method creates correct object"""
        created_at = datetime(2023, 5, 15, 10, 30, 0)
        input_dict = {
            "id": 5,
            "title": "FromDict Test",
            "text": "Testing from_dict",
            "type": MessageType.NOTES.value,
            "created_at": created_at
        }
        
        message = MessageInfos.from_dict(input_dict)
        
        # Check all fields were set correctly
        self.assertEqual(message.id, 5)
        self.assertEqual(message.title, "FromDict Test")
        self.assertEqual(message.text, "Testing from_dict")
        self.assertEqual(message.type, MessageType.NOTES.value)
        self.assertEqual(message.created_at, created_at)
        
        print("  🔹 from_dict method creates MessageInfos object with correct values")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(MessageInfosModelTest)