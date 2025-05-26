from rest_framework.views import APIView
from rest_framework import status
from models.response.BLEOResponse import BLEOResponse
import jwt
from auth.jwt_auth import JWT_SECRET
from utils.mongodb_utils import MongoDB

class TokenValidationView(APIView):
    """API view for validating tokens and checking login status"""
    
    def post(self, request):
        """Check if a token is valid and return user information"""
        try:
            token = request.data.get('token')
            
            if not token:
                return BLEOResponse.validation_error(
                    message="Token is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Verify token
            try:
                # Decode token without verifying expiration first
                payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], options={"verify_exp": False})
                
                # Check if token is blacklisted
                db_blacklist = MongoDB.get_instance().get_collection('TokenBlacklist')
                if db_blacklist.find_one({"token": token}):
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
                    return BLEOResponse.success(
                        data={
                            "is_logged_in": False,
                            "reason": "expired",
                            "expiry": datetime.datetime.fromtimestamp(payload["exp"]).isoformat()
                        },
                        message="Token has expired - user is logged out"
                    ).to_response()
                
                # Token is valid - get user info
                db_users = MongoDB.get_instance().get_collection('Users')
                user = db_users.find_one({"BLEOId": payload["bleoid"]}, {"password": 0})
                
                if user:
                    user["_id"] = str(user["_id"])
                
                return BLEOResponse.success(
                    data={
                        "is_logged_in": True,
                        "user": user,
                        "token_expiry": datetime.datetime.fromtimestamp(payload["exp"]).isoformat()
                    },
                    message="Token is valid - user is logged in"
                ).to_response()
                
            except jwt.InvalidTokenError as e:
                return BLEOResponse.success(
                    data={
                        "is_logged_in": False,
                        "reason": "invalid",
                        "details": str(e)
                    },
                    message="Invalid token - user is logged out"
                ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to validate token: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)