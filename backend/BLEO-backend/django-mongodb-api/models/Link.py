from typing import Dict, Any, Optional
from datetime import datetime
from .enums.ConnectionStatusType import ConnectionStatusType

class Link:
    """Connection between users"""
    def __init__(
        self,
        BLEOIdPartner1: str,
        BLEOIdPartner2: Optional[str] = None,
        status: str = ConnectionStatusType.PENDING.value,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.BLEOIdPartner1 = BLEOIdPartner1
        self.BLEOIdPartner2 = BLEOIdPartner2
        self.status = status
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "BLEOIdPartner1": self.BLEOIdPartner1,
            "BLEOIdPartner2": self.BLEOIdPartner2,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }