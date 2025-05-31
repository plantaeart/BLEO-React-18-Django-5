"""
Application state tracking configuration

This file tracks the current app version and collection recreation history.
It's used to initialize the AppParameters collection and track database changes.
"""
from datetime import datetime
from models.enums.DebugType import DebugType

# Current application version
APP_VERSION = "1.0.0"

# Debug level
# Options: "DEBUG" or "NO_DEBUG"
DEBUG_LEVEL = DebugType.NO_DEBUG.value