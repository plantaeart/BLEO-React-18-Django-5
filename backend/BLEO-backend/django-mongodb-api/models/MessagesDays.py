from typing import List, Dict, Any, Optional
from datetime import datetime
from models.MessageInfos import MessageInfos
from models.enums.MoodType import MoodType
from models.enums.MoodQuadrantType import MoodQuadrantType
from models.enums.EnergyLevelType import EnergyLevelType
from models.enums.PleasantnessType import PleasantnessType

class MessagesDays:
    """Daily messages schema"""
    def __init__(
        self,
        fromBLEOId: str,
        toBLEOId: str,
        date: datetime,
        messages: List[Dict[str, Any]] = None,
        mood: str = None,
        energy_level: str = None,
        pleasantness: str = None
    ):
        self.fromBLEOId = fromBLEOId
        self.toBLEOId = toBLEOId
        self.date = date or datetime.now().date()
        self.messages = [MessageInfos.from_dict(msg) for msg in (messages or [])]
        self.mood = mood
        self._energy_level = energy_level
        self._pleasantness = pleasantness
    
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
            "fromBLEOId": self.fromBLEOId,
            "toBLEOId": self.toBLEOId,
            "date": self.date,
            "messages": [msg.to_dict() for msg in self.messages],
            "mood": self.mood,
            "energy_level": self._energy_level,
            "pleasantness": self._pleasantness
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessagesDays':
        return cls(
            fromBLEOId=data.get("fromBLEOId"),
            toBLEOId=data.get("toBLEOId"),
            date=data.get("date"),
            messages=data.get("messages", []),
            mood=data.get("mood"),
            energy_level=data.get("energy_level"),
            pleasantness=data.get("pleasantness")
        )