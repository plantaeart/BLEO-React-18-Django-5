from typing import Dict, Any, Optional
from datetime import datetime
from .enums.MessageType import MessageType

class MessageInfos:
    """Message information schema"""
    def __init__(
        self,
        id: int,
        title: str,
        text: str,
        type: MessageType,
        created_at: datetime = None,
    ):
        self.id = id  # ID is now a required integer
        self.title = title
        self.text = text
        self.type = type
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "type": self.type,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageInfos':
        return cls(
            id=data.get("id"),  # This must be provided by MessageDaysView
            title=data.get("title"),
            text=data.get("text"),
            type=data.get("type"),
            created_at=data.get("created_at")
        )