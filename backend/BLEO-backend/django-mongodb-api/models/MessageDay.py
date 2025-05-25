from typing import List, Dict, Any, Optional
from datetime import datetime
from models.MessageInfos import MessageInfos
from models.enums.MoodType import MoodType
from models.enums.EnergyPleasantnessType import MoodQuadrant, EnergyLevel, Pleasantness

class MessageDay:
    """Daily messages schema"""
    def __init__(
        self,
        BLEOId: int,
        date: datetime,
        messages: List[Dict[str, Any]] = None,
        mood: str = None,
        energy_level: str = None,
        pleasantness: str = None
    ):
        self.BLEOId = BLEOId
        self.date = date or datetime.now().date()
        self.messages = [MessageInfos.from_dict(msg) for msg in (messages or [])]
        self.mood = mood
        self._energy_level = energy_level
        self._pleasantness = pleasantness
    
    @property
    def energy_level(self) -> Optional[EnergyLevel]:
        """Get the energy level"""
        if self._energy_level:
            try:
                return EnergyLevel(self._energy_level)
            except ValueError:
                return None
        return None
    
    @energy_level.setter
    def energy_level(self, value: str):
        """Set the energy level"""
        self._energy_level = value
    
    @property
    def pleasantness(self) -> Optional[Pleasantness]:
        """Get the pleasantness level"""
        if self._pleasantness:
            try:
                return Pleasantness(self._pleasantness)
            except ValueError:
                return None
        return None
    
    @pleasantness.setter
    def pleasantness(self, value: str):
        """Set the pleasantness level"""
        self._pleasantness = value
    
    def get_mood_quadrant(self) -> Optional[MoodQuadrant]:
        """Get the mood quadrant based on energy and pleasantness"""
        if self.energy_level and self.pleasantness:
            return MoodQuadrant.from_dimensions(self.energy_level, self.pleasantness)
        return None
    
    def get_moods_for_current_quadrant(self) -> List[MoodType]:
        """Get all mood types that belong to the current quadrant"""
        quadrant = self.get_mood_quadrant()
        if not quadrant:
            return list(MoodType)  # Return all moods if no quadrant set
        
        return [mood for mood in MoodType if mood.quadrant == quadrant]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "BLEOId": self.BLEOId,
            "date": self.date,
            "messages": [msg.to_dict() for msg in self.messages],
            "mood": self.mood,
            "energy_level": self._energy_level,
            "pleasantness": self._pleasantness
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageDay':
        return cls(
            BLEOId=data.get("BLEOId"),
            date=data.get("date"),
            messages=data.get("messages", []),
            mood=data.get("mood"),
            energy_level=data.get("energy_level"),
            pleasantness=data.get("pleasantness")
        )