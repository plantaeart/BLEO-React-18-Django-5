from typing import Dict, Any
from models.enums.DebugType import DebugType

class AppParameters:
    """
    Model for application parameters
    
    Contains global settings for the application like debug level and version
    """
    
    def __init__(
        self,
        debug_level: str = DebugType.DEBUG.value,
        app_version: str = "1.0.0",
        id: str = "app_parameters"
    ):
        self.id = id
        self.debug_level = debug_level
        self.app_version = app_version
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary for DB storage"""
        return {
            "id": self.id,
            "debug_level": self.debug_level,
            "app_version": self.app_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppParameters':
        """Create object from dictionary"""
        return cls(
            id=data.get("id", "app_parameters"),
            debug_level=data.get("debug_level", DebugType.DEBUG.value),
            app_version=data.get("app_version", "1.0.0"),
        )