from typing import List, Dict, Any
from datetime import datetime
from models import MessageInfos

class MessageDay:
    """Daily messages schema"""
    def __init__(
        self,
        BLEOId: int,
        date: datetime,
        messages: List[Dict[str, Any]] = None,
        mood: str = None
    ):
        self.BLEOId = BLEOId
        self.date = date or datetime.now().date()
        self.messages = [MessageInfos.from_dict(msg) for msg in (messages or [])]
        self.mood = mood
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "BLEOId": self.BLEOId,
            "date": self.date,
            "messages": [msg.to_dict() for msg in self.messages],
            "mood": self.mood
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageDay':
        return cls(
            BLEOId=data.get("BLEOId"),
            date=data.get("date"),
            messages=data.get("messages", []),
            mood=data.get("mood")
        )