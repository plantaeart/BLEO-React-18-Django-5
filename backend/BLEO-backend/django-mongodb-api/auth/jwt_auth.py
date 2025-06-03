from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import check_password
import jwt
from datetime import datetime, timedelta, timezone
from utils.mongodb_utils import MongoDB
from models.response.BLEOResponse import BLEOResponse
from utils.logger import Logger
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType
import os
from dotenv import load_dotenv
from utils.jwt_utils import setup_jwt_secret

load_dotenv()

# Ensure JWT_SECRET exists and is secure
jwt_setup = setup_jwt_secret()
if not jwt_setup['success']:
    print(f"⚠️  JWT Secret setup warning: {jwt_setup['message']}")

# Get JWT secret from environment
JWT_SECRET = os.getenv('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError("JWT_SECRET not found in environment variables. Please run setup_jwt_secret().")

ACCESS_TOKEN_EXPIRE = int(os.getenv('ACCESS_TOKEN_EXPIRE', '15'))  # minutes
REFRESH_TOKEN_EXPIRE = int(os.getenv('REFRESH_TOKEN_EXPIRE', '7'))  # days

class CustomTokenObtainPairView(APIView):
    """API view for obtaining JWT token pairs"""
    
    def post(self, request):
        """Authenticate user and return token pair"""
        try:
            # Log request (don't log password)
            Logger.debug_system_action(
                "Authentication request received",
                LogType.INFO.value,
                200
            )
            
            email = request.data.get('email')
            password = request.data.get('password')
            
            # Mask email for logging
            masked_email = self._mask_email(email) if email else "missing-email"
            
            if not email or not password:
                # Log validation error
                Logger.debug_error(
                    "Authentication failed: Email or password is missing",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Email and password are required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Log authentication attempt
            Logger.debug_system_action(
                f"Authentication attempt for: {masked_email}",
                LogType.INFO.value,
                200
            )
            
            # Get user from database
            db = MongoDB.get_instance().get_collection('Users')
            user = db.find_one({"email": email})
            
            if not user:
                # Log user not found
                Logger.debug_error(
                    f"Authentication failed: User not found for {masked_email}",
                    401,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid credentials"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
                
            if not check_password(password, user['password']):
                # Log password mismatch
                Logger.debug_error(
                    f"Authentication failed: Invalid password for {masked_email}",
                    401,
                    user['BLEOId'],
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid credentials"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
            
            bleoid = user['BLEOId']
            
            # Create tokens with fixed datetime usage
            access_payload = {
                'bleoid': bleoid,
                'email': user['email'],
                'exp': datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
            }
            
            refresh_payload = {
                'bleoid': bleoid,
                'email': user['email'],
                'exp': datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE)
            }
            
            access_token = jwt.encode(access_payload, JWT_SECRET, algorithm='HS256')
            refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm='HS256')
            
            # Log token creation
            Logger.debug_user_action(
                bleoid,
                f"Generated tokens for {masked_email} - access:valid for {ACCESS_TOKEN_EXPIRE}m, refresh:valid for {REFRESH_TOKEN_EXPIRE}d",
                LogType.INFO.value,
                200
            )
            
            # Update last login
            db.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now()}}
            )
            
            # Log authentication success
            Logger.debug_user_action(
                bleoid,
                f"Authentication successful for {masked_email}",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data={
                    'access': access_token,
                    'refresh': refresh_token,
                    'user': {
                        'bleoid': bleoid,
                        'email': user['email'],
                        'username': user.get('userName', 'User')
                    }
                },
                message="Authentication successful"
            ).to_response()
            
        except Exception as e:
            # Log server error
            Logger.debug_error(
                f"Authentication failed with error: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Authentication failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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

class TokenRefreshView(APIView):
    """API view for refreshing JWT tokens"""
    
    def post(self, request):
        """Refresh access token using refresh token"""
        try:
            # Log request - don't log the token itself
            Logger.debug_system_action(
                "Token refresh request received",
                LogType.INFO.value,
                200
            )
            
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                # Log validation error
                Logger.debug_error(
                    "Token refresh failed: Refresh token is missing",
                    400,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Refresh token is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Verify token
            try:
                payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=['HS256'])
                
                # Get bleoid and email for logging
                bleoid = payload.get('bleoid')
                email = payload.get('email')
                masked_email = self._mask_email(email) if email else "unknown-email"
                
                # Log token validated
                Logger.debug_user_action(
                    bleoid,
                    f"Refresh token validated for {masked_email}",
                    LogType.INFO.value,
                    200
                )
                
                # Check if token is blacklisted
                db_blacklist = MongoDB.get_instance().get_collection('TokenBlacklist')
                if db_blacklist.find_one({"token": refresh_token}):
                    # Log blacklisted token
                    Logger.debug_error(
                        f"Token refresh failed: Token is blacklisted for {masked_email}",
                        401,
                        bleoid,
                        ErrorSourceType.SERVER.value
                    )
                    
                    raise jwt.InvalidTokenError("Token is blacklisted")
                
            except jwt.ExpiredSignatureError:
                # Log expired token
                Logger.debug_error(
                    "Token refresh failed: Refresh token expired",
                    401,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Refresh token expired"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
                
            except jwt.InvalidTokenError as e:
                # Log invalid token
                Logger.debug_error(
                    f"Token refresh failed: Invalid token - {str(e)}",
                    401,
                    None,
                    ErrorSourceType.SERVER.value
                )
                
                return BLEOResponse.validation_error(
                    message="Invalid refresh token"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
            
            # Create new access token with fixed datetime usage
            access_payload = {
                'bleoid': payload['bleoid'],
                'email': payload['email'],
                'exp': datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
            }
            
            new_access_token = jwt.encode(access_payload, JWT_SECRET, algorithm='HS256')
            
            # Log success
            Logger.debug_user_action(
                bleoid,
                f"Access token refreshed successfully for {masked_email} - valid for {ACCESS_TOKEN_EXPIRE}m",
                LogType.SUCCESS.value,
                200
            )
            
            return BLEOResponse.success(
                data={
                    'access': new_access_token
                },
                message="Token refreshed successfully"
            ).to_response()
            
        except Exception as e:
            # Log server error
            Logger.debug_error(
                f"Token refresh failed with error: {str(e)}",
                500,
                None,
                ErrorSourceType.SERVER.value
            )
            
            return BLEOResponse.server_error(
                message=f"Token refresh failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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