from enum import Enum

class LogType(str, Enum):
    """Log types for categorizing entries"""
    ERROR = "error"
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    AUTH = "auth"
    DATABASE = "database"
    API = "api"