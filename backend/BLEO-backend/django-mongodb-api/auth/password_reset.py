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
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType
from utils.privacy_utils import PrivacyUtils

class PasswordResetRequestView(APIView):
    """Request a password reset"""
    
    def post(self, request):
        try:
            # Log request
            Logger.debug_system_action(
                "Password reset request received",
                LogType.INFO.value,
                200
            )
            
            email = request.data.get('email')
            if not email:
                # Log validation error
                Logger.debug_error(
                    "Password reset failed: Email is missing",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Email is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Mask email for logging
            masked_email = PrivacyUtils.mask_email(email)
            
            # Log reset attempt
            Logger.debug_system_action(
                f"Processing password reset for: {masked_email}",
                LogType.INFO.value,
                200
            )
            
            db = MongoDB.get_instance().get_collection('Users')
            user = db.find_one({"email": email})
            
            if not user:
                # Log user not found - but don't reveal this in response
                Logger.debug_error(
                    f"Password reset user not found: {masked_email}",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                # Don't reveal if user exists or not for security
                return BLEOResponse.success(
                    message="If your email exists, you'll receive reset instructions"
                ).to_response()
            
            # Get user's bleoid for logging
            bleoid = user.get('bleoid')
            
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
            
            # Log token creation
            Logger.debug_user_action(
                bleoid,
                f"Password reset token created for {masked_email}, expires in 24 hours",
                LogType.INFO.value,
                200
            )
            
            # Send email
            reset_url = f"https://yourdomain.com/reset-password?token={token}"
            try:
                send_mail(
                    'Password Reset Request',
                    f'Click the following link to reset your password: {reset_url}',
                    'noreply@yourdomain.com',
                    [email],
                    fail_silently=False,
                )
                
                # Log email sent
                Logger.debug_user_action(
                    bleoid,
                    f"Password reset email sent to {masked_email}",
                    LogType.SUCCESS.value,
                    200
                )
            except Exception as email_error:
                # Log email error
                Logger.debug_error(
                    f"Failed to send password reset email to {masked_email}: {str(email_error)}",
                    500,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                # Continue execution - don't reveal email send failure
            
            return BLEOResponse.success(
                message="If your email exists, you'll receive reset instructions"
            ).to_response()
            
        except Exception as e:
            # Log server error
            Logger.debug_error(
                f"Password reset request failed: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to process password reset request: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetConfirmView(APIView):
    """Confirm a password reset"""
    
    def post(self, request):
        try:
            # Log request - don't log the token itself
            Logger.debug_system_action(
                "Password reset confirmation request received",
                LogType.INFO.value,
                200
            )
            
            token = request.data.get('token')
            new_password = request.data.get('password')
            
            if not token or not new_password:
                # Log validation error
                Logger.debug_error(
                    "Password reset confirmation failed: Token or password is missing",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Token and password are required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Validate password strength
            if len(new_password) < 8:
                # Log validation error
                Logger.debug_error(
                    "Password reset confirmation failed: Password too short",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
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
                # Log invalid token error
                Logger.debug_error(
                    "Password reset confirmation failed: Invalid or expired token",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid or expired token"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get email and mask it for logging
            email = reset.get("email")
            masked_email = PrivacyUtils.mask_email(email)
            
            # Get user from DB to find bleoid
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({"email": email})
            bleoid = user.get('bleoid') if user else None
            
            # Log valid token
            Logger.debug_system_action(
                f"Valid password reset token for {masked_email}",
                LogType.INFO.value,
                200
            )
            
            # Update user's password
            result = db_users.update_one(
                {"email": email},
                {"$set": {"password": make_password(new_password)}}
            )
            
            if result.modified_count == 0:
                # Log update error
                Logger.debug_error(
                    f"Failed to update password for {masked_email}",
                    500,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.server_error(
                    message="Failed to update password"
                ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Delete used token
            db_reset.delete_one({"token": token})
            
            # Log success
            Logger.debug_user_action(
                bleoid,
                f"Password reset successful for {masked_email}",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                message="Password updated successfully"
            ).to_response()
            
        except Exception as e:
            # Log server error
            Logger.debug_error(
                f"Password reset confirmation failed: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to reset password: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)