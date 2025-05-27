from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import MessageInfosSerializer, MessagesDayserializer
from datetime import datetime

class MessageInfosSerializerTest(BLEOBaseTest):
    """Test cases for MessageInfosSerializer validation and transformation"""
    
    def test_valid_message_info(self):
        """Test that valid message info passes validation"""
        data = {
            'title': 'Test Message',
            'text': 'This is a test message',
            'type': 'Thoughts',
            'created_at': datetime.now().isoformat()
        }
        serializer = MessageInfosSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['title'], 'Test Message')
        self.assertEqual(serializer.validated_data['text'], 'This is a test message')
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
            'type': 'Thoughts'
        }
        serializer = MessageInfosSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        print(f"  🔹 Missing title error detected: {serializer.errors.get('title')}")

class MessageDaySerializerTest(BLEOBaseTest):
    """Test cases for MessageDaySerializer validation and transformation"""
    
    def test_valid_message_day(self):
        """Test that valid message day passes validation"""
        data = {
            'BLEOId': 'WQJ94S',
            'date': '27-05-2023',
            'messages': [
                {
                    'title': 'Message 1',
                    'text': 'Text for message 1',
                    'type': 'Thoughts'
                }
            ],
            'mood': 'Happy',
            'energy_level': 'high',
            'pleasantness': 'pleasant'
        }
        serializer = MessagesDayserializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['BLEOId'], 'WQJ94S')
        self.assertEqual(serializer.validated_data['mood'], 'Happy')
        print(f"  🔹 Validated BLEOId: {serializer.validated_data['BLEOId']}")
        print(f"  🔹 Validated mood: {serializer.validated_data['mood']}")
        print(f"  🔹 Messages count: {len(serializer.validated_data['messages'])}")
    
    def test_invalid_energy_level(self):
        """Test that invalid energy level is rejected"""
        data = {
            'BLEOId': 'WQJ94S',
            'date': '27-05-2023',
            'energy_level': 'invalid_energy',  # Not in EnergyLevel enum
            'pleasantness': 'pleasant'
        }
        serializer = MessagesDayserializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('energy_level', serializer.errors)
        print(f"  🔹 Energy level error detected: {serializer.errors.get('energy_level')}")
    
    def test_alternative_date_format(self):
        """Test that both date formats are accepted"""
        data = {
            'BLEOId': 'WQJ94S',
            'date': '2023-05-27',  # YYYY-MM-DD format
        }
        serializer = MessagesDayserializer(data=data)
        self.assertTrue(serializer.is_valid())
        print(f"  🔹 YYYY-MM-DD format accepted: {serializer.validated_data['date']}")
        
        # Test DD-MM-YYYY format
        data['date'] = '27-05-2023'
        serializer = MessagesDayserializer(data=data)
        self.assertTrue(serializer.is_valid())
        print(f"  🔹 DD-MM-YYYY format accepted: {serializer.validated_data['date']}")

# To run the tests and see output
if __name__ == '__main__':
    print("Running MessageInfosSerializerTest...")
    run_test_with_output(MessageInfosSerializerTest)
    
    print("\nRunning MessageDaySerializerTest...")
    run_test_with_output(MessageDaySerializerTest)