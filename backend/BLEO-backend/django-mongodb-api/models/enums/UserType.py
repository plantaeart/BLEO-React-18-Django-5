from enum import Enum

class UserType(str, Enum):
    """User types for debug logs"""
    USER = "user"
    SYSTEM = "system"