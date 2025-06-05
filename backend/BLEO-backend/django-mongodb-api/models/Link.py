import re
from typing import Dict, Any
from datetime import datetime
from models.enums.ConnectionStatusType import ConnectionStatusType

class Link:
    """Connection between users"""
    def __init__(
        self,
        bleoidPartner1: str,
        bleoidPartner2: str,
        status: str = ConnectionStatusType.PENDING.value,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        # Add validation for both partners
        if not bleoidPartner1:
            raise ValueError("bleoidPartner1 cannot be null or empty")
        if not bleoidPartner2:
            raise ValueError("bleoidPartner2 cannot be null or empty")
        
        # Add BLEOID format validation and normalization
        self.bleoidPartner1 = self._validate_and_normalize_bleoid(bleoidPartner1, "bleoidPartner1")
        self.bleoidPartner2 = self._validate_and_normalize_bleoid(bleoidPartner2, "bleoidPartner2")
        
        self.status = status
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    @staticmethod
    def _validate_and_normalize_bleoid(bleoid: str, field_name: str) -> str:
        """Validate and normalize BLEOID format"""
        if not bleoid or len(bleoid.strip()) == 0:
            raise ValueError(f"{field_name} cannot be null or empty")
        
        # Normalize to uppercase and strip whitespace
        normalized_bleoid = bleoid.strip().upper()
        
        # Validate format matches pattern ^[A-Z0-9]{6}$
        if not re.match(r'^[A-Z0-9]{6}$', normalized_bleoid):
            raise ValueError(f"{field_name} must be exactly 6 uppercase letters/numbers. Invalid format: '{bleoid}'")
        
        return normalized_bleoid
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Link':
        """Create Link from dictionary with validation"""
        bleoidPartner1 = data.get("bleoidPartner1")
        bleoidPartner2 = data.get("bleoidPartner2")
        
        if not bleoidPartner1:
            raise ValueError("bleoidPartner1 is required")
        if not bleoidPartner2:
            raise ValueError("bleoidPartner2 is required")
            
        return cls(
            bleoidPartner1=bleoidPartner1,
            bleoidPartner2=bleoidPartner2,
            status=data.get("status", ConnectionStatusType.PENDING.value),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Link to dictionary"""
        return {
            "bleoidPartner1": self.bleoidPartner1,
            "bleoidPartner2": self.bleoidPartner2,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def __str__(self) -> str:
        """String representation of Link"""
        return f"Link({self.bleoidPartner1} <-> {self.bleoidPartner2}, status={self.status})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"Link(bleoidPartner1='{self.bleoidPartner1}', bleoidPartner2='{self.bleoidPartner2}', "
                f"status='{self.status}', created_at={self.created_at}, updated_at={self.updated_at})")