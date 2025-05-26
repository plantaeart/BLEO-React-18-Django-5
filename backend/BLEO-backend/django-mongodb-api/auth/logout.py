from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from models.response.BLEOResponse import BLEOResponse
from datetime import datetime
import jwt
from auth.jwt_auth import JWT_SECRET

class LogoutView(APIView):
    """API view for user logout"""
    
    def post(self, request):
        """Invalidate the user's refresh token"""
        try:
            # Get the refresh token from request
            refresh_token = request.data.get("refresh")
            
            if not refresh_token:
                return BLEOResponse.validation_error(
                    message="Refresh token is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            try:
                # Verify and get expiration from token
                payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=['HS256'])
                exp_timestamp = payload['exp']
                exp_date = datetime.fromtimestamp(exp_timestamp)
            except:
                # If token is invalid, just return success (token can't be used anyway)
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
            
            return BLEOResponse.success(
                message="Logged out successfully"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Logout failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)