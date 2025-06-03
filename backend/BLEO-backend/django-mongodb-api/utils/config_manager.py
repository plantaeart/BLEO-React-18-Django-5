import os
from models.AppParameters import AppParameters
from models.enums.DebugType import DebugType
from utils.logger import Logger
from models.enums.LogType import LogType
from utils.parameter_manager import ParameterManager

class ConfigManager:
    """Configuration manager for app state tracking and parameter management"""
    
    @staticmethod
    def get_app_state():
        """Get current app state from MongoDB AppParameters collection"""
        try:
            # Import here to avoid circular import
            from utils.mongodb_utils import MongoDB
            # Get parameters from database
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            return ParameterManager.get_app_state_direct(db)
        except Exception as e:
            Logger.server_error(f"Error loading parameters from database: {str(e)}")
            # Return defaults if database access fails
            return {
                AppParameters.PARAM_APP_VERSION: "1.0.0",
                AppParameters.PARAM_DEBUG_LEVEL: DebugType.DEBUG.value,
            }
    
    @staticmethod
    def update_app_version(new_version):
        """Update app version in database"""
        try:
            # Import here to avoid circular import
            from utils.mongodb_utils import MongoDB
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            return ParameterManager.update_parameter_value(
                db, 
                AppParameters.PARAM_APP_VERSION, 
                new_version
            )
        except Exception as e:
            Logger.server_error(f"Error updating app version: {str(e)}")
            return False
    
    @staticmethod
    def update_debug_level(debug_level):
        """Update debug level in database"""
        try:
            # Import here to avoid circular import
            from utils.mongodb_utils import MongoDB
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            return ParameterManager.update_parameter_value(
                db, 
                AppParameters.PARAM_DEBUG_LEVEL, 
                debug_level
            )
        except Exception as e:
            Logger.server_error(f"Error updating debug level: {str(e)}")
            return False

    @staticmethod
    def get_parameter_value(param_name):
        """Get specific parameter value from database"""
        try:
            # Import here to avoid circular import
            from utils.mongodb_utils import MongoDB
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            return ParameterManager.get_parameter_value(db, param_name)
        except Exception as e:
            Logger.server_error(f"Error getting parameter {param_name}: {str(e)}")
            return None
    
    @staticmethod
    def update_parameter(param_name, param_value):
        """Update specific parameter in database"""
        if param_name == AppParameters.PARAM_APP_VERSION:
            return ConfigManager.update_app_version(param_value)
        elif param_name == AppParameters.PARAM_DEBUG_LEVEL:
            return ConfigManager.update_debug_level(param_value)
        else:
            try:
                # Import here to avoid circular import
                from utils.mongodb_utils import MongoDB
                db = MongoDB.get_instance().get_collection('AppParameters')
                
                return ParameterManager.update_parameter_value(db, param_name, param_value)
            except Exception as e:
                Logger.server_error(f"Error updating parameter {param_name}: {str(e)}")
                return False