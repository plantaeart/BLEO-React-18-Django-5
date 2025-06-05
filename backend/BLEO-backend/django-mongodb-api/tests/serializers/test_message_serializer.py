from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import MessageInfosSerializer, MessagesDaysSerializer
from datetime import datetime
from models.enums.MessageType import MessageType
from models.enums.MoodType import MoodType 
from models.enums.EnergyLevelType import EnergyLevelType
from models.enums.PleasantnessType import PleasantnessType

class MessageInfosSerializerTest(BLEOBaseTest):
    """Test cases for MessageInfosSerializer validation and transformation"""
    
    def test_valid_message_info(self):
        """Test that valid message info passes validation"""
        data = {
            'title': 'Test Message',
            'text': 'This is a test message',
            'type': MessageType.THOUGHTS.value,
            'created_at': datetime.now().isoformat()
        }
        serializer = MessageInfosSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['title'], 'Test Message')
        self.assertEqual(serializer.validated_data['text'], 'This is a test message')
        self.assertEqual(serializer.validated_data['type'], MessageType.THOUGHTS.value)  # Validate enum
        print(f"  🔹 Validated title: {serializer.validated_data['title']}")
        print(f"  🔹 Validated text: {serializer.validated_data['text']} (type: {serializer.validated_data['type']})")
    
    def test_invalid_message_type(self):
        """Test that invalid message type is rejected"""
        data = {
            'title': 'Test Message',
            'text': 'This is a test message',
            'type': 'InvalidType',  # Not in MessageType enum
            'created_at': datetime.now().isoformat()
        }
        serializer = MessageInfosSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)
        print(f"  🔹 Type error detected: {serializer.errors.get('type')}")

    def test_missing_required_fields(self):
        """Test that missing required fields raises validation error"""
        data = {
            'text': 'This message has no title',
            'type': MessageType.THOUGHTS.value
        }
        serializer = MessageInfosSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        print(f"  🔹 Missing title error detected: {serializer.errors.get('title')}")

    def test_bleoid_validation_in_nested_serializers(self):
        """Test BLEOID validation when used in nested contexts"""
        # This test ensures MessageInfos works correctly when embedded in MessagesDays
        data = {
            'from_bleoid': 'ABC123',
            'to_bleoid': 'DEF456', 
            'date': '2023-05-27',
            'messages': [
                {
                    'title': 'Valid Message',
                    'text': 'Valid message text',
                    'type': MessageType.THOUGHTS.value
                }
            ]
        }
        
        # This should work with valid BLEOIDs
        from api.serializers import MessagesDaysSerializer
        serializer = MessagesDaysSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        print("  🔹 MessageInfos works correctly in nested serializer context")

    def test_message_type_string_to_enum_conversion(self):
        """Test that string message types are properly handled"""
        # Your MessageInfos model now validates types, so serializer should too
        data = {
            'title': 'Test Message',
            'text': 'Test content',
            'type': 'Thoughts'  # String that should be valid
        }
        
        serializer = MessageInfosSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['type'], 'Thoughts')
        
        print("  🔹 MessageInfos serializer handles string types correctly")

# To run the tests and see output
if __name__ == '__main__':
    print("Running MessageInfosSerializerTest...")
    run_test_with_output(MessageInfosSerializerTest)