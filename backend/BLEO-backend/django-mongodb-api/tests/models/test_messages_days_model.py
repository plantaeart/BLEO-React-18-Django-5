from tests.base_test import BLEOBaseTest, run_test_with_output
from models.MessagesDays import MessagesDays
from models.MessageInfos import MessageInfos
from models.enums.MoodQuadrantType import MoodQuadrantType
from models.enums.EnergyLevelType import EnergyLevelType
from models.enums.PleasantnessType import PleasantnessType
from models.enums.MessageType import MessageType
from models.enums.MoodType import MoodType
from datetime import datetime

class MessagesDaysModelTest(BLEOBaseTest):
    """Test cases for MessagesDays model"""
    
    def test_initialization_with_required_fields(self):
        """Test MessagesDays initialization with only required fields"""
        message_day = MessagesDays(
            from_bleoid="ABC123",
            to_bleoid="DEF456",
            date=datetime(2023, 5, 15)
        )
        
        # Check required fields
        self.assertEqual(message_day.from_bleoid, "ABC123")
        self.assertEqual(message_day.to_bleoid, "DEF456")
        self.assertEqual(message_day.date, datetime(2023, 5, 15))
        
        # Check default values
        self.assertEqual(message_day.messages, [])
        self.assertIsNone(message_day.mood)
        self.assertIsNone(message_day._energy_level)
        self.assertIsNone(message_day._pleasantness)
        
        print("  🔹 MessagesDays initialized with default values for optional fields")
    
    def test_initialization_with_all_fields(self):
        """Test MessagesDays initialization with all fields provided"""
        messages = [
            {"id": 1, "title": "First", "text": "First message", "type": MessageType.THOUGHTS.value},
            {"id": 2, "title": "Second", "text": "Second message", "type": MessageType.NOTES.value}
        ]
        
        message_day = MessagesDays(
            from_bleoid="DEF456",
            to_bleoid="GHI789",
            date=datetime(2023, 5, 16),
            messages=messages,
            mood=MoodType.JOYFUL.value,
            energy_level=EnergyLevelType.HIGH.value,
            pleasantness=PleasantnessType.PLEASANT.value
        )
        
        # Check all fields were set correctly
        self.assertEqual(message_day.from_bleoid, "DEF456")
        self.assertEqual(message_day.to_bleoid, "GHI789")
        self.assertEqual(message_day.date, datetime(2023, 5, 16))
        self.assertEqual(len(message_day.messages), 2)
        self.assertEqual(message_day.messages[0].title, "First")
        self.assertEqual(message_day.mood, MoodType.JOYFUL.value)
        self.assertEqual(message_day._energy_level, EnergyLevelType.HIGH.value)
        self.assertEqual(message_day._pleasantness, PleasantnessType.PLEASANT.value)
        
        print("  🔹 MessagesDays initialized with custom messages, mood, energy and pleasantness")
    
    def test_energy_level_property(self):
        """Test the energy_level property"""
        # Valid energy level
        message_day1 = MessagesDays(
            from_bleoid="GHI789",
            to_bleoid="JKL012",
            date=datetime(2023, 5, 17),
            energy_level=EnergyLevelType.HIGH.value
        )
        self.assertEqual(message_day1.energy_level, EnergyLevelType.HIGH.value)
        
        # Invalid energy level
        message_day2 = MessagesDays(
            from_bleoid="GHI789",
            to_bleoid="JKL012",
            date=datetime(2023, 5, 17),
            energy_level="invalid_value"
        )
        self.assertEqual(message_day2.energy_level, "invalid_value")  # Now returns the value as-is
        
        # None energy level
        message_day3 = MessagesDays(
            from_bleoid="GHI789",
            to_bleoid="JKL012",
            date=datetime(2023, 5, 17)
        )
        self.assertIsNone(message_day3.energy_level)
        
        print("  🔹 Energy level property handles valid, invalid and None values")
    
    def test_pleasantness_property(self):
        """Test the pleasantness property"""
        # Valid pleasantness
        message_day1 = MessagesDays(
            from_bleoid="JKL012",
            to_bleoid="MNO345",
            date=datetime(2023, 5, 18),
            pleasantness=PleasantnessType.PLEASANT.value
        )
        self.assertEqual(message_day1.pleasantness, PleasantnessType.PLEASANT.value)  # Changed property name
        
        # Invalid pleasantness
        message_day2 = MessagesDays(
            from_bleoid="JKL012",
            to_bleoid="MNO345",
            date=datetime(2023, 5, 18),
            pleasantness="invalid_value"
        )
        self.assertEqual(message_day2.pleasantness, "invalid_value")  # Changed property name, returns value as-is
        
        # None pleasantness
        message_day3 = MessagesDays(
            from_bleoid="JKL012",
            to_bleoid="MNO345",
            date=datetime(2023, 5, 18)
        )
        self.assertIsNone(message_day3.pleasantness)  # Changed property name
        
        print("  🔹 Pleasantness property handles valid, invalid and None values")
    
    def test_get_mood_quadrant_method(self):
        """Test get_mood_quadrant returns correct quadrant"""
        # High energy + Pleasant
        message_day1 = MessagesDays(
            from_bleoid="MNO345",
            to_bleoid="PQR678",
            date=datetime(2023, 5, 19),
            energy_level=EnergyLevelType.HIGH.value,
            pleasantness=PleasantnessType.PLEASANT.value
        )
        self.assertEqual(message_day1.get_mood_quadrant(), MoodQuadrantType.YELLOW.value)  # Add .value
        
        # Low energy + Unpleasant
        message_day2 = MessagesDays(
            from_bleoid="MNO345",
            to_bleoid="PQR678",
            date=datetime(2023, 5, 19),
            energy_level=EnergyLevelType.LOW.value,
            pleasantness=PleasantnessType.UNPLEASANT.value
        )
        self.assertEqual(message_day2.get_mood_quadrant(), MoodQuadrantType.BLUE.value)  # Add .value
        
        # Missing energy level
        message_day3 = MessagesDays(
            from_bleoid="MNO345",
            to_bleoid="PQR678",
            date=datetime(2023, 5, 19),
            pleasantness=PleasantnessType.PLEASANT.value
        )
        self.assertIsNone(message_day3.get_mood_quadrant())
        
        # Missing pleasantness
        message_day4 = MessagesDays(
            from_bleoid="MNO345",
            to_bleoid="PQR678",
            date=datetime(2023, 5, 19),
            energy_level=EnergyLevelType.HIGH.value
        )
        self.assertIsNone(message_day4.get_mood_quadrant())
        
        print("  🔹 get_mood_quadrant returns correct quadrant based on energy and pleasantness")
    
    def test_to_dict_method(self):
        """Test MessagesDays to_dict method returns all fields"""
        message_day = MessagesDays(
            from_bleoid="PQR678",
            to_bleoid="STU901",
            date=datetime(2023, 5, 20),
            messages=[
                {"id": 1, "title": "Dict", "text": "Dict test", "type": MessageType.NOTES.value}
            ],
            mood=MoodType.CONTENT.value,
            energy_level=EnergyLevelType.LOW.value,
            pleasantness=PleasantnessType.PLEASANT.value
        )
        
        message_day_dict = message_day.to_dict()
        
        # Check all fields are in the dict
        self.assertEqual(message_day_dict["from_bleoid"], "PQR678")
        self.assertEqual(message_day_dict["to_bleoid"], "STU901")
        self.assertEqual(message_day_dict["date"], datetime(2023, 5, 20))
        self.assertEqual(len(message_day_dict["messages"]), 1)
        self.assertEqual(message_day_dict["messages"][0]["title"], "Dict")
        self.assertEqual(message_day_dict["mood"], MoodType.CONTENT.value)
        self.assertEqual(message_day_dict["energy_level"], EnergyLevelType.LOW.value)
        self.assertEqual(message_day_dict["pleasantness"], PleasantnessType.PLEASANT.value)
        
        print("  🔹 to_dict method returns complete dictionary with all fields")
    
    def test_from_dict_method(self):
        """Test MessagesDays from_dict method creates correct object"""
        input_dict = {
            "from_bleoid": "STU901",
            "to_bleoid": "VWX234",
            "date": datetime(2023, 5, 21),
            "messages": [
                {"id": 1, "title": "FromDict", "text": "FromDict test", "type": MessageType.THOUGHTS.value}
            ],
            "mood": MoodType.RELAXED.value,
            "energy_level": EnergyLevelType.LOW.value,
            "pleasantness": PleasantnessType.PLEASANT.value
        }
        
        message_day = MessagesDays.from_dict(input_dict)
        
        # Check all fields were set correctly
        self.assertEqual(message_day.from_bleoid, "STU901")
        self.assertEqual(message_day.to_bleoid, "VWX234")
        self.assertEqual(message_day.date, datetime(2023, 5, 21))
        self.assertEqual(len(message_day.messages), 1)
        self.assertEqual(message_day.messages[0].title, "FromDict")
        self.assertEqual(message_day.mood, MoodType.RELAXED.value)
        self.assertEqual(message_day._energy_level, EnergyLevelType.LOW.value)
        self.assertEqual(message_day._pleasantness, PleasantnessType.PLEASANT.value)
        
        print("  🔹 from_dict method creates MessagesDays object with correct values")
    
    def test_bleoid_format_validation(self):
        """Test BLEOID format validation in MessagesDays"""
        # Valid BLEOIDs should work
        valid_msg = MessagesDays(
            from_bleoid="ABC123",
            to_bleoid="DEF456",
            date=datetime(2023, 5, 15)
        )
        self.assertEqual(valid_msg.from_bleoid, "ABC123")
        self.assertEqual(valid_msg.to_bleoid, "DEF456")
        print("    ✓ Valid BLEOIDs accepted")
        
        # Cases that should be NORMALIZED (not rejected)
        normalization_cases = [
            ("abc123", "ABC123"),      # Lowercase to uppercase
            ("def456", "DEF456"),      # Lowercase to uppercase
            ("  ABC123  ", "ABC123"),  # Trim whitespace
            ("  def456  ", "DEF456"),  # Lowercase + whitespace
            ("AbC123", "ABC123"),      # Mixed case
        ]
        
        for input_bleoid, expected_bleoid in normalization_cases:
            msg = MessagesDays(
                from_bleoid=input_bleoid,
                to_bleoid="XYZ789",  # Valid second BLEOID
                date=datetime(2023, 5, 15)
            )
            self.assertEqual(msg.from_bleoid, expected_bleoid)
            print(f"    ✓ Normalized from_bleoid '{input_bleoid}' → '{expected_bleoid}'")
            
            # Test to_bleoid normalization too
            msg2 = MessagesDays(
                from_bleoid="XYZ789",  # Valid first BLEOID
                to_bleoid=input_bleoid,
                date=datetime(2023, 5, 15)
            )
            self.assertEqual(msg2.to_bleoid, expected_bleoid)
            print(f"    ✓ Normalized to_bleoid '{input_bleoid}' → '{expected_bleoid}'")
        
        # Cases that should be REJECTED (truly invalid)
        invalid_cases = [
            {"from_bleoid": "ABC-12", "to_bleoid": "DEF456", "reason": "hyphen in from_bleoid"},
            {"from_bleoid": "ABC123", "to_bleoid": "DEF@56", "reason": "@ symbol in to_bleoid"},
            {"from_bleoid": "", "to_bleoid": "DEF456", "reason": "empty from_bleoid"},
            {"from_bleoid": "ABC123", "to_bleoid": "", "reason": "empty to_bleoid"},
            {"from_bleoid": "ABCDEFG", "to_bleoid": "DEF456", "reason": "too long from_bleoid"},
            {"from_bleoid": "ABC123", "to_bleoid": "DEFGH", "reason": "too short to_bleoid"},
            {"from_bleoid": "ABC 12", "to_bleoid": "DEF456", "reason": "space in from_bleoid"},
            {"from_bleoid": "ABC123", "to_bleoid": "DEF 56", "reason": "space in to_bleoid"},
        ]
        
        for case in invalid_cases:
            with self.assertRaises(ValueError) as context:
                MessagesDays(
                    from_bleoid=case["from_bleoid"],
                    to_bleoid=case["to_bleoid"],
                    date=datetime(2023, 5, 15)
                )
            
            error_message = str(context.exception)
            print(f"    ✓ Correctly rejected {case['reason']}: {error_message}")
        
        print("  🔹 MessagesDays BLEOID format validation and normalization work correctly")
    
    def test_self_reference_validation(self):
        """Test that self-referencing messages are rejected"""
        with self.assertRaises(ValueError) as context:
            MessagesDays(
                from_bleoid="ABC123",
                to_bleoid="ABC123",  # Same as from_bleoid
                date=datetime(2023, 5, 15)
            )
        
        self.assertIn("cannot be the same", str(context.exception))
        print("  🔹 MessagesDays correctly rejects self-references")
    
    def test_bleoid_normalization(self):
        """Test BLEOID normalization to uppercase"""
        msg = MessagesDays(
            from_bleoid="abc123",  # Lowercase input
            to_bleoid="def456",   # Lowercase input
            date=datetime(2023, 5, 15)
        )
        
        # Should be normalized to uppercase
        self.assertEqual(msg.from_bleoid, "ABC123")
        self.assertEqual(msg.to_bleoid, "DEF456")
        
        # Test more normalization cases
        normalization_test_cases = [
            # (input_from, input_to, expected_from, expected_to)
            ("  ghi789  ", "  jkl012  ", "GHI789", "JKL012"),  # Whitespace
            ("AbC123", "dEf456", "ABC123", "DEF456"),           # Mixed case
            ("123abc", "456def", "123ABC", "456DEF"),           # Numbers first
        ]
        
        for input_from, input_to, expected_from, expected_to in normalization_test_cases:
            msg = MessagesDays(
                from_bleoid=input_from,
                to_bleoid=input_to,
                date=datetime(2023, 5, 15)
            )
            
            self.assertEqual(msg.from_bleoid, expected_from)
            self.assertEqual(msg.to_bleoid, expected_to)
            print(f"    ✓ Normalized '{input_from}' + '{input_to}' → '{expected_from}' + '{expected_to}'")
        
        print("  🔹 MessagesDays normalizes BLEOIDs to uppercase correctly")
    
    def test_self_reference_validation_with_normalization(self):
        """Test that self-referencing messages are rejected even after normalization"""
        
        # Same BLEOID in different cases should still be detected as self-reference
        self_reference_cases = [
            ("abc123", "ABC123"),  # Same after normalization
            ("ABC123", "abc123"),  # Same after normalization
            ("  abc123  ", "ABC123"),  # Same after trimming and normalization
            ("AbC123", "aBc123"),  # Same after normalization
        ]
        
        for from_bleoid, to_bleoid in self_reference_cases:
            with self.assertRaises(ValueError) as context:
                MessagesDays(
                    from_bleoid=from_bleoid,
                    to_bleoid=to_bleoid,
                    date=datetime(2023, 5, 15)
                )
            
            error_message = str(context.exception)
            self.assertIn("cannot be the same", error_message)
            print(f"    ✓ Correctly rejected self-reference: '{from_bleoid}' == '{to_bleoid}' after normalization")
        
        print("  🔹 Self-reference validation works correctly with normalization")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(MessagesDaysModelTest)