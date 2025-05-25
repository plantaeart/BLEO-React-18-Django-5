from typing import Dict, Any
from datetime import datetime
from enums import MessageType

class MessageInfos:
    """Message information schema"""
    def __init__(
        self,
        title: str,
        text: str,
        type: MessageType,
        created_at: datetime = None
    ):
        self.title = title
        self.text = text
        self.type = type
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "text": self.text,
            "type": self.type,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageInfos':
        return cls(
            title=data.get("title"),
            text=data.get("text"),
            type=data.get("type"),
            created_at=data.get("created_at")
        )