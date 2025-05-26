from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from models.response.BLEOResponse import BLEOResponse

class EmailVerificationView(APIView):
    """API view for manual email verification (admin only)"""
    
    def post(self, request):
        """Admin-only: Manually verify a user's email"""
        try:
            # This would typically be protected by admin authentication
            email = request.data.get('email')
            
            if not email:
                return BLEOResponse.validation_error(
                    message="Email is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Update user's email verification status
            db = MongoDB.get_instance().get_collection('Users')
            result = db.update_one(
                {"mail": email},
                {"$set": {"email_verified": True}}
            )
            
            if result.modified_count == 0:
                return BLEOResponse.not_found(
                    message="User not found or already verified"
                ).to_response(status.HTTP_404_NOT_FOUND)
                
            return BLEOResponse.success(
                message="Email verified successfully"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Email verification failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        # Stub for API compatibility
        return self.post(request)