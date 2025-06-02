from models.DebugLogs import DebugLogs
from utils.mongodb_utils import MongoDB
from models.enums.LogType import LogType
from models.enums.UserType import UserType
from models.enums.ErrorSourceType import ErrorSourceType
from models.enums.DebugType import DebugType
import traceback
from datetime import datetime
from models.AppParameters import AppParameters

class Logger:
    """Utility class for logging actions to MongoDB"""
    
    @staticmethod
    def _should_log():
        """Check if debug logging is enabled in AppParameters"""
        try:
            db = MongoDB.get_instance().get_collection('AppParameters')
            debug_param = db.find_one({"param_name": AppParameters.PARAM_DEBUG_LEVEL})
            
            # Default to logging unless explicitly set to NO_DEBUG
            if not debug_param:
                return True
                
            return debug_param.get('param_value') == DebugType.DEBUG.value
        except Exception as e:
            # If there's an error checking debug status, default to logging
            print(f"Error checking debug status: {str(e)}")
            return True
    
    @staticmethod
    def _get_next_id():
        """Get next ID using max(id) + 1"""
        try:
            db = MongoDB.get_instance().get_collection('DebugLogs')
            # Find the document with the highest ID
            result = db.find_one(sort=[("id", -1)])
            
            if result and "id" in result:
                return result["id"] + 1
            else:
                return 1
        except Exception as e:
            print(f"Error getting next ID: {str(e)}")
            return 1
    
    @staticmethod
    def _save_log(log_entry):
        """Save a log entry to the database if debug is enabled"""
        # Only log if debug is enabled
        if not Logger._should_log():
            return None
            
        try:
            # Set the ID to max(id) + 1 if it's the placeholder value
            if log_entry.id == 0:
                log_entry.id = Logger._get_next_id()
                
            db = MongoDB.get_instance().get_collection('DebugLogs')
            result = db.insert_one(log_entry.to_dict())
            return result.inserted_id
        except Exception as e:
            print(f"Error logging to database: {str(e)}")
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def user_action(bleoid, message, log_type=LogType.INFO.value, code=200):
        """Log a user action"""
        log_entry = DebugLogs(
            message=message,
            type=log_type,
            code=code,
            BLEOId=bleoid,
            user_type=UserType.USER.value
        )
        return Logger._save_log(log_entry)
    
    @staticmethod
    def system_action(message, log_type=LogType.INFO.value, code=200):
        """Log a system action"""
        log_entry = DebugLogs(
            message=message,
            type=log_type,
            code=code,
            user_type=UserType.SYSTEM.value
        )
        return Logger._save_log(log_entry)
    
    @staticmethod
    def error(message, code=500, bleoid=None, error_source=None):
        """Log an error"""
        user_type = UserType.USER.value if bleoid else UserType.SYSTEM.value
        log_entry = DebugLogs(
            message=message,
            type=LogType.ERROR.value,
            code=code,
            BLEOId=bleoid,
            user_type=user_type,
            error_source=error_source
        )
        return Logger._save_log(log_entry)
    
    @staticmethod
    def server_error(message, code=500, bleoid=None):
        """Log a server-side error"""
        return Logger.error(
            message=message,
            code=code,
            bleoid=bleoid,
            error_source=ErrorSourceType.SERVER.value
        )
    
    @staticmethod
    def app_error(message, code=400, bleoid=None):
        """Log an application-side error"""
        return Logger.error(
            message=message,
            code=code,
            bleoid=bleoid,
            error_source=ErrorSourceType.SERVER.value
        )
    
    @staticmethod
    def debug_user_action(bleoid, message, log_type=LogType.INFO.value, code=200):
        """Log a user action only if debug is enabled"""
        if Logger._should_log():
            return Logger.user_action(bleoid, message, log_type, code)
        return None
    
    @staticmethod
    def debug_system_action(message, log_type=LogType.INFO.value, code=200):
        """Log a system action only if debug is enabled"""
        if Logger._should_log():
            return Logger.system_action(message, log_type, code)
        return None
        
    @staticmethod
    def debug_error(message, code=500, bleoid=None, error_source=None):
        """Log an error only if debug is enabled"""
        if Logger._should_log():
            return Logger.error(message, code, bleoid, error_source)
        return None