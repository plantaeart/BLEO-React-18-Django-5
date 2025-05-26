from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from django.utils.functional import SimpleLazyObject
from utils.mongodb_utils import MongoDB

class TokenBlacklistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        # Only check on authenticated endpoints
        if 'Authorization' in request.headers:
            try:
                # Extract token
                header = request.headers.get('Authorization')
                if header.startswith('Bearer '):
                    token = header.split(' ')[1]
                    
                    # Check if token is blacklisted
                    db = MongoDB.get_instance().get_collection('TokenBlacklist')
                    if db.find_one({"token": token}):
                        raise exceptions.AuthenticationFailed('Token is blacklisted')
            except Exception:
                # If any error occurs during token validation, 
                # we'll let the view handle authentication
                pass
                
        response = self.get_response(request)
        return response