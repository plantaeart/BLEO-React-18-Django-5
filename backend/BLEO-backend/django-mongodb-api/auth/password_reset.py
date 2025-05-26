# Create auth/password_reset.py
from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from models.response.BLEOResponse import BLEOResponse
from django.core.mail import send_mail
import secrets
import string
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password

class PasswordResetRequestView(APIView):
    """Request a password reset"""
    
    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return BLEOResponse.validation_error(
                    message="Email is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            db = MongoDB.get_instance().get_collection('Users')
            user = db.find_one({"email": email})
            
            if not user:
                # Don't reveal if user exists or not for security
                return BLEOResponse.success(
                    message="If your email exists, you'll receive reset instructions"
                ).to_response()
            
            # Generate reset token
            token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))
            expiry = datetime.now() + timedelta(hours=24)
            
            # Store token in database
            db_reset = MongoDB.get_instance().get_collection('PasswordResets')
            db_reset.insert_one({
                "email": email,
                "token": token,
                "expires": expiry
            })
            
            # Send email
            reset_url = f"https://yourdomain.com/reset-password?token={token}"
            send_mail(
                'Password Reset Request',
                f'Click the following link to reset your password: {reset_url}',
                'noreply@yourdomain.com',
                [email],
                fail_silently=False,
            )
            
            return BLEOResponse.success(
                message="If your email exists, you'll receive reset instructions"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to process password reset request: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetConfirmView(APIView):
    """Confirm a password reset"""
    
    def post(self, request):
        try:
            token = request.data.get('token')
            new_password = request.data.get('password')
            
            if not token or not new_password:
                return BLEOResponse.validation_error(
                    message="Token and password are required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Validate password strength
            if len(new_password) < 8:
                return BLEOResponse.validation_error(
                    message="Password must be at least 8 characters long"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Find token
            db_reset = MongoDB.get_instance().get_collection('PasswordResets')
            reset = db_reset.find_one({
                "token": token,
                "expires": {"$gt": datetime.now()}
            })
            
            if not reset:
                return BLEOResponse.validation_error(
                    message="Invalid or expired token"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Update user's password
            db_users = MongoDB.get_instance().get_collection('Users')
            result = db_users.update_one(
                {"email": reset["email"]},
                {"$set": {"password": make_password(new_password)}}
            )
            
            if result.modified_count == 0:
                return BLEOResponse.server_error(
                    message="Failed to update password"
                ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Delete used token
            db_reset.delete_one({"token": token})
            
            return BLEOResponse.success(
                message="Password updated successfully"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Failed to reset password: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)