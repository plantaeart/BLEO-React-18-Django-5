"""
Validation patterns and constants for the BLEO application.
Centralizes regex patterns, validation rules, and format constants.
"""

import re

class ValidationPatterns:
    """Common validation patterns used across the application"""
    
    # BLEOID patterns
    BLEOID_PATTERN = r'^[A-Z0-9]{6}$'
    BLEOID_LENGTH = 6
    BLEOID_DESCRIPTION = "BLEOID must be exactly 6 uppercase letters/numbers"
    
    # Email patterns
    EMAIL_BASIC_PATTERN = r'^[^@]+@[^@]+\.[^@]+$'
    EMAIL_MAX_LENGTH = 254
    
    # Password patterns
    PASSWORD_MIN_LENGTH = 8
    
    # JWT token pattern (basic format check)
    JWT_PATTERN = r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$'
    
    # Date patterns
    DATE_DD_MM_YYYY_PATTERN = r'^\d{2}-\d{2}-\d{4}$'
    DATE_YYYY_MM_DD_PATTERN = r'^\d{4}-\d{2}-\d{2}$'
    
    # Common character sets
    UPPERCASE_ALPHANUMERIC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    
    @classmethod
    def validate_bleoid_format(cls, value, field_name="bleoid"):
        """Centralized BLEOID validation function"""
        if not value or len(value.strip()) == 0:
            from rest_framework import serializers
            raise serializers.ValidationError(f"{field_name} cannot be empty")
        
        # Normalize to uppercase and strip whitespace
        normalized_value = value.strip().upper()
        
        # Validate format matches pattern
        if not re.match(cls.BLEOID_PATTERN, normalized_value):
            from rest_framework import serializers
            raise serializers.ValidationError(f"{field_name} {cls.BLEOID_DESCRIPTION}")
        
        return normalized_value
    
    @classmethod
    def validate_jwt_format(cls, value, field_name="token"):
        """Basic JWT format validation"""
        if not value or len(value.strip()) == 0:
            from rest_framework import serializers
            raise serializers.ValidationError(f"{field_name} cannot be empty")
        
        # Basic JWT format check (3 parts separated by dots)
        parts = value.split('.')
        if len(parts) != 3:
            from rest_framework import serializers
            raise serializers.ValidationError(f"Invalid JWT {field_name} format")
        
        return value.strip()
    
    @classmethod
    def validate_url_bleoid(cls, bleoid_str, field_name="bleoid"):
        """Validate BLEOID from URL parameters"""
        if not bleoid_str:
            from rest_framework import serializers
            raise serializers.ValidationError(f"{field_name} parameter is required")
        
        try:
            return cls.validate_bleoid_format(bleoid_str, field_name)
        except Exception as e:
            from rest_framework import serializers
            raise serializers.ValidationError(f"Invalid {field_name} in URL: {str(e)}")
    
    @classmethod
    def is_valid_bleoid(cls, value):
        """Check if value matches BLEOID pattern without raising exception"""
        if not value:
            return False
        
        normalized_value = value.strip().upper()
        return bool(re.match(cls.BLEOID_PATTERN, normalized_value))
    
    @classmethod
    def normalize_bleoid(cls, value):
        """Normalize BLEOID to standard format"""
        if not value:
            return value
        return value.strip().upper()

class ValidationMessages:
    """Standard validation error messages"""
    
    # BLEOID messages
    BLEOID_REQUIRED = "BLEOID is required"
    BLEOID_EMPTY = "BLEOID cannot be empty"
    BLEOID_INVALID_FORMAT = f"BLEOID must be exactly {ValidationPatterns.BLEOID_LENGTH} uppercase letters/numbers"
    BLEOID_SELF_REFERENCE = "Cannot reference yourself"
    
    # Email messages
    EMAIL_REQUIRED = "Email is required"
    EMAIL_INVALID_FORMAT = "Invalid email format"
    EMAIL_EMPTY = "Email cannot be empty"
    EMAIL_TOO_LONG = f"Email cannot exceed {ValidationPatterns.EMAIL_MAX_LENGTH} characters"
    
    # Password messages
    PASSWORD_REQUIRED = "Password is required"
    PASSWORD_TOO_SHORT = f"Password must be at least {ValidationPatterns.PASSWORD_MIN_LENGTH} characters long"
    
    # Token messages
    TOKEN_REQUIRED = "Token is required"
    TOKEN_EMPTY = "Token cannot be empty"
    TOKEN_INVALID_FORMAT = "Invalid token format"
    
    # Date messages
    DATE_INVALID_FORMAT = "Date format invalid. Please use DD-MM-YYYY or YYYY-MM-DD format"
    
    # General messages
    FIELD_REQUIRED = "{field_name} is required"
    FIELD_EMPTY = "{field_name} cannot be empty"
    FIELD_TOO_LONG = "{field_name} is too long"

class ValidationRules:
    """Validation rules and constraints"""
    
    # Field length constraints
    MAX_LENGTHS = {
        'bleoid': ValidationPatterns.BLEOID_LENGTH,
        'email': ValidationPatterns.EMAIL_MAX_LENGTH,
        'userName': 50,
        'bio': 500,
        'message_title': 255,
        'message_text': 5000,
    }
    
    # Minimum length constraints
    MIN_LENGTHS = {
        'password': ValidationPatterns.PASSWORD_MIN_LENGTH,
        'bleoid': ValidationPatterns.BLEOID_LENGTH,
    }
    
    # Date formats (in order of preference)
    SUPPORTED_DATE_FORMATS = ['%d-%m-%Y', '%Y-%m-%d']
    STANDARD_DATE_FORMAT = '%d-%m-%Y'
    
    # JWT expiration times (in hours)
    JWT_EXPIRATION = {
        'email_verification': 1,
        'password_reset': 1,
        'access_token': 1,
        'refresh_token': 168,  # 7 days
    }