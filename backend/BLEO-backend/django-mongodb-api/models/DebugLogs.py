import re
from typing import Dict, Any, Optional
from datetime import datetime
from models.enums.UserType import UserType
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType

class DebugLogs:
    """Debug log entry with BLEOID validation when provided"""
    
    def __init__(
        self,
        message: str,
        type: str,
        code: int,
        id: int = 0,
        date: datetime = None,
        bleoid: Optional[str] = None,
        user_type: str = UserType.SYSTEM.value,
        error_source: Optional[str] = None
    ):
        # Validate and set required fields
        if id is None:
            raise ValueError("id cannot be None")
            
        self._id = id
        self.date = date or datetime.now()
        self.message = message
        self.type = type
        self.code = code
        self.user_type = user_type
        self.error_source = error_source
        self.bleoid = self._validate_and_normalize_bleoid(bleoid) if bleoid is not None else None
    
    @staticmethod
    def _validate_and_normalize_bleoid(bleoid: Optional[str]) -> Optional[str]:
        """Validate and normalize BLEOID format when provided"""
        if bleoid is None:
            return None
            
        if not bleoid or len(bleoid.strip()) == 0:
            raise ValueError("bleoid cannot be empty when provided")
        
        # Normalize to uppercase and strip whitespace
        normalized_bleoid = bleoid.strip().upper()
        
        # Validate format matches pattern ^[A-Z0-9]{6}$
        if not re.match(r'^[A-Z0-9]{6}$', normalized_bleoid):
            raise ValueError(f"bleoid must be exactly 6 uppercase letters/numbers. Invalid format: '{bleoid}'")
        
        return normalized_bleoid
    
    @property
    def id(self) -> int:
        """Get the log ID"""
        return self._id
    
    @id.setter
    def id(self, value: int):
        """Set the log ID with validation"""
        if value is None:
            raise ValueError("id cannot be None")
        self._id = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DebugLogs to dictionary"""
        return {
            "id": self.id,
            "date": self.date,
            "message": self.message,
            "type": self.type,
            "code": self.code,
            "bleoid": self.bleoid,
            "user_type": self.user_type,
            "error_source": self.error_source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DebugLogs':
        """Create DebugLogs from dictionary with validation"""
        # Validate required fields
        if 'id' not in data or data['id'] is None:
            raise ValueError("id is required and cannot be None")
        if 'date' not in data or data['date'] is None:
            raise ValueError("date is required and cannot be None")
            
        return cls(
            id=data['id'],
            date=data['date'],
            message=data.get('message', ''),
            type=data.get('type', LogType.INFO.value),
            code=data.get('code', 200),
            bleoid=data.get('bleoid'),  # Will be validated in __init__ if not None
            user_type=data.get('user_type', UserType.SYSTEM.value),
            error_source=data.get('error_source')
        )
    
    @classmethod
    def log_user_action(cls, bleoid: str, message: str, type: str, code: int) -> 'DebugLogs':
        """Create a user action log with BLEOID validation"""
        return cls(
            bleoid=bleoid,  # Will be validated
            message=message,
            type=type,
            code=code,
            user_type=UserType.USER.value
        )
    
    @classmethod
    def log_system_action(cls, message: str, type: str, code: int) -> 'DebugLogs':
        """Create a system action log (no BLEOID validation needed)"""
        return cls(
            bleoid=None,  # System logs don't need BLEOID
            message=message,
            type=type,
            code=code,
            user_type=UserType.SYSTEM.value
        )
    
    @classmethod
    def log_error(cls, message: str, code: int, bleoid: Optional[str] = None, 
                  error_source: Optional[str] = None) -> 'DebugLogs':
        """Create an error log with optional BLEOID validation"""
        user_type = UserType.USER.value if bleoid else UserType.SYSTEM.value
        return cls(
            bleoid=bleoid,  # Will be validated if provided
            message=message,
            type=LogType.ERROR.value,
            code=code,
            user_type=user_type,
            error_source=error_source
        )
    
    @classmethod
    def log_success(cls, message: str, code: int, bleoid: Optional[str] = None) -> 'DebugLogs':
        """Create a success log with optional BLEOID validation"""
        user_type = UserType.USER.value if bleoid else UserType.SYSTEM.value
        return cls(
            bleoid=bleoid,  # Will be validated if provided
            message=message,
            type=LogType.SUCCESS.value,
            code=code,
            user_type=user_type
        )
    
    def __str__(self) -> str:
        """String representation of DebugLogs"""
        return f"DebugLogs(id={self.id}, type={self.type}, code={self.code}, bleoid={self.bleoid})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"DebugLogs(id={self.id}, date={self.date}, message='{self.message}', "
                f"type='{self.type}', code={self.code}, bleoid='{self.bleoid}', "
                f"user_type='{self.user_type}', error_source='{self.error_source}')")