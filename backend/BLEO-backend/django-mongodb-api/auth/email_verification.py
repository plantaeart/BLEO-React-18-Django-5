from rest_framework.views import APIView
from rest_framework import status
from utils.mongodb_utils import MongoDB
from models.response.BLEOResponse import BLEOResponse
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType
from utils.privacy_utils import PrivacyUtils
from services.EmailService import EmailService
from api.serializers import (
    EmailVerificationRequestSerializer,
    EmailVerificationConfirmSerializer,
    EmailVerificationResponseSerializer
)
from django.conf import settings
import jwt
import uuid
from datetime import datetime, timedelta, timezone
import os

class EmailVerificationView(APIView):
    """API view for email verification system"""
    
    def post(self, request):
        """Send email verification token to user"""
        try:
            # Validate request data using updated serializer
            serializer = EmailVerificationRequestSerializer(data=request.data)
            if not serializer.is_valid():
                # Enhanced error logging for email validation
                error_details = []
                if 'email' in serializer.errors:
                    error_details.append(f"Email: {serializer.errors['email']}")
                
                Logger.debug_error(
                    f"Email verification request validation failed: {', '.join(error_details)}",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid request data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Email is now guaranteed to be valid format and <= 254 chars
            email = serializer.validated_data['email']
            masked_email = PrivacyUtils.mask_email(email)
            
            # Log request
            Logger.debug_system_action(
                f"Email verification request for {masked_email}",
                LogType.INFO.value,
                200
            )
            
            # Check if user exists
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({'email': email})
            
            if not user:
                Logger.debug_error(
                    f"Email verification failed: User not found for {masked_email}",
                    404,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="User with this email address not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Check if already verified
            if user.get('email_verified', False):
                return BLEOResponse.success(
                    message="Email is already verified",
                    data={"email_verified": True}
                ).to_response(status.HTTP_200_OK)
            
            # Generate JWT token
            payload = {
                'bleoid': user['bleoid'],
                'email': email,
                'type': 'email_verification',
                'jti': str(uuid.uuid4()),
                'iat': datetime.now(timezone.utc).timestamp(),
                'exp': (datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()
            }
            
            verification_token = jwt.encode(
                payload, 
                os.getenv('JWT_SECRET'), 
                algorithm='HS256'
            )
            
            # Store verification token in database
            db_email_verifications = MongoDB.get_instance().get_collection('EmailVerifications')
            verification_data = {
                'bleoid': user['bleoid'],
                'email': email,
                'token': verification_token,
                'created_at': datetime.now(timezone.utc),
                'expires_at': datetime.now(timezone.utc) + timedelta(hours=24),
                'verified': False,
                'attempts': 0
            }
            
            # Remove any existing verification records for this email
            db_email_verifications.delete_many({'email': email})
            
            # Insert new verification record
            db_email_verifications.insert_one(verification_data)
            
            # Send verification email
            try:
                email_sent = EmailService.send_verification_email(
                    email=email,
                    verification_token=verification_token,
                    user_name=user.get('userName', 'User')
                )
                
                if not email_sent:
                    raise Exception("Email service returned False")
                    
            except Exception as e:
                Logger.debug_error(
                    f"Failed to send verification email to {masked_email}: {str(e)}",
                    500,
                    user['bleoid'],
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.server_error(
                    message="Failed to send verification email. Please try again later."
                ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Log success
            Logger.debug_system_action(
                f"Verification email sent successfully to {masked_email}",
                LogType.INFO.value,
                200
            )
            
            return BLEOResponse.success(
                message="Verification email sent successfully. Please check your inbox.",
                data={"email_sent": True}
            ).to_response(status.HTTP_200_OK)
            
        except Exception as e:
            Logger.debug_error(
                f"Email verification request failed with error: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Email verification request failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        """Verify email using token"""
        try:
            # Validate request data using updated serializer with stricter validation
            serializer = EmailVerificationConfirmSerializer(data=self._extract_request_data(request))
            if not serializer.is_valid():
                # Enhanced error logging for token/BLEOID validation
                error_details = []
                if 'bleoid' in serializer.errors:
                    error_details.append(f"BLEOID: {serializer.errors['bleoid']}")
                if 'email' in serializer.errors:
                    error_details.append(f"Email: {serializer.errors['email']}")
                if 'token' in serializer.errors:
                    error_details.append(f"Token: {serializer.errors['token']}")
                
                Logger.debug_error(
                    f"Email verification validation failed: {', '.join(error_details)}",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid request data",
                    errors=serializer.errors
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # All fields are now guaranteed to be valid format
            token = serializer.validated_data['token']
            
            # Log request
            Logger.debug_system_action(
                "Email verification confirmation received",
                LogType.INFO.value,
                200
            )
            
            # Decode and validate JWT token
            try:
                payload = jwt.decode(
                    token, 
                    os.getenv('JWT_SECRET'), 
                    algorithms=['HS256']
                )
                
                bleoid = payload.get('bleoid')
                email = payload.get('email')
                token_type = payload.get('type')
                
                if token_type != 'email_verification':
                    raise jwt.InvalidTokenError("Invalid token type")
                    
            except jwt.ExpiredSignatureError:
                Logger.debug_error(
                    "Email verification failed: Token expired",
                    401,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Verification token has expired. Please request a new one."
                ).to_response(status.HTTP_401_UNAUTHORIZED)
                
            except jwt.InvalidTokenError as e:
                Logger.debug_error(
                    f"Email verification failed: Invalid token - {str(e)}",
                    401,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid verification token"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
            
            masked_email = PrivacyUtils.mask_email(email)
            
            # Check if verification record exists
            db_email_verifications = MongoDB.get_instance().get_collection('EmailVerifications')
            verification_record = db_email_verifications.find_one({'email': email, 'token': token})
            
            if not verification_record:
                Logger.debug_error(
                    f"Email verification failed: No verification record found for {masked_email}",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid or expired verification token"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Check if already verified
            if verification_record.get('verified', False):
                response_data = {
                    'email_verified': True,
                    'email_verified_at': verification_record.get('verified_at'),
                    'message': 'Email is already verified'
                }
                
                # Use response serializer
                response_serializer = EmailVerificationResponseSerializer(data=response_data)
                if response_serializer.is_valid():
                    return BLEOResponse.success(
                        message="Email is already verified",
                        data=response_serializer.validated_data
                    ).to_response(status.HTTP_200_OK)
            
            # Check if token is expired
            expires_at = self._ensure_timezone_aware(verification_record['expires_at'])
            if expires_at < datetime.now(timezone.utc):
                Logger.debug_error(
                    f"Email verification failed: Token expired for {masked_email}",
                    401,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Verification token has expired. Please request a new one."
                ).to_response(status.HTTP_401_UNAUTHORIZED)
            
            # Update user's email verification status
            db_users = MongoDB.get_instance().get_collection('Users')
            verification_time = datetime.now(timezone.utc)
            
            user_update_result = db_users.update_one(
                {"bleoid": bleoid, "email": email},
                {
                    "$set": {
                        "email_verified": True,
                        "email_verified_at": verification_time
                    }
                }
            )
            
            if user_update_result.matched_count == 0:
                Logger.debug_error(
                    f"Email verification failed: User not found for {masked_email}",
                    404,
                    bleoid,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="User not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            # Update verification record
            db_email_verifications.update_one(
                {"email": email, "token": token},
                {
                    "$set": {
                        "verified": True,
                        "verified_at": verification_time
                    }
                }
            )
            
            # Prepare response data
            response_data = {
                'email_verified': True,
                'email_verified_at': verification_time,
                'message': 'Email verified successfully! Your account is now active.'
            }
            
            # Use response serializer
            response_serializer = EmailVerificationResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                Logger.debug_system_action(
                    f"Email verification completed successfully for {masked_email}",
                    LogType.INFO.value,
                    200
                )
                
                return BLEOResponse.success(
                    message="Email verified successfully! Your account is now active.",
                    data=response_serializer.validated_data
                ).to_response(status.HTTP_200_OK)
            else:
                # Fallback if serializer fails
                return BLEOResponse.success(
                    message="Email verified successfully! Your account is now active.",
                    data=response_data
                ).to_response(status.HTTP_200_OK)
                
        except Exception as e:
            Logger.debug_error(
                f"Email verification confirmation failed with error: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Email verification failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Check email verification status"""
        try:
            email = request.query_params.get('email')
            
            if not email:
                return BLEOResponse.validation_error(
                    message="Email parameter is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Validate email format
            if not PrivacyUtils.is_valid_email(email):
                return BLEOResponse.validation_error(
                    message="Invalid email format"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            masked_email = PrivacyUtils.mask_email(email)
            
            # Check user's verification status
            db_users = MongoDB.get_instance().get_collection('Users')
            user = db_users.find_one({'email': email})
            
            if not user:
                return BLEOResponse.validation_error(
                    message="User not found"
                ).to_response(status.HTTP_404_NOT_FOUND)
            
            response_data = {
                'email_verified': user.get('email_verified', False),
                'email_verified_at': user.get('email_verified_at'),
                'message': 'Email verification status retrieved'
            }
            
            # Use response serializer
            response_serializer = EmailVerificationResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                return BLEOResponse.success(
                    message="Email verification status retrieved",
                    data=response_serializer.validated_data
                ).to_response(status.HTTP_200_OK)
            else:
                return BLEOResponse.success(
                    message="Email verification status retrieved",
                    data=response_data
                ).to_response(status.HTTP_200_OK)
                
        except Exception as e:
            Logger.debug_error(
                f"Email verification status check failed: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Failed to check verification status: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _extract_request_data(self, request):
        """Extract data from request regardless of content type"""
        try:
            if hasattr(request, 'data') and request.data:
                return request.data
            
            if request.body:
                try:
                    import json
                    body_str = request.body.decode('utf-8')
                    return json.loads(body_str)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            
            if hasattr(request, 'POST') and request.POST:
                return dict(request.POST)
            
            if hasattr(request, 'query_params') and request.query_params:
                return dict(request.query_params)
            
            return {}
            
        except Exception:
            return {}
    
    def _ensure_timezone_aware(self, dt):
        """Ensure datetime is timezone-aware (assume UTC if naive)"""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt