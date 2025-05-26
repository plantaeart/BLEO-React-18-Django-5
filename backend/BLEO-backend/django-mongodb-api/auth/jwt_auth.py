from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import check_password
import jwt
from datetime import datetime, timedelta, timezone  # Added timezone import
from utils.mongodb_utils import MongoDB
from models.response.BLEOResponse import BLEOResponse
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# Get JWT secret from environment or use a default
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-here')
ACCESS_TOKEN_EXPIRE = int(os.getenv('ACCESS_TOKEN_EXPIRE', '15'))  # minutes
REFRESH_TOKEN_EXPIRE = int(os.getenv('REFRESH_TOKEN_EXPIRE', '7'))  # days

class CustomTokenObtainPairView(APIView):
    """API view for obtaining JWT token pairs"""
    
    def post(self, request):
        """Authenticate user and return token pair"""
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not email or not password:
                return BLEOResponse.validation_error(
                    message="Email and password are required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Get user from database
            db = MongoDB.get_instance().get_collection('Users')
            user = db.find_one({"mail": email})
            
            if not user or not check_password(password, user['password']):
                return BLEOResponse.validation_error(
                    message="Invalid credentials"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
            
            # Create tokens with fixed datetime usage
            access_payload = {
                'bleoid': user['BLEOId'],
                'email': user['mail'],
                'exp': datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE)  # Fixed
            }
            
            refresh_payload = {
                'bleoid': user['BLEOId'],
                'email': user['mail'],
                'exp': datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE)  # Fixed
            }
            
            access_token = jwt.encode(access_payload, JWT_SECRET, algorithm='HS256')
            refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm='HS256')
            
            # Update last login
            db.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now()}}
            )
            
            return BLEOResponse.success(
                data={
                    'access': access_token,
                    'refresh': refresh_token,
                    'user': {
                        'bleoid': user['BLEOId'],
                        'email': user['mail'],
                        'username': user.get('userName', 'User')
                    }
                },
                message="Authentication successful"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Authentication failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)

class TokenRefreshView(APIView):
    """API view for refreshing JWT tokens"""
    
    def post(self, request):
        """Refresh access token using refresh token"""
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return BLEOResponse.validation_error(
                    message="Refresh token is required"
                ).to_response(status.HTTP_400_BAD_REQUEST)
            
            # Verify token
            try:
                payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=['HS256'])
                
                # Check if token is blacklisted
                db_blacklist = MongoDB.get_instance().get_collection('TokenBlacklist')
                if db_blacklist.find_one({"token": refresh_token}):
                    raise jwt.InvalidTokenError("Token is blacklisted")
                
            except jwt.ExpiredSignatureError:
                return BLEOResponse.validation_error(
                    message="Refresh token expired"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
                
            except jwt.InvalidTokenError:
                return BLEOResponse.validation_error(
                    message="Invalid refresh token"
                ).to_response(status.HTTP_401_UNAUTHORIZED)
            
            # Create new access token with fixed datetime usage
            access_payload = {
                'bleoid': payload['bleoid'],
                'email': payload['email'],
                'exp': datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE)  # Fixed
            }
            
            new_access_token = jwt.encode(access_payload, JWT_SECRET, algorithm='HS256')
            
            return BLEOResponse.success(
                data={
                    'access': new_access_token
                },
                message="Token refreshed successfully"
            ).to_response()
            
        except Exception as e:
            return BLEOResponse.server_error(
                message=f"Token refresh failed: {str(e)}"
            ).to_response(status.HTTP_500_INTERNAL_SERVER_ERROR)