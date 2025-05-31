from rest_framework.views import APIView
from rest_framework import status
from models.response.BLEOResponse import BLEOResponse
import jwt
from auth.jwt_auth import JWT_SECRET
from utils.mongodb_utils import MongoDB
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType

class TokenValidationView(APIView):
    """API view for validating tokens and checking login status"""
    
    def post(self, request):
        """Check if a token is valid and return user information"""
        try:
            # Log request, we don't log the token itself
            Logger.debug_system_action(
                "Token validation request received",
                LogType.INFO.value,
                200
            )
            
            token = request.data.get('token')
            
            if not token:
                # Log validation error
                Logger.debug_error(
                    "Token validation failed: Token is missing",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Token is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Verify token
            try:
                # Decode token without verifying expiration first
                payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], options={"verify_exp": False})
                bleoid = payload.get("bleoid", "unknown")
                
                # Log token decode success
                Logger.debug_system_action(
                    f"Token decoded successfully for BLEOId: {bleoid}",
                    LogType.INFO.value,
                    200
                )
                
                # Check if token is blacklisted
                db_blacklist = MongoDB.get_instance().get_collection('TokenBlacklist')
                if db_blacklist.find_one({"token": token}):
                    # Log blacklisted token
                    Logger.debug_error(
                        f"Token validation failed: Token is blacklisted for BLEOId: {bleoid}",
                        401,
                        bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.success(
                        data={
                            "is_logged_in": False,
                            "reason": "blacklisted"
                        },
                        message="Token is blacklisted - user is logged out"
                    ).to_response()
                
                # Check if token has expired
                import datetime
                current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
                if payload["exp"] < current_timestamp:
                    # Calculate expiry time for logging
                    expires_str = datetime.datetime.fromtimestamp(payload["exp"]).isoformat()
                    
                    # Log token expired
                    Logger.debug_error(
                        f"Token validation failed: Token expired at {expires_str} for BLEOId: {bleoid}",
                        401,
                        bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.success(
                        data={
                            "is_logged_in": False,
                            "reason": "expired",
                            "expiry": expires_str
                        },
                        message="Token has expired - user is logged out"
                    ).to_response()
                
                # Token is valid - get user info
                db_users = MongoDB.get_instance().get_collection('Users')
                user = db_users.find_one({"BLEOId": bleoid}, {"password": 0})
                
                if user:
                    user["_id"] = str(user["_id"])
                    
                    # Log valid token
                    Logger.debug_user_action(
                        bleoid,
                        "Token validation successful - user is logged in",
                        LogType.SUCCESS.value,
                        200
                    )
                    
                    return BLEOResponse.success(
                        data={
                            "is_logged_in": True,
                            "user": user,
                            "token_expiry": datetime.datetime.fromtimestamp(payload["exp"]).isoformat()
                        },
                        message="Token is valid - user is logged in"
                    ).to_response()
                else:
                    # Log user not found
                    Logger.debug_error(
                        f"Token validation failed: User not found for BLEOId: {bleoid}",
                        404,
                        bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    return BLEOResponse.success(
                        data={
                            "is_logged_in": False,
                            "reason": "user_not_found"
                        },
                        message="User not found"
                    ).to_response()
                
            except jwt.InvalidTokenError as e:
                # Log invalid token
                Logger.debug_error(
                    f"Token validation failed: Invalid token - {str(e)}",
                    401,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.success(
                    data={
                        "is_logged_in": False,
                        "reason": "invalid",
                        "details": str(e)
                    },
                    message="Invalid token - user is logged out"
                ).to_response()
            
        except Exception as e:
            # Log server error
            Logger.debug_error(
                f"Token validation failed with error: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to validate token: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)