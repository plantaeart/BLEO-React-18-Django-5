from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import MessageInfosSerializer, MessagesDaysSerializer
from datetime import datetime
from models.enums.MessageType import MessageType
from models.enums.MoodType import MoodType 
from models.enums.EnergyLevelType import EnergyLevelType
from models.enums.PleasantnessType import PleasantnessType

class MessageDaySerializerTest(BLEOBaseTest):
    """Test cases for MessageDaySerializer validation and transformation"""
    
    def test_valid_message_day(self):
        """Test that valid message day passes validation"""
        data = {
            'from_bleoid': 'ABC123',
            'to_bleoid': 'DEF456',
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
        self.assertEqual(serializer.validated_data['from_bleoid'], 'ABC123')
        self.assertEqual(serializer.validated_data['to_bleoid'], 'DEF456')
        self.assertEqual(serializer.validated_data['mood'], MoodType.JOYFUL)
        self.assertEqual(serializer.validated_data['energy_level'], EnergyLevelType.HIGH)
        self.assertEqual(serializer.validated_data['pleasantness'], PleasantnessType.PLEASANT.value)
        print(f"  🔹 Validated from_bleoid: {serializer.validated_data['from_bleoid']}")
        print(f"  🔹 Validated to_bleoid: {serializer.validated_data['to_bleoid']}")
        print(f"  🔹 Validated mood: {serializer.validated_data['mood']}")
        print(f"  🔹 Messages count: {len(serializer.validated_data['messages'])}")
    
    def test_missing_to_bleoid(self):
        """Test that missing to_bleoid fails validation"""
        data = {
            'from_bleoid': 'ABC123',  # Only from_bleoid
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

        self.assertTrue(serializer.is_valid(), f"Serializer should be valid but got errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['from_bleoid'], 'ABC123')
        self.assertNotIn('to_bleoid', serializer.validated_data) 
        
        print(f"  🔹 Missing to_bleoid is OK - will be auto-discovered from link")
        print(f"  🔹 Validated from_bleoid: {serializer.validated_data['from_bleoid']}")
        print(f"  🔹 to_bleoid will be discovered in view layer")
        
    def test_invalid_energy_level(self):
        """Test that invalid energy level is rejected"""
        data = {
            'from_bleoid': 'ABC123',
            'to_bleoid': 'DEF456',
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
            'from_bleoid': 'ABC123',
            'to_bleoid': 'DEF456',
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
            'from_bleoid': 'ABC123',
            'to_bleoid': 'DEF456',
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
            'from_bleoid': 'ABC123',
            'to_bleoid': 'DEF456',
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
            'from_bleoid': 'ABC123',
            'to_bleoid': 'DEF456',
            'date': '27-05-2023',
            'energy_level': EnergyLevelType.LOW.value,
            'pleasantness': PleasantnessType.PLEASANT.value,
            'mood': MoodType.CALM.value
        }
        serializer = MessagesDaysSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        print(f"  🔹 Validated mood with energy/PleasantnessType combination")

    def test_null_bleoid_fields(self):
        """Test that null bleoid fields are rejected"""
        test_cases = [
            {'from_bleoid': None, 'to_bleoid': 'ABC123'},
            {'from_bleoid': 'ABC123', 'to_bleoid': None},
            {'from_bleoid': '', 'to_bleoid': 'ABC123'},
            {'from_bleoid': 'ABC123', 'to_bleoid': ''},
        ]
        
        for case in test_cases:
            data = {
                'date': '2025-01-01',
                'messages': []
            }
            data.update(case)
            
            serializer = MessagesDaysSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            # Should have errors for the invalid field

    def test_bleoid_format_validation(self):
        """Test BLEOID format validation in MessagesDays serializer"""
        # Test invalid BLEOID formats
        invalid_cases = [
            {'from_bleoid': 'abc-123', 'to_bleoid': 'DEF456'},  # Contains hyphen
            {'from_bleoid': 'ABC123', 'to_bleoid': 'def@456'},  # Contains @
            {'from_bleoid': '', 'to_bleoid': 'DEF456'},         # Empty
            {'from_bleoid': 'ABC123', 'to_bleoid': ''},         # Empty
            {'from_bleoid': 'ABCDEFG', 'to_bleoid': 'DEF456'},  # Too long
            {'from_bleoid': 'ABC12', 'to_bleoid': 'DEF456'},    # Too short
        ]
        
        base_data = {
            'date': '2023-05-27',
            'messages': []
        }
        
        for case in invalid_cases:
            test_data = {**base_data, **case}
            serializer = MessagesDaysSerializer(data=test_data)
            self.assertFalse(serializer.is_valid())
            
            # Check which field has the error
            if 'from_bleoid' in case and case['from_bleoid'] in ['abc-123', 'def@456', '', 'ABCDEFG', 'ABC12']:
                self.assertIn('from_bleoid', serializer.errors)
            if 'to_bleoid' in case and case['to_bleoid'] in ['def@456', '', 'ABCDEFG', 'ABC12']:
                self.assertIn('to_bleoid', serializer.errors)
        
        print("  🔹 BLEOID format validation works correctly in MessagesDays")

    def test_bleoid_normalization(self):
        """Test BLEOID normalization to uppercase"""
        data = {
            'from_bleoid': 'abc123',  # Lowercase
            'to_bleoid': 'def456',    # Lowercase
            'date': '2023-05-27',
            'messages': []
        }
        
        serializer = MessagesDaysSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Should be normalized to uppercase
        self.assertEqual(serializer.validated_data['from_bleoid'], 'ABC123')
        self.assertEqual(serializer.validated_data['to_bleoid'], 'DEF456')
        
        print("  🔹 BLEOID normalization works correctly in MessagesDays")

    def test_self_reference_validation(self):
        """Test that self-referencing messages are rejected"""
        data = {
            'from_bleoid': 'ABC123',
            'to_bleoid': 'ABC123',  # Same as from_bleoid
            'date': '2023-05-27',
            'messages': []
        }
        
        serializer = MessagesDaysSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('to_bleoid', serializer.errors)
        
        error_message = str(serializer.errors['to_bleoid'])
        self.assertIn('Cannot send messages to yourself', error_message)
        
        print("  🔹 Self-reference validation works correctly in MessagesDays")

# To run the tests and see output
if __name__ == '__main__':
    print("\nRunning MessageDaySerializerTest...")
    run_test_with_output(MessageDaySerializerTest)