from typing import Dict, Any, Optional
from datetime import datetime
from models.enums.UserType import UserType
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType

class DebugLogs:
    """
    Model for system and user action logs
    
    Note: id and date fields are required and cannot be null or None.
    - id defaults to 0 and should be replaced with a real ID before saving to DB
    - date defaults to the current date/time if not specified
    """
    
    def __init__(
        self,
        message: str,
        type: str,
        code: int,
        id: int = 0,
        date: datetime = None,
        BLEOId: str = None,
        user_type: str = UserType.SYSTEM.value,
        error_source: str = None,
    ):
        if id is None:
            raise ValueError("id cannot be None in DebugLogs")
        
        self._id = id 
        self.message = message
        self.type = type
        self.code = code
        self.BLEOId = BLEOId
        self.user_type = user_type
        self.error_source = error_source
        self._date = datetime.now() if date is None else date
    
    @property
    def id(self) -> int:
        """Get the ID of the log entry"""
        return self._id

    @id.setter
    def id(self, value: int):
        """Set the ID of the log entry"""
        if value is None:
            raise ValueError("id cannot be None in DebugLogs")
        self._id = value
    
    @property
    def date(self) -> datetime:
        """Get the date and time of the log entry"""
        return self._date
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary for DB storage"""
        return {
            "id": self.id,
            "date": self.date,
            "message": self.message,
            "type": self.type,
            "code": self.code,
            "BLEOId": self.BLEOId,
            "user_type": self.user_type,
            "error_source": self.error_source,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DebugLogs':
        """Create object from dictionary"""

        if "id" not in data or data["id"] is None:
            raise ValueError("id cannot be null in DebugLogs")
            
        if "date" not in data or data["date"] is None:
            raise ValueError("date cannot be null in DebugLogs")
            
        return cls(
            id=data["id"],
            date=data["date"],
            message=data.get("message", ""),
            type=data.get("type", ""),
            code=data.get("code", 0),
            BLEOId=data.get("BLEOId"),
            user_type=data.get("user_type", UserType.SYSTEM.value),
            error_source=data.get("error_source"),
        )
    
    @classmethod
    def log_user_action(cls, BLEOId: str, message: str, type: str, code: int) -> 'DebugLogs':
        """Helper method to quickly log a user action"""
        return cls(
            id=0,
            date=datetime.now(),
            BLEOId=BLEOId,
            user_type=UserType.USER.value,
            message=message,
            type=type,
            code=code
        )
    
    @classmethod
    def log_system_action(cls, message: str, type: str, code: int) -> 'DebugLogs':
        """Helper method to quickly log a system action"""
        return cls(
            id=0,
            date=datetime.now(),
            user_type=UserType.SYSTEM.value,
            message=message,
            type=type,
            code=code
        )
    
    @classmethod
    def log_error(cls, message: str, code: int, BLEOId: str = None, error_source: str = None) -> 'DebugLogs':
        """Helper method to log an error"""
        user_type = UserType.USER.value if BLEOId else UserType.SYSTEM.value
        return cls(
            id=0,
            date=datetime.now(),
            BLEOId=BLEOId,
            user_type=user_type,
            message=message,
            type=LogType.ERROR.value,
            code=code,
            error_source=error_source,
        )
    
    @classmethod
    def log_success(cls, message: str, code: int, BLEOId: str = None) -> 'DebugLogs':
        """Helper method to log a success"""
        user_type = UserType.USER.value if BLEOId else UserType.SYSTEM.value
        return cls(
            id=0,
            date=datetime.now(),
            BLEOId=BLEOId,
            user_type=user_type,
            message=message,
            type=LogType.SUCCESS.value,
            code=code
        )