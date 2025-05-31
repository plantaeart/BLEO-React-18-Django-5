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
            fromBLEOId="ABC123",
            toBLEOId="DEF456",
            date=datetime(2023, 5, 15)
        )
        
        # Check required fields
        self.assertEqual(message_day.fromBLEOId, "ABC123")
        self.assertEqual(message_day.toBLEOId, "DEF456")
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
            fromBLEOId="DEF456",
            toBLEOId="GHI789",
            date=datetime(2023, 5, 16),
            messages=messages,
            mood=MoodType.JOYFUL.value,
            energy_level=EnergyLevelType.HIGH.value,
            pleasantness=PleasantnessType.PLEASANT.value
        )
        
        # Check all fields were set correctly
        self.assertEqual(message_day.fromBLEOId, "DEF456")
        self.assertEqual(message_day.toBLEOId, "GHI789")
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
            fromBLEOId="GHI789",
            toBLEOId="JKL012",
            date=datetime(2023, 5, 17),
            energy_level=EnergyLevelType.HIGH.value
        )
        self.assertEqual(message_day1.energy_level, EnergyLevelType.HIGH.value)
        
        # Invalid energy level
        message_day2 = MessagesDays(
            fromBLEOId="GHI789",
            toBLEOId="JKL012",
            date=datetime(2023, 5, 17),
            energy_level="invalid_value"
        )
        self.assertEqual(message_day2.energy_level, "invalid_value")  # Now returns the value as-is
        
        # None energy level
        message_day3 = MessagesDays(
            fromBLEOId="GHI789",
            toBLEOId="JKL012",
            date=datetime(2023, 5, 17)
        )
        self.assertIsNone(message_day3.energy_level)
        
        print("  🔹 Energy level property handles valid, invalid and None values")
    
    def test_pleasantness_property(self):
        """Test the pleasantness property"""
        # Valid pleasantness
        message_day1 = MessagesDays(
            fromBLEOId="JKL012",
            toBLEOId="MNO345",
            date=datetime(2023, 5, 18),
            pleasantness=PleasantnessType.PLEASANT.value
        )
        self.assertEqual(message_day1.pleasantness, PleasantnessType.PLEASANT.value)  # Changed property name
        
        # Invalid pleasantness
        message_day2 = MessagesDays(
            fromBLEOId="JKL012",
            toBLEOId="MNO345",
            date=datetime(2023, 5, 18),
            pleasantness="invalid_value"
        )
        self.assertEqual(message_day2.pleasantness, "invalid_value")  # Changed property name, returns value as-is
        
        # None pleasantness
        message_day3 = MessagesDays(
            fromBLEOId="JKL012",
            toBLEOId="MNO345",
            date=datetime(2023, 5, 18)
        )
        self.assertIsNone(message_day3.pleasantness)  # Changed property name
        
        print("  🔹 Pleasantness property handles valid, invalid and None values")
    
    def test_get_mood_quadrant_method(self):
        """Test get_mood_quadrant returns correct quadrant"""
        # High energy + Pleasant
        message_day1 = MessagesDays(
            fromBLEOId="MNO345",
            toBLEOId="PQR678",
            date=datetime(2023, 5, 19),
            energy_level=EnergyLevelType.HIGH.value,
            pleasantness=PleasantnessType.PLEASANT.value
        )
        self.assertEqual(message_day1.get_mood_quadrant(), MoodQuadrantType.YELLOW.value)  # Add .value
        
        # Low energy + Unpleasant
        message_day2 = MessagesDays(
            fromBLEOId="MNO345",
            toBLEOId="PQR678",
            date=datetime(2023, 5, 19),
            energy_level=EnergyLevelType.LOW.value,
            pleasantness=PleasantnessType.UNPLEASANT.value
        )
        self.assertEqual(message_day2.get_mood_quadrant(), MoodQuadrantType.BLUE.value)  # Add .value
        
        # Missing energy level
        message_day3 = MessagesDays(
            fromBLEOId="MNO345",
            toBLEOId="PQR678",
            date=datetime(2023, 5, 19),
            pleasantness=PleasantnessType.PLEASANT.value
        )
        self.assertIsNone(message_day3.get_mood_quadrant())
        
        # Missing pleasantness
        message_day4 = MessagesDays(
            fromBLEOId="MNO345",
            toBLEOId="PQR678",
            date=datetime(2023, 5, 19),
            energy_level=EnergyLevelType.HIGH.value
        )
        self.assertIsNone(message_day4.get_mood_quadrant())
        
        print("  🔹 get_mood_quadrant returns correct quadrant based on energy and pleasantness")
    
    def test_to_dict_method(self):
        """Test MessagesDays to_dict method returns all fields"""
        message_day = MessagesDays(
            fromBLEOId="PQR678",
            toBLEOId="STU901",
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
        self.assertEqual(message_day_dict["fromBLEOId"], "PQR678")
        self.assertEqual(message_day_dict["toBLEOId"], "STU901")
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
            "fromBLEOId": "STU901",
            "toBLEOId": "VWX234",
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
        self.assertEqual(message_day.fromBLEOId, "STU901")
        self.assertEqual(message_day.toBLEOId, "VWX234")
        self.assertEqual(message_day.date, datetime(2023, 5, 21))
        self.assertEqual(len(message_day.messages), 1)
        self.assertEqual(message_day.messages[0].title, "FromDict")
        self.assertEqual(message_day.mood, MoodType.RELAXED.value)
        self.assertEqual(message_day._energy_level, EnergyLevelType.LOW.value)
        self.assertEqual(message_day._pleasantness, PleasantnessType.PLEASANT.value)
        
        print("  🔹 from_dict method creates MessagesDays object with correct values")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(MessagesDaysModelTest)