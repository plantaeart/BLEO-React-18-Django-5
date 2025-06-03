from models.AppParameters import AppParameters
from models.enums.DebugType import DebugType
from utils.logger import Logger
from models.enums.LogType import LogType

class ParameterManager:
    """Simple parameter management for AppParameters collection"""
    
    @staticmethod
    def get_debug_level():
        """Get current debug level from database"""
        try:
            from utils.mongodb_utils import MongoDB
            
            # Ensure MongoDB is initialized
            if not MongoDB._initialized:
                print("⚠️ MongoDB not initialized, using default debug level")
                return DebugType.DEBUG.value
                
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            param = db.find_one({"param_name": AppParameters.PARAM_DEBUG_LEVEL})
            return param.get("param_value", DebugType.DEBUG.value) if param else DebugType.DEBUG.value
        except Exception as e:
            Logger.server_error(f"Error getting debug level: {str(e)}")
            return DebugType.DEBUG.value
    
    @staticmethod
    def get_app_version():
        """Get current app version from database"""
        try:
            from utils.mongodb_utils import MongoDB
            
            # Ensure MongoDB is initialized
            if not MongoDB._initialized:
                print("⚠️ MongoDB not initialized, using default app version")
                return "1.0.0"
                
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            param = db.find_one({"param_name": AppParameters.PARAM_APP_VERSION})
            return param.get("param_value", "1.0.0") if param else "1.0.0"
        except Exception as e:
            Logger.server_error(f"Error getting app version: {str(e)}")
            return "1.0.0"
    
    @staticmethod
    def get_parameter_value(param_name, default_value=None):
        """Get any parameter value from database"""
        try:
            from utils.mongodb_utils import MongoDB
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            param = db.find_one({"param_name": param_name})
            return param.get("param_value", default_value) if param else default_value
        except Exception as e:
            Logger.server_error(f"Error getting parameter {param_name}: {str(e)}")
            return default_value
    
    @staticmethod
    def update_parameter_value(param_name, param_value):
        """Update parameter value in database"""
        try:
            from utils.mongodb_utils import MongoDB
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            # Update parameter in database
            result = db.update_one(
                {"param_name": param_name},
                {"$set": {"param_value": param_value}}
            )
            
            if result.matched_count == 0:
                # Create if it doesn't exist
                next_id = 0
                highest_id = db.find_one(sort=[("id", -1)])
                if highest_id and "id" in highest_id:
                    next_id = highest_id["id"] + 1
                    
                db.insert_one({
                    "id": next_id,
                    "param_name": param_name,
                    "param_value": param_value
                })
                
            Logger.system_action(
                f"Parameter {param_name} updated to {param_value}",
                LogType.INFO.value,
                200
            )
            return True
        except Exception as e:
            Logger.server_error(f"Error updating parameter {param_name}: {str(e)}")
            return False