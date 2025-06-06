from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from models.response.BLEOResponse import BLEOResponse
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType
from utils.privacy_utils import PrivacyUtils
from services.EmailService import EmailService
from models.PasswordResets import PasswordResets
from api.serializers import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetResponseSerializer,
    PasswordResetTokenValidationSerializer  # Add this import
)
from django.contrib.auth.hashers import make_password
from datetime import datetime, timedelta, timezone
import jwt
import uuid
import os
from utils.validation_patterns import ValidationRules

class PasswordResetRequestView(APIView):
    """Request a password reset - follows email verification pattern"""
    
    def post(self, request):
        """Send password reset token to user"""
        try:
            # Validate request data using serializer
            serializer = PasswordResetRequestSerializer(data=request.data)
            if not serializer.is_valid():
                Logger.debug_error(
                    f"Password reset request validation failed: {serializer.errors}",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid request data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get validated data from serializer
            validated_data = serializer.validated_data
            email = validated_data['email']
            masked_email = PrivacyUtils.mask_email(email)
            
            # Log request
            Logger.debug_system_action(
                f"Password reset request for {masked_email}",
                LogType.INFO.value,
                200
            )
            
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({'email': email})
            
            if not user:
                Logger.debug_error(
                    f"Password reset failed: User not found for {masked_email}",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                # Security: Don't reveal if user exists or not
                # Use response serializer for consistent response
                response_data = {
                    'email_sent': False,
                    'message': "If your email exists, you'll receive reset instructions"
                }
                
                return BLEOResponse.success(
                    message="If your email exists, you'll receive reset instructions",
                    data=response_data
                ).to_response(status.HTTP_200_OK)
            
            bleoid = user.get('bleoid')
            
            # Generate JWT token (same as email verification)
            payload = {
                'bleoid': bleoid,
                'email': email,
                'type': 'password_reset',
                'jti': str(uuid.uuid4()),
                'iat': datetime.now(timezone.utc).timestamp(),
                'exp': (datetime.now(timezone.utc) + timedelta(hours=ValidationRules.JWT_EXPIRATION['password_reset'])).timestamp()
            }
            
            reset_token = jwt.encode(
                payload, 
                os.getenv('JWT_SECRET'), 
                algorithm='HS256'
            )
            
            # Create PasswordResets model instance
            password_reset = PasswordResets(
                bleoid=bleoid,
                email=email,
                token=reset_token,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=ValidationRules.JWT_EXPIRATION['password_reset']),
                used=False,
                attempts=0
            )
            
            # Store reset token in database using the model
            db_password_resets = MongoDB.get_instance().get_collection('PasswordResets')
            
            # Remove any existing reset records for this email
            db_password_resets.delete_many({'email': email})
            
            # Insert new reset record using the model
            db_password_resets.insert_one(password_reset.to_dict())
            
            # Send reset email using EmailService
            try:
                email_sent = EmailService.send_password_reset_email(
                    email=email,
                    reset_token=reset_token,
                    user_name=user.get('userName', 'User')
                )
                
                if not email_sent:
                    raise Exception("Email service returned False")
                    
            except Exception as e:
                Logger.debug_error(
                    f"Failed to send password reset email to {masked_email}: {str(e)}",
                    500,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.server_error(
                    message="Failed to send reset email. Please try again later."
                ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Use response serializer for consistent response
            response_data = {
                'email_sent': True,
                'reset_token_created': True,
                'expires_in_hours': ValidationRules.JWT_EXPIRATION['password_reset'],
                'message': "If your email exists, you'll receive reset instructions"
            }
            
            # Log success
            Logger.debug_system_action(
                f"Password reset email sent successfully to {masked_email}",
                LogType.INFO.value,
                200
            )
            
            return BLEOResponse.success(
                message="If your email exists, you'll receive reset instructions",
                data=response_data
            ).to_response(status.HTTP_200_OK)
            
        except Exception as e:
            Logger.debug_error(
                f"Password reset request failed with error: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Password reset request failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetConfirmView(APIView):
    """Confirm password reset using token - follows email verification pattern"""
    
    def put(self, request):
        """Reset password using token"""
        try:
            # Validate request data using serializer
            serializer = PasswordResetConfirmSerializer(data=request.data)
            if not serializer.is_valid():
                Logger.debug_error(
                    f"Password reset confirmation validation failed: {serializer.errors}",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid request data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get validated data from serializer
            validated_data = serializer.validated_data
            token = validated_data['token']
            new_password = validated_data['password']
            
            # Log request
            Logger.debug_system_action(
                "Password reset confirmation received",
                LogType.INFO.value,
                200
            )
            
            # Decode and validate JWT token (same as email verification)
            try:
                payload = jwt.decode(
                    token, 
                    os.getenv('JWT_SECRET'), 
                    algorithms=['HS256']
                )
                
                bleoid = payload.get('bleoid')
                email = payload.get('email')
                token_type = payload.get('type')
                
                if token_type != 'password_reset':
                    raise jwt.InvalidTokenError("Invalid token type")
                    
            except jwt.ExpiredSignatureError:
                Logger.debug_error(
                    "Password reset failed: Token expired",
                    401,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Reset token has expired. Please request a new one."
                ).to_response(status.HTTP_401_UNAUTHORIZED)
                
            except jwt.InvalidTokenError as e:
                Logger.debug_error(
                    f"Password reset failed: Invalid token - {str(e)}",
                    401,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid reset token"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
            
            masked_email = PrivacyUtils.mask_email(email)
            
            # Get reset record and create model instance
            db_password_resets = MongoDB.get_instance().get_collection('PasswordResets')
            reset_record_data = db_password_resets.find_one({'email': email, 'token': token})
            
            if not reset_record_data:
                Logger.debug_error(
                    f"Password reset failed: No reset record found for {masked_email}",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid or expired reset token"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Create model instance from database data
            reset_record = PasswordResets.from_dict(reset_record_data)
            
            # Use model methods for validation
            if reset_record.used:
                Logger.debug_error(
                    f"Password reset failed: Token already used for {masked_email}",
                    400,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Reset token has already been used"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            if reset_record.is_expired():
                Logger.debug_error(
                    f"Password reset failed: Token expired for {masked_email}",
                    401,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Reset token has expired. Please request a new one."
                ).to_response(status.HTTP_401_UNAUTHORIZED)
            
            # Update user's password
            db_users = MongoDB.get_instance().get_collection('Users')
            reset_time = datetime.now(timezone.utc)
            
            user_update_result = db_users.update_one(
                {"bleoid": bleoid, "email": email},
                {
                    "$set": {
                        "password": make_password(new_password),
                        "password_reset_at": reset_time,
                        "updated_at": reset_time
                    }
                }
            )
            
            if user_update_result.matched_count == 0:
                Logger.debug_error(
                    f"Password reset failed: User not found for {masked_email}",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="User not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Mark reset record as used using model method
            reset_record.mark_as_used()
            
            # Update the database record
            db_password_resets.update_one(
                {"email": email, "token": token},
                {"$set": reset_record.to_dict()}
            )
            
            # Prepare response data with proper structure
            response_data = {
                'password_reset': True,
                'reset_at': reset_time.isoformat(),  # Convert to ISO string
                'message': 'Password reset successfully! You can now login with your new password.'
            }
            
            # Use response serializer for consistent output
            response_serializer = PasswordResetResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                validated_response = response_serializer.validated_data
                
                Logger.debug_system_action(
                    f"Password reset completed successfully for {masked_email}",
                    LogType.SUCCESS.value,
                    200
                )
                
                return BLEOResponse.success(
                    message="Password reset successfully! You can now login with your new password.",
                    data=validated_response
                ).to_response(status.HTTP_200_OK)
            else:
                # Log serializer errors but still return success with raw data
                Logger.debug_error(
                    f"Response serializer validation failed: {response_serializer.errors}",
                    500,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                # Fallback if response serializer fails
                return BLEOResponse.success(
                    message="Password reset successfully! You can now login with your new password.",
                    data=response_data
                ).to_response(status.HTTP_200_OK)
                
        except Exception as e:
            Logger.debug_error(
                f"Password reset confirmation failed with error: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Password reset failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Check if reset token is valid"""
        try:
            # Get token from query parameters
            token = request.query_params.get('token')
            
            print(f"here1")

            # Use serializer for proper validation
            validate_data = {'token': token} if token else {}
            serializer = PasswordResetTokenValidationSerializer(data=validate_data)
            
            if not serializer.is_valid():
                return BLEOResponse.validation_error(
                    message="Invalid token parameter",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get validated token
            validated_token = serializer.validated_data['token']
            
            # Continue with JWT validation...
            try:
                payload = jwt.decode(
                    validated_token,
                    os.getenv('JWT_SECRET'), 
                    algorithms=['HS256']
                )
                
                token_type = payload.get('type')
                if token_type != 'password_reset':
                    raise jwt.InvalidTokenError("Invalid token type")
                
                email = payload.get('email')
                
                print(f"here2")

                # Get reset record and check using model
                db_password_resets = MongoDB.get_instance().get_collection('PasswordResets')
                reset_record_data = db_password_resets.find_one({'email': email, 'token': token})
                
                if not reset_record_data:
                    return BLEOResponse.validation_error(
                        message="Invalid or expired reset token"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                
                # Create model instance and validate
                reset_record = PasswordResets.from_dict(reset_record_data)
                
                if not reset_record.is_valid():
                    return BLEOResponse.validation_error(
                        message="Invalid or expired reset token"
                    ).to_response(status.HTTP_400_BAD_REQUEST)
                
                print(f"here3")

                # Prepare structured response data
                response_data = {
                    "token_valid": True,
                    "expires_at": self._ensure_timezone_aware(reset_record.expires_at).isoformat(),
                    "created_at": self._ensure_timezone_aware(reset_record.created_at).isoformat(),
                    "time_remaining_hours": max(0, (self._ensure_timezone_aware(reset_record.expires_at) - datetime.now(timezone.utc)).total_seconds() / 3600)
                }

                print(f"here4")
                
                return BLEOResponse.success(
                    message="Reset token is valid",
                    data=response_data
                ).to_response(status.HTTP_200_OK)
                
            except jwt.ExpiredSignatureError:
                return BLEOResponse.validation_error(
                    message="Reset token has expired"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
                
            except jwt.InvalidTokenError:
                return BLEOResponse.validation_error(
                    message="Invalid reset token"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            Logger.debug_error(
                f"Password reset token validation failed: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to validate reset token: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _ensure_timezone_aware(self, dt):
        """Ensure datetime is timezone-aware (assume UTC if naive)"""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt