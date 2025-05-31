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

class MessageDaySerializerTest(BLEOBaseTest):
    """Test cases for MessageDaySerializer validation and transformation"""
    
    def test_valid_message_day(self):
        """Test that valid message day passes validation"""
        data = {
            'fromBLEOId': 'ABC123',
            'toBLEOId': 'DEF456',
            'date': '27-05-2023',
            'messages': [
                {
                    'title': 'Message 1',
                    'text': 'Text for message 1',
                    'type': MessageType.THOUGHTS.value
                }
            ],
            'mood': MoodType.JOYFUL.value,
            'energy_level': EnergyLevelType.HIGH.value,
            'pleasantness': PleasantnessType.PLEASANT.value
        }
        serializer = MessagesDaysSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['fromBLEOId'], 'ABC123')
        self.assertEqual(serializer.validated_data['toBLEOId'], 'DEF456')
        self.assertEqual(serializer.validated_data['mood'], MoodType.JOYFUL)
        self.assertEqual(serializer.validated_data['energy_level'], EnergyLevelType.HIGH)
        self.assertEqual(serializer.validated_data['pleasantness'], PleasantnessType.PLEASANT.value)
        print(f"  🔹 Validated fromBLEOId: {serializer.validated_data['fromBLEOId']}")
        print(f"  🔹 Validated toBLEOId: {serializer.validated_data['toBLEOId']}")
        print(f"  🔹 Validated mood: {serializer.validated_data['mood']}")
        print(f"  🔹 Messages count: {len(serializer.validated_data['messages'])}")
    
    def test_missing_to_bleoid(self):
        """Test that missing toBLEOId fails validation"""
        data = {
            'fromBLEOId': 'ABC123',  # Only fromBLEOId
            'date': '27-05-2023',
            'messages': [
                {
                    'title': 'Message 1',
                    'text': 'Text for message 1',
                    'type': MessageType.THOUGHTS.value
                }
            ]
        }
        serializer = MessagesDaysSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('toBLEOId', serializer.errors)
        print(f"  🔹 Missing toBLEOId error detected: {serializer.errors.get('toBLEOId')}")
    
    def test_invalid_energy_level(self):
        """Test that invalid energy level is rejected"""
        data = {
            'fromBLEOId': 'ABC123',
            'toBLEOId': 'DEF456',
            'date': '27-05-2023',
            'energy_level': 'invalid_energy',  # Not in EnergyLevelType enum
            'pleasantness': PleasantnessType.PLEASANT.value
        }
        serializer = MessagesDaysSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('energy_level', serializer.errors)
        print(f"  🔹 Energy level error detected: {serializer.errors.get('energy_level')}")
    
    def test_alternative_date_format(self):
        """Test that both date formats are accepted"""
        data = {
            'fromBLEOId': 'ABC123',
            'toBLEOId': 'DEF456',
            'date': '2023-05-27',  # YYYY-MM-DD format
        }
        serializer = MessagesDaysSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        print(f"  🔹 YYYY-MM-DD format accepted: {serializer.validated_data['date']}")
        
        # Test DD-MM-YYYY format
        data['date'] = '27-05-2023'
        serializer = MessagesDaysSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        print(f"  🔹 DD-MM-YYYY format accepted: {serializer.validated_data['date']}")
        
    def test_message_types_in_nested_messages(self):
        """Test that message types are properly validated in nested messages"""
        data = {
            'fromBLEOId': 'ABC123',
            'toBLEOId': 'DEF456',
            'date': '27-05-2023',
            'messages': [
                {
                    'title': 'Message 1',
                    'text': 'Text for message 1',
                    'type': MessageType.THOUGHTS.value
                },
                {
                    'title': 'Message 2',
                    'text': 'Text for message 2',
                    'type': MessageType.LOVE_MESSAGE.value
                },
                {
                    'title': 'Message 3',
                    'text': 'Text for message 3',
                    'type': 'InvalidType'  # Not in MessageType enum
                }
            ]
        }
        serializer = MessagesDaysSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        # The error will be in the messages field with details about the 3rd item
        self.assertIn('messages', serializer.errors)
        print(f"  🔹 Message type error detected in nested messages: {serializer.errors.get('messages')}")

    def test_mood_quadrant_calculation(self):
        """Test that mood quadrant is calculated from energy and PleasantnessType"""
        # High energy, pleasant mood (Yellow quadrant)
        data = {
            'fromBLEOId': 'ABC123',
            'toBLEOId': 'DEF456',
            'date': '27-05-2023',
            'energy_level': EnergyLevelType.HIGH.value,
            'pleasantness': PleasantnessType.PLEASANT.value,
            'mood': MoodType.JOYFUL.value
        }
        serializer = MessagesDaysSerializer(data=data)
        print(f"  🔹 Error displayed : {serializer.error_messages}")
        self.assertTrue(serializer.is_valid())
        
        # Low energy, pleasant mood (Green quadrant) 
        data = {
            'fromBLEOId': 'ABC123',
            'toBLEOId': 'DEF456',
            'date': '27-05-2023',
            'energy_level': EnergyLevelType.LOW.value,
            'pleasantness': PleasantnessType.PLEASANT.value,
            'mood': MoodType.CALM.value
        }
        serializer = MessagesDaysSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        print(f"  🔹 Validated mood with energy/PleasantnessType combination")

# To run the tests and see output
if __name__ == '__main__':
    print("Running MessageInfosSerializerTest...")
    run_test_with_output(MessageInfosSerializerTest)
    
    print("\nRunning MessageDaySerializerTest...")
    run_test_with_output(MessageDaySerializerTest)