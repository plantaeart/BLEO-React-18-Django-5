from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from models.response.BLEOResponse import BLEOResponse
from datetime import datetime
import jwt
from auth.jwt_auth import JWT_SECRET
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType

class LogoutView(APIView):
    """API view for user logout"""
    
    def post(self, request):
        """Invalidate the user's refresh token"""
        try:
            # Log request - don't log the token itself
            Logger.debug_system_action(
                "Logout request received",
                LogType.INFO.value,
                200
            )
            
            # Get the refresh token from request
            refresh_token = request.data.get("refresh")
            
            if not refresh_token:
                # Log validation error
                Logger.debug_error(
                    "Logout failed: Refresh token is missing",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Refresh token is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            try:
                # Verify and get expiration from token
                payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=['HS256'])
                exp_timestamp = payload['exp']
                exp_date = datetime.fromtimestamp(exp_timestamp)
                
                # Get bleoid for logging
                bleoid = payload.get('bleoid')
                
                # Log token validation success
                Logger.debug_user_action(
                    bleoid,
                    "Refresh token validated for logout",
                    LogType.INFO.value,
                    200
                )
            except jwt.ExpiredSignatureError:
                # Log expired token
                Logger.debug_error(
                    "Logout process: Token already expired",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                # If token is already expired, just return success
                return BLEOResponse.success(
                    message="Logged out successfully"
                ).to_response()
            except jwt.InvalidTokenError as e:
                # Log invalid token
                Logger.debug_error(
                    f"Logout process: Invalid token - {str(e)}",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                # If token is invalid, just return success (token can't be used anyway)
                return BLEOResponse.success(
                    message="Logged out successfully"
                ).to_response()
            except Exception as token_error:
                # Log token error
                Logger.debug_error(
                    f"Logout token error: {str(token_error)}",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                # If there's any issue with the token, just return success
                return BLEOResponse.success(
                    message="Logged out successfully"
                ).to_response()
            
            # Add token to blacklist in MongoDB
            db = MongoDB.get_instance().get_collection('TokenBlacklist')
            
            # Store the blacklisted token with expiry time
            db.insert_one({
                "token": refresh_token,
                "created_at": datetime.now(),
                "expires_at": exp_date
            })
            
            # Log success
            Logger.debug_user_action(
                bleoid,
                "User logged out successfully - token blacklisted",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                message="Logged out successfully"
            ).to_response()
            
        except Exception as e:
            # Log server error
            Logger.debug_error(
                f"Logout failed with error: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Logout failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)