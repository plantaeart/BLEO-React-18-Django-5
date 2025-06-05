from typing import List, Dict, Any, Optional
from datetime import datetime
from models.MessageInfos import MessageInfos
from models.enums.MoodType import MoodType
from models.enums.MoodQuadrantType import MoodQuadrantType
from models.enums.EnergyLevelType import EnergyLevelType
from models.enums.PleasantnessType import PleasantnessType
import re

class MessagesDays:
    """Daily messages schema"""
    def __init__(
        self,
        from_bleoid: str,
        to_bleoid: str,
        date: datetime,
        messages: List[Dict[str, Any]] = None,
        mood: str = None,
        energy_level: str = None,
        pleasantness: str = None
    ):
        self.from_bleoid = self._validate_and_normalize_bleoid(from_bleoid, "from_bleoid")
        self.to_bleoid = self._validate_and_normalize_bleoid(to_bleoid, "to_bleoid")
        
        # Check after normalization
        if self.from_bleoid == self.to_bleoid:
            raise ValueError("from_bleoid and to_bleoid cannot be the same")
        
        self.date = date or datetime.now().date()
        self.messages = [MessageInfos.from_dict(msg) for msg in (messages or [])]
        self.mood = mood
        self._energy_level = energy_level
        self._pleasantness = pleasantness
    
    @staticmethod
    def _validate_and_normalize_bleoid(value: str, field_name: str) -> str:
        """Validate and normalize BLEOID format"""
        if not value:
            raise ValueError(f"{field_name} cannot be null or empty")
        
        if not value or len(value.strip()) == 0:
            raise ValueError(f"{field_name} cannot be empty")
        
        # Normalize to uppercase and strip whitespace
        normalized_bleoid = value.strip().upper()
        
        # Validate format matches pattern ^[A-Z0-9]{6}$
        if not re.match(r'^[A-Z0-9]{6}$', normalized_bleoid):
            raise ValueError(f"{field_name} must be exactly 6 uppercase letters/numbers. Invalid format: '{value}'")
        
        return normalized_bleoid
    
    @property
    def energy_level(self) -> Optional[str]:
        """Get the energy level"""
        if self._energy_level:
            try:
                return self._energy_level
            except ValueError:
                return None
        return None
    
    @energy_level.setter
    def energy_level(self, value: str):
        """Set the energy level"""
        self._energy_level = value
    
    @property
    def pleasantness(self) -> Optional[str]:
        """Get the pleasantness level"""
        if self._pleasantness:
            try:
                return self._pleasantness
            except ValueError:
                return None
        return None
    
    @pleasantness.setter
    def pleasantness(self, value: str):
        """Set the pleasantness level"""
        self._pleasantness = value
    
    def get_mood_quadrant(self) -> Optional[str]:
        """Get the mood quadrant based on energy and pleasantness"""
        if self._energy_level and self._pleasantness:
            try:
                energy = EnergyLevelType(self._energy_level)
                pleasant = PleasantnessType(self._pleasantness)
                return MoodQuadrantType.from_dimensions(energy, pleasant).value
            except (ValueError, KeyError):
                return None
        return None
    
    def get_moods_for_current_quadrant(self) -> List[str]:
        """Get all mood types that belong to the current quadrant"""
        quadrant = self.get_mood_quadrant()
        if not quadrant:
            return [mood.value for mood in MoodType]
        
        return [mood.value for mood in MoodType if mood.quadrant.value == quadrant]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_bleoid": self.from_bleoid,
            "to_bleoid": self.to_bleoid,
            "date": self.date,
            "messages": [msg.to_dict() for msg in self.messages],
            "mood": self.mood,
            "energy_level": self._energy_level,
            "pleasantness": self._pleasantness
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessagesDays':
        """Create MessagesDays from dictionary with validation"""
        from_bleoid = data.get("from_bleoid")
        to_bleoid = data.get("to_bleoid")
        
        if not from_bleoid:
            raise ValueError("from_bleoid is required")
        if not to_bleoid:
            raise ValueError("to_bleoid is required")
            
        return cls(
            from_bleoid=from_bleoid,
            to_bleoid=to_bleoid,
            date=data.get("date"),
            messages=data.get("messages", []),
            mood=data.get("mood"),
            energy_level=data.get("energy_level"),
            pleasantness=data.get("pleasantness")
        )