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
            params = db.find_one({"id": "app_parameters"})
            
            # If parameters don't exist yet, create default ones
            if not params:
                default_params = AppParameters()
                db.insert_one(default_params.to_dict())
                params = default_params.to_dict()
            
            # Convert ObjectId to string
            if "_id" in params:
                params["_id"] = str(params["_id"])
            
            # Serialize the parameters
            serializer = AppParametersSerializer(params)
            
            return BLEOResponse.success(
                data=serializer.data,
                message="Application parameters retrieved successfully"
            ).to_response()
            
        except Exception as e:
            Logger.server_error(f"Failed to retrieve app parameters: {str(e)}")
            return BLEOResponse.server_error(
                message=f"Failed to retrieve application parameters: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        """Update application parameters"""
        try:
            # Use serializer for validation
            serializer = AppParametersSerializer(data=request.data)
            if not serializer.is_valid():
                Logger.app_error(f"Invalid app parameters data: {serializer.errors}")
                return BLEOResponse.validation_error(
                    message="Invalid data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            db = MongoDB.get_instance().get_collection('AppParameters')
            
            # Check if parameters exist
            existing = db.find_one({"id": "app_parameters"})
            
            if existing:
                # Update existing parameters
                result = db.update_one(
                    {"id": "app_parameters"}, 
                    {"$set": validated_data}
                )
                
                if result.modified_count == 0:
                    return BLEOResponse.success(
                        message="No changes made to application parameters"
                    ).to_response(status.HTTP_200_OK)
            else:
                # Create new parameters
                default_params = AppParameters(**validated_data)
                db.insert_one(default_params.to_dict())
            
            # Get and return updated parameters
            updated_params = db.find_one({"id": "app_parameters"})
            
            if "_id" in updated_params:
                updated_params["_id"] = str(updated_params["_id"])
            
            # Log the update
            Logger.system_action(
                f"Application parameters updated: debug_level={updated_params.get('debug_level')}, " +
                f"app_version={updated_params.get('app_version')}",
                LogType.INFO.value,
                200
            )
            
            # Serialize the response
            response_serializer = AppParametersSerializer(updated_params)
            
            return BLEOResponse.success(
                data=response_serializer.data,
                message="Application parameters updated successfully"
            ).to_response()
            
        except Exception as e:
            Logger.server_error(f"Failed to update app parameters: {str(e)}")
            return BLEOResponse.server_error(
                message=f"Failed to update application parameters: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)