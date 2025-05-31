from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from models.response.BLEOResponse import BLEOResponse
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType

class EmailVerificationView(APIView):
    """API view for manual email verification (admin only)"""
    
    def post(self, request):
        """Admin-only: Manually verify a user's email"""
        try:
            # Log request
            Logger.debug_system_action(
                "Admin email verification request received",
                LogType.INFO.value,
                200
            )
            
            # This would typically be protected by admin authentication
            email = request.data.get('email')
            
            if not email:
                # Log validation error
                Logger.debug_error(
                    "Email verification failed: Email parameter missing",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Email is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Mask email for logging
            masked_email = self._mask_email(email)
            
            # Log verification attempt
            Logger.debug_system_action(
                f"Attempting to verify email for: {masked_email}",
                LogType.INFO.value,
                200
            )
            
            # Update user's email verification status
            db = MongoDB.get_instance().get_collection('Users')
            result = db.update_one(
                {"email": email},
                {"$set": {"email_verified": True}}
            )
            
            if result.modified_count == 0:
                # Log not found error
                Logger.debug_error(
                    f"Email verification failed: User not found or already verified for {masked_email}",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.not_found(
                    message="User not found or already verified"
                ).to_response(status.HTTP_404_NOT_FOUND)
                
            # Log success
            Logger.debug_system_action(
                f"Email verified successfully for: {masked_email}",
                LogType.SUCCESS.value,
                200
            )
                
            return BLEOResponse.success(
                message="Email verified successfully"
            ).to_response()
            
        except Exception as e:
            # Log error
            Logger.debug_error(
                f"Email verification failed with error: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Email verification failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        # Log request
        Logger.debug_system_action(
            "Admin email verification request received (PUT)",
            LogType.INFO.value,
            200
        )
        
        # Stub for API compatibility
        return self.post(request)
    
    def _mask_email(self, email):
        """Mask email for logging purposes"""
        try:
            if not email or '@' not in email:
                return "invalid-email"
                
            parts = email.split('@')
            username = parts[0]
            domain = parts[1]
            
            if len(username) <= 3:
                masked_username = username[0] + '*' * (len(username) - 1)
            else:
                masked_username = username[0:2] + '*' * (len(username) - 3) + username[-1]
                
            return f"{masked_username}@{domain}"
        except:
            return "invalid-email"