from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from models.response.BLEOResponse import BLEOResponse
from models.AppParameters import AppParameters
from api.serializers import AppParametersSerializer
from utils.logger import Logger
from models.enums.LogType import LogType

class AppParametersView(APIView):
    """API view for managing application parameters"""
    
    def get(self, request):
        """Get application parameters"""
        try:
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            # Get parameter name from query params if provided
            param_name = request.query_params.get('param_name')
            
            if param_name:
                # Get specific parameter by name
                param = db.find_one({"param_name": param_name})
                
                if not param:
                    return BLEOResponse.not_found(
                        message=f"Parameter '{param_name}' not found"
                    ).to_response(status.HTTP_404_NOT_FOUND)
                
                # Convert ObjectId to string
                if "_id" in param:
                    param["_id"] = str(param["_id"])
                
                return BLEOResponse.success(
                    data=param,
                    message=f"Parameter '{param_name}' retrieved successfully"
                ).to_response()
            else:
                # Get all parameters
                params = list(db.find())
                
                # Convert ObjectId to string for each parameter
                for param in params:
                    if "_id" in param:
                        param["_id"] = str(param["_id"])
                
                return BLEOResponse.success(
                    data={"parameters": params},
                    message="All application parameters retrieved successfully"
                ).to_response()
            
        except Exception as e:
            Logger.server_error(f"Failed to retrieve app parameters: {str(e)}")
            return BLEOResponse.server_error(
                message=f"Failed to retrieve application parameters: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        """Update application parameter"""
        try:
            param_name = request.data.get('param_name')
            param_value = request.data.get('param_value')
            
            if not param_name:
                return BLEOResponse.validation_error(
                    message="Parameter name is required",
                    errors={"param_name": "This field is required"}
                ).to_response(status.HTTP_400_BAD_REQUEST)
                
            if param_value is None:
                return BLEOResponse.validation_error(
                    message="Parameter value is required",
                    errors={"param_value": "This field is required"}
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            # Check if parameter exists
            existing = db.find_one({"param_name": param_name})
            
            if existing:
                # Update existing parameter
                result = db.update_one(
                    {"param_name": param_name}, 
                    {"$set": {"param_value": param_value}}
                )
                
                if result.modified_count == 0:
                    return BLEOResponse.success(
                        message=f"No changes made to parameter '{param_name}'"
                    ).to_response(status.HTTP_200_OK)
            else:
                # Create new parameter
                # Get next available ID
                next_id = 0
                highest_id = db.find_one(sort=[("id", -1)])
                if highest_id and "id" in highest_id:
                    next_id = highest_id["id"] + 1
                
                new_param = AppParameters(
                    id=next_id,
                    param_name=param_name,
                    param_value=param_value
                )
                
                db.insert_one(new_param.to_dict())
            
            # Get and return updated parameter
            updated_param = db.find_one({"param_name": param_name})
            
            if "_id" in updated_param:
                updated_param["_id"] = str(updated_param["_id"])
            
            # Special handling for specific parameters
            if param_name == AppParameters.PARAM_DEBUG_LEVEL:
                # Update config file
                from utils.config_manager import ConfigManager
                ConfigManager.update_debug_level(param_value)
            elif param_name == AppParameters.PARAM_APP_VERSION:
                # Update config file
                from utils.config_manager import ConfigManager
                ConfigManager.update_app_version(param_value)
            
            # Log the update
            Logger.system_action(
                f"Application parameter updated: {param_name}={param_value}",
                LogType.INFO.value,
                200
            )
            
            return BLEOResponse.success(
                data=updated_param,
                message=f"Parameter '{param_name}' updated successfully"
            ).to_response()
            
        except Exception as e:
            Logger.server_error(f"Failed to update app parameter: {str(e)}")
            return BLEOResponse.server_error(
                message=f"Failed to update application parameter: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)