from enum import Enum

class ErrorSourceType(str, Enum):
    """Source of errors, either from server or application code"""
    SERVER = "server"
    APPLICATION = "application"