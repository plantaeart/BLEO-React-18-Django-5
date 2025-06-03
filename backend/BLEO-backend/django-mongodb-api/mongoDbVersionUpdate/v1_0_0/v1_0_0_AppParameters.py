from models.AppParameters import AppParameters
from utils.mongodb_utils import MongoDB
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.DebugType import DebugType

def update_app_parameters(app_state=None):
    """Update or create default app parameters if they don't exist"""
    try:
        # Connect to MongoDB
        db = MongoDB.get_instance().get_collection('AppParameters')
        
        # Use provided app_state or get default values
        if not app_state:
            app_state = {
                AppParameters.PARAM_DEBUG_LEVEL: DebugType.NO_DEBUG.value,
                AppParameters.PARAM_APP_VERSION: "1.0.0"
            }
            
        # Define default parameters
        DEFAULT_PARAMS = [
            {
                'id': 0,
                'param_name': AppParameters.PARAM_DEBUG_LEVEL,
                'param_value': app_state.get(AppParameters.PARAM_DEBUG_LEVEL, DebugType.NO_DEBUG.value)
            },
            {
                'id': 1,
                'param_name': AppParameters.PARAM_APP_VERSION, 
                'param_value': app_state.get(AppParameters.PARAM_APP_VERSION, "1.0.0")
            }
        ]
        
        updated_count = 0
        created_count = 0
        
        # Check and update/create each parameter
        for param in DEFAULT_PARAMS:
            # Check if parameter exists
            existing = db.find_one({"param_name": param['param_name']})
            
            if existing:
                # Update if value is different
                if existing['param_value'] != param['param_value']:
                    db.update_one(
                        {"param_name": param['param_name']},
                        {"$set": {"param_value": param['param_value']}}
                    )
                    updated_count += 1
                    Logger.system_action(
                        f"[v1.0.0] Updated parameter: {param['param_name']}={param['param_value']}",
                        LogType.INFO.value,
                        200
                    )
            else:
                # Create new parameter
                db.insert_one(param)
                created_count += 1
                Logger.system_action(
                    f"[v1.0.0] Created parameter: {param['param_name']}={param['param_value']}",
                    LogType.INFO.value,
                    201
                )
        
        return {
            "success": True,
            "created": created_count,
            "updated": updated_count,
            "message": f"App parameters initialized in v1.0.0: {created_count} created, {updated_count} updated"
        }
        
    except Exception as e:
        Logger.server_error(f"[v1.0.0] Failed to initialize app parameters: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to initialize app parameters in v1.0.0"
        }

# This function can be called during version updates
def run_update(app_state):
    """Run the app parameters update"""
    print("Initializing default application parameters for version 1.0.0...")
    result = update_app_parameters(app_state)
    
    if result["success"]:
        print(f"✅ [v1.0.0] {result['message']}")
    else:
        print(f"❌ [v1.0.0] {result['message']}: {result['error']}")
    
    return result["success"]