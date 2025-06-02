from typing import Dict, Any
from models.enums.DebugType import DebugType

class AppParameters:
    """
    Model for application parameters
    
    Each parameter is stored as a separate record with:
    - id: Unique integer identifier 
    - param_name: Parameter name/key
    - param_value: Parameter value (can be any type)
    """
    
    def __init__(
        self,
        param_name: str,
        param_value: Any,
        id: int = None
    ):
        self.id = id
        self.param_name = param_name
        self.param_value = param_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary for DB storage"""
        return {
            "id": self.id,
            "param_name": self.param_name,
            "param_value": self.param_value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppParameters':
        """Create object from dictionary"""
        return cls(
            id=data.get("id"),
            param_name=data.get("param_name"),
            param_value=data.get("param_value")
        )
    
    # Common parameter names - constants for consistency
    PARAM_DEBUG_LEVEL = "debug_level"
    PARAM_APP_VERSION = "app_version"