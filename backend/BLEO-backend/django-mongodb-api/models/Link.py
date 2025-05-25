from typing import Dict, Any, Optional
from datetime import datetime

class Link:
    """Link schema for connecting partners"""
    def __init__(
        self,
        BLEOIdPartner1: int,
        BLEOIdPartner2: Optional[int] = None,
        created_at: datetime = None
    ):
        self.BLEOIdPartner1 = BLEOIdPartner1
        self.BLEOIdPartner2 = BLEOIdPartner2
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "BLEOIdPartner1": self.BLEOIdPartner1,
            "BLEOIdPartner2": self.BLEOIdPartner2,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Link':
        return cls(
            BLEOIdPartner1=data.get("BLEOIdPartner1"),
            BLEOIdPartner2=data.get("BLEOIdPartner2"),
            created_at=data.get("created_at")
        )