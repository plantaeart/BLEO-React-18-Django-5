from tests.base_test import BLEOBaseTest, run_test_with_output
from models.MessagesDays import MessagesDays
from models.MessageInfos import MessageInfos
from models.enums.EnergyPleasantnessType import EnergyLevel, Pleasantness, MoodQuadrant
from datetime import datetime

class MessagesDaysModelTest(BLEOBaseTest):
    """Test cases for MessagesDays model"""
    
    def test_initialization_with_required_fields(self):
        """Test MessagesDays initialization with only required fields"""
        message_day = MessagesDays(
            BLEOId="ABC123",
            date=datetime(2023, 5, 15)
        )
        
        # Check required fields
        self.assertEqual(message_day.BLEOId, "ABC123")
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
            {"id": 1, "title": "First", "text": "First message", "type": "Thoughts"},
            {"id": 2, "title": "Second", "text": "Second message", "type": "Journal"}
        ]
        
        message_day = MessagesDays(
            BLEOId="DEF456",
            date=datetime(2023, 5, 16),
            messages=messages,
            mood="Happy",
            energy_level="high",
            pleasantness="pleasant"
        )
        
        # Check all fields were set correctly
        self.assertEqual(message_day.BLEOId, "DEF456")
        self.assertEqual(message_day.date, datetime(2023, 5, 16))
        self.assertEqual(len(message_day.messages), 2)
        self.assertEqual(message_day.messages[0].title, "First")
        self.assertEqual(message_day.mood, "Happy")
        self.assertEqual(message_day._energy_level, "high")
        self.assertEqual(message_day._pleasantness, "pleasant")
        
        print("  🔹 MessagesDays initialized with custom messages, mood, energy and pleasantness")
    
    def test_energy_level_property(self):
        """Test the energy_level property"""
        # Valid energy level
        message_day1 = MessagesDays(
            BLEOId="GHI789",
            date=datetime(2023, 5, 17),
            energy_level="high"
        )
        self.assertEqual(message_day1.energy_level, EnergyLevel.HIGH)
        
        # Invalid energy level
        message_day2 = MessagesDays(
            BLEOId="GHI789",
            date=datetime(2023, 5, 17),
            energy_level="invalid_value"
        )
        self.assertIsNone(message_day2.energy_level)
        
        # None energy level
        message_day3 = MessagesDays(
            BLEOId="GHI789",
            date=datetime(2023, 5, 17)
        )
        self.assertIsNone(message_day3.energy_level)
        
        print("  🔹 Energy level property handles valid, invalid and None values")
    
    def test_pleasantness_property(self):
        """Test the pleasantness property"""
        # Valid pleasantness
        message_day1 = MessagesDays(
            BLEOId="JKL012",
            date=datetime(2023, 5, 18),
            pleasantness="pleasant"
        )
        self.assertEqual(message_day1.pleasantness, Pleasantness.PLEASANT)
        
        # Invalid pleasantness
        message_day2 = MessagesDays(
            BLEOId="JKL012",
            date=datetime(2023, 5, 18),
            pleasantness="invalid_value"
        )
        self.assertIsNone(message_day2.pleasantness)
        
        # None pleasantness
        message_day3 = MessagesDays(
            BLEOId="JKL012",
            date=datetime(2023, 5, 18)
        )
        self.assertIsNone(message_day3.pleasantness)
        
        print("  🔹 Pleasantness property handles valid, invalid and None values")
    
    def test_get_mood_quadrant_method(self):
        """Test get_mood_quadrant returns correct quadrant"""
        # High energy + Pleasant
        message_day1 = MessagesDays(
            BLEOId="MNO345",
            date=datetime(2023, 5, 19),
            energy_level="high",
            pleasantness="pleasant"
        )
        self.assertEqual(message_day1.get_mood_quadrant(), MoodQuadrant.YELLOW)
        
        # Low energy + Unpleasant
        message_day2 = MessagesDays(
            BLEOId="MNO345",
            date=datetime(2023, 5, 19),
            energy_level="low",
            pleasantness="unpleasant"
        )
        self.assertEqual(message_day2.get_mood_quadrant(), MoodQuadrant.BLUE)
        
        # Missing energy level
        message_day3 = MessagesDays(
            BLEOId="MNO345",
            date=datetime(2023, 5, 19),
            pleasantness="pleasant"
        )
        self.assertIsNone(message_day3.get_mood_quadrant())
        
        # Missing pleasantness
        message_day4 = MessagesDays(
            BLEOId="MNO345",
            date=datetime(2023, 5, 19),
            energy_level="high"
        )
        self.assertIsNone(message_day4.get_mood_quadrant())
        
        print("  🔹 get_mood_quadrant returns correct quadrant based on energy and pleasantness")
    
    def test_to_dict_method(self):
        """Test MessagesDays to_dict method returns all fields"""
        message_day = MessagesDays(
            BLEOId="PQR678",
            date=datetime(2023, 5, 20),
            messages=[
                {"id": 1, "title": "Dict", "text": "Dict test", "type": "Notes"}
            ],
            mood="Content",
            energy_level="medium",
            pleasantness="pleasant"
        )
        
        message_day_dict = message_day.to_dict()
        
        # Check all fields are in the dict
        self.assertEqual(message_day_dict["BLEOId"], "PQR678")
        self.assertEqual(message_day_dict["date"], datetime(2023, 5, 20))
        self.assertEqual(len(message_day_dict["messages"]), 1)
        self.assertEqual(message_day_dict["messages"][0]["title"], "Dict")
        self.assertEqual(message_day_dict["mood"], "Content")
        self.assertEqual(message_day_dict["energy_level"], "medium")
        self.assertEqual(message_day_dict["pleasantness"], "pleasant")
        
        print("  🔹 to_dict method returns complete dictionary with all fields")
    
    def test_from_dict_method(self):
        """Test MessagesDays from_dict method creates correct object"""
        input_dict = {
            "BLEOId": "STU901",
            "date": datetime(2023, 5, 21),
            "messages": [
                {"id": 1, "title": "FromDict", "text": "FromDict test", "type": "Thoughts"}
            ],
            "mood": "Relaxed",
            "energy_level": "low",
            "pleasantness": "pleasant"
        }
        
        message_day = MessagesDays.from_dict(input_dict)
        
        # Check all fields were set correctly
        self.assertEqual(message_day.BLEOId, "STU901")
        self.assertEqual(message_day.date, datetime(2023, 5, 21))
        self.assertEqual(len(message_day.messages), 1)
        self.assertEqual(message_day.messages[0].title, "FromDict")
        self.assertEqual(message_day.mood, "Relaxed")
        self.assertEqual(message_day._energy_level, "low")
        self.assertEqual(message_day._pleasantness, "pleasant")
        
        print("  🔹 from_dict method creates MessagesDays object with correct values")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(MessagesDaysModelTest)