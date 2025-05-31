from enum import Enum

class DebugType(str, Enum):
    """Debug types"""
    DEBUG = "DEBUG"
    NO_DEBUG = "NO_DEBUG"