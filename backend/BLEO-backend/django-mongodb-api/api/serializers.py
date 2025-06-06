import re
from rest_framework import serializers
from models.enums.MessageType import MessageType
from models.enums.ConnectionStatusType import ConnectionStatusType
from datetime import datetime
from models.enums.EnergyLevelType import EnergyLevelType
from models.enums.PleasantnessType import PleasantnessType
from models.enums.UserType import UserType
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType
from models.enums.DebugType import DebugType
from models.AppParameters import AppParameters
import random
import string
from bson import Binary
import base64

from utils.validation_patterns import (
    ValidationPatterns, 
    ValidationMessages, 
    ValidationRules
)

class FlexibleDateField(serializers.Field):
    """Custom field to handle multiple date formats"""
    
    def to_internal_value(self, value):
        """Convert string date to Python date object"""
        if not value:
            return None
            
        # Use centralized date formats
        for date_format in ValidationRules.SUPPORTED_DATE_FORMATS:
            try:
                return datetime.strptime(value, date_format).date()
            except (ValueError, TypeError):
                continue
                
        raise serializers.ValidationError(ValidationMessages.DATE_INVALID_FORMAT)
    
    def to_representation(self, value):
        """Convert Python date object to string"""
        if not value:
            return None
            
        if isinstance(value, str):
            return value
            
        # Use standard date format
        return value.strftime(ValidationRules.STANDARD_DATE_FORMAT)

class MessageInfosSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, read_only=True)
    title = serializers.CharField(max_length=ValidationRules.MAX_LENGTHS['message_title'])
    text = serializers.CharField(max_length=ValidationRules.MAX_LENGTHS['message_text'])
    type = serializers.ChoiceField(choices=[t.value for t in MessageType])
    created_at = serializers.DateTimeField(default=datetime.now, format="%Y-%m-%dT%H:%M:%S")
    date = serializers.CharField(required=False, read_only=True)
    
    def validate_type(self, value):
        """Additional validation for message type"""
        if value not in [t.value for t in MessageType]:
            raise serializers.ValidationError(f"Invalid message type: '{value}'. Valid types are: {', '.join([t.value for t in MessageType])}")
        return value

class UserSerializer(serializers.Serializer):
    bleoid = serializers.CharField(max_length=ValidationRules.MAX_LENGTHS['bleoid'], required=False)
    email = serializers.EmailField(max_length=ValidationRules.MAX_LENGTHS['email'], required=False)
    password = serializers.CharField(min_length=ValidationRules.MIN_LENGTHS['password'], required=False)
    userName = serializers.CharField(max_length=ValidationRules.MAX_LENGTHS['userName'], required=False)
    bio = serializers.CharField(max_length=ValidationRules.MAX_LENGTHS['bio'], required=False)
    email_verified = serializers.BooleanField(required=False)
    preferences = serializers.DictField(required=False)
    last_login = serializers.CharField(required=False)
    created_at = serializers.CharField(required=False)
    updated_at = serializers.CharField(required=False)
    profilePic = serializers.CharField(required=False)  # Base64 encoded
    
    def __init__(self, *args, **kwargs):
        """Handle partial updates by making required fields optional"""
        super().__init__(*args, **kwargs)
        
        # If this is a partial update, make all fields optional
        if kwargs.get('partial', False):
            for field_name, field in self.fields.items():
                field.required = False
    
    def _generate_bleoid(self):
        """Generate a random 6-character BLEOID"""
        return ''.join(random.choice(ValidationPatterns.UPPERCASE_ALPHANUMERIC) for _ in range(ValidationPatterns.BLEOID_LENGTH))
    
    def validate_bleoid(self, value):
        """Validate BLEOID format when provided"""
        if value:
            # Use centralized validation
            return ValidationPatterns.validate_bleoid_format(value, "bleoid")
        return value
    
    def validate_email(self, value):
        """Validate email format when provided"""
        if value:
            # Let DRF handle email validation
            return value.lower().strip()
        return value
    
    def validate(self, data):
        """Cross-field validation for full creation"""
        # Check if this is a full creation (not partial update)
        is_partial = getattr(self, 'partial', False)
        auto_generate = self.context.get('auto_generate_id', False)
        
        # Handle auto-generation of bleoid
        if auto_generate and not data.get('bleoid'):
            data['bleoid'] = self._generate_bleoid()
            # Log the generation for debugging
            print(f"Auto-generated BLEOID: {data['bleoid']}")
        
        if not is_partial:
            # For full creation, require email and password
            if not data.get('email'):
                raise serializers.ValidationError({
                    'email': ValidationMessages.EMAIL_REQUIRED
                })
            if not data.get('password'):
                raise serializers.ValidationError({
                    'password': ValidationMessages.PASSWORD_REQUIRED
                })
            
            # Require bleoid for full creation (unless auto-generating)
            if not auto_generate and not data.get('bleoid'):
                raise serializers.ValidationError({
                    'bleoid': ValidationMessages.BLEOID_REQUIRED
                })
        
        return data
    
    def to_representation(self, instance):
        """Convert model instance to serialized data"""
        if isinstance(instance, dict):
            data = instance.copy()
        else:
            data = {
                'bleoid': instance.bleoid,
                'email': instance.email,
                'userName': getattr(instance, 'userName', ''),
                'bio': getattr(instance, 'bio', ''),
            }
        
        # Handle Binary profilePic conversion to base64
        if 'profilePic' in data and isinstance(data['profilePic'], Binary):
            data['profilePic'] = base64.b64encode(data['profilePic']).decode('utf-8')
        
        return data

class LinkSerializer(serializers.Serializer):
    bleoidPartner1 = serializers.CharField(max_length=ValidationRules.MAX_LENGTHS['bleoid'], required=True, allow_null=False)
    bleoidPartner2 = serializers.CharField(max_length=ValidationRules.MAX_LENGTHS['bleoid'], required=True, allow_null=False)
    status = serializers.ChoiceField(
        choices=["pending", "accepted", "rejected", "blocked"],
        default="pending"
    )
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)
    
    def validate_bleoidPartner2(self, value):
        """Validate that bleoidPartner2 is not null or empty"""
        if value is None:
            raise serializers.ValidationError("bleoidPartner2 cannot be null")
        
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError(ValidationMessages.BLEOID_EMPTY)
        
        return ValidationPatterns.validate_bleoid_format(value, "bleoidPartner2")
    
    def validate_bleoidPartner1(self, value):
        """Validate that bleoidPartner1 is not null or empty"""
        if value is None:
            raise serializers.ValidationError("bleoidPartner1 cannot be null")
        
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError(ValidationMessages.BLEOID_EMPTY)
        
        return ValidationPatterns.validate_bleoid_format(value, "bleoidPartner1")
    
    def validate(self, data):
        """Validate that a user isn't linking to themselves"""
        p1 = data.get('bleoidPartner1')
        p2 = data.get('bleoidPartner2')
        
        if p1 and p2 and p1 == p2:
            raise serializers.ValidationError({"bleoidPartner2": ValidationMessages.BLEOID_SELF_REFERENCE})
            
        return data

class MessagesDaysSerializer(serializers.Serializer):
    """Serializer for MessagesDays"""
    from_bleoid = serializers.CharField(max_length=ValidationRules.MAX_LENGTHS['bleoid'], required=True, allow_null=False)
    to_bleoid = serializers.CharField(max_length=ValidationRules.MAX_LENGTHS['bleoid'], required=False, allow_null=False)
    date = serializers.CharField(required=True)
    messages = MessageInfosSerializer(many=True, required=False, default=[])
    mood = serializers.CharField(required=False, allow_null=True)
    energy_level = serializers.CharField(required=False, allow_null=True)
    pleasantness = serializers.CharField(required=False, allow_null=True)
    quadrant = serializers.CharField(required=False, allow_null=True, read_only=True)
    
    def validate(self, data):
        """Validate mood, energy_level and pleasantness compatibility"""
        energy = data.get('energy_level')
        pleasant = data.get('pleasantness')
        
        if energy and energy not in [e.value for e in EnergyLevelType]:
            raise serializers.ValidationError({"energy_level": f"Invalid energy level. Must be one of: {', '.join([e.value for e in EnergyLevelType])}"})
            
        if pleasant and pleasant not in [p.value for p in PleasantnessType]:
            raise serializers.ValidationError({"pleasantness": f"Invalid pleasantness value. Must be one of: {', '.join([p.value for p in PleasantnessType])}"})
        
        # Add self-reference validation (only if to_bleoid is provided)
        from_bleoid = data.get('from_bleoid')
        to_bleoid = data.get('to_bleoid')
        
        if from_bleoid and to_bleoid and from_bleoid == to_bleoid:
            raise serializers.ValidationError({"to_bleoid": ValidationMessages.BLEOID_SELF_REFERENCE})
            
        return data

    def validate_from_bleoid(self, value):
        """Validate from_bleoid format"""
        return ValidationPatterns.validate_bleoid_format(value, "from_bleoid")

    def validate_to_bleoid(self, value):
        """Validate to_bleoid format (when provided)"""
        if value:
            return ValidationPatterns.validate_bleoid_format(value, "to_bleoid")
        return value

class ConnectionRequestSerializer(serializers.Serializer):
    """Serializer for connection requests"""
    from_bleoid = serializers.CharField(
        max_length=6, 
        required=True,
        allow_null=False,
        help_text="BLEOID of the user sending the connection request"
    )
    to_bleoid = serializers.CharField(
        max_length=6, 
        required=True,
        allow_null=False,
        help_text="BLEOID of the user receiving the connection request"
    )
    
    def validate_from_bleoid(self, value):
        """Validate from_bleoid format"""
        return ValidationPatterns.validate_bleoid_format(value, "from_bleoid")

    def validate_to_bleoid(self, value):
        """Validate to_bleoid format"""
        return ValidationPatterns.validate_bleoid_format(value, "to_bleoid")
    
    def validate(self, data):
        """Cross-field validation"""
        from_bleoid = data.get('from_bleoid')
        to_bleoid = data.get('to_bleoid')
        
        if from_bleoid and to_bleoid and from_bleoid == to_bleoid:
            raise serializers.ValidationError({
                'to_bleoid': ValidationMessages.BLEOID_SELF_REFERENCE
            })
        return data

class ConnectionResponseSerializer(serializers.Serializer):
    """Serializer for connection responses"""
    # Map actions to their resulting status values
    ACTION_STATUS_MAP = {
        'accept': ConnectionStatusType.ACCEPTED,
        'reject': ConnectionStatusType.REJECTED,
        'block': ConnectionStatusType.BLOCKED
    }
    
    action = serializers.ChoiceField(choices=list(ACTION_STATUS_MAP.keys()))
    current_status = serializers.CharField(required=False, write_only=True)
    
    def validate(self, data):
        """Validate allowed status transitions"""
        action = data.get('action')
        current_status = data.get('current_status')
        
        # Define allowed transitions
        if current_status == "blocked" and action != "block":
            raise serializers.ValidationError({
                "action": f"Cannot change status from 'blocked' to '{action}'. Blocked connections are permanent."
            })
            
        return data

class ConnectionSerializer(serializers.Serializer):
    """Serializer for connection objects"""
    _id = serializers.CharField(required=False, read_only=True)
    bleoidPartner1 = serializers.CharField(max_length=6, required=True, allow_null=False)
    bleoidPartner2 = serializers.CharField(max_length=6, required=True, allow_null=False)
    status = serializers.ChoiceField(
        choices=[
            ConnectionStatusType.PENDING,
            ConnectionStatusType.ACCEPTED, 
            ConnectionStatusType.REJECTED, 
            ConnectionStatusType.BLOCKED
        ],
        default=ConnectionStatusType.PENDING
    )
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    other_user = serializers.DictField(required=False, read_only=True)
    
    # Add a method to get connection direction relative to a user
    def get_direction(self, obj):
        current_user = self.context.get('current_user')
        if not current_user:
            return None
            
        if obj.get('bleoidPartner1') == current_user:
            return "outgoing"
        elif obj.get('bleoidPartner2') == current_user:
            return "incoming"
        return None
    
    # Add this field to show the direction (when context is provided)
    direction = serializers.SerializerMethodField(read_only=True)

    def validate_bleoidPartner1(self, value):
        """Validate bleoidPartner1 format"""
        return ValidationPatterns.validate_bleoid_format(value, "bleoidPartner1")

    def validate_bleoidPartner2(self, value):
        """Validate bleoidPartner2 format"""
        return ValidationPatterns.validate_bleoid_format(value, "bleoidPartner2")

class ConnectionFilterSerializer(serializers.Serializer):
    """Serializer for connection list filtering"""
    bleoid = serializers.CharField(max_length=6, required=True, allow_null=False)
    status = serializers.ChoiceField(
        choices=["pending", "accepted", "rejected", "blocked", "all"],
        default="all",
        required=False
    )
    direction = serializers.ChoiceField(
        choices=["incoming", "outgoing", "both"],
        default="both",
        required=False
    )

    def validate_bleoid(self, value):
        """Validate bleoid format"""
        return ValidationPatterns.validate_bleoid_format(value, "bleoid")

class DebugLogSerializer(serializers.Serializer):
    """Serializer for validating log data from API requests"""
    message = serializers.CharField(required=True)
    type = serializers.CharField(required=True)
    code = serializers.IntegerField(required=True)
    bleoid = serializers.CharField(max_length=6, required=False, allow_null=True)
    user_type = serializers.CharField(required=False, default=UserType.USER.value)
    error_source = serializers.CharField(required=False, allow_null=True)

    def validate_type(self, value):
        """Validate that type is a valid LogType"""
        if value not in [t.value for t in LogType]:
            raise serializers.ValidationError(
                f"Invalid log type. Must be one of: {', '.join([t.value for t in LogType])}"
            )
        return value

    def validate_user_type(self, value):
        """Validate that user_type is a valid UserType"""
        if value not in [t.value for t in UserType]:
            raise serializers.ValidationError(
                f"Invalid user type. Must be one of: {', '.join([t.value for t in UserType])}"
            )
        return value
        
    def validate_error_source(self, value):
        """Validate that error_source is a valid ErrorSourceType"""
        if value is not None and value not in [t.value for t in ErrorSourceType]:
            raise serializers.ValidationError(
                f"Invalid error source. Must be one of: {', '.join([t.value for t in ErrorSourceType])}"
            )
        return value

    def validate_bleoid(self, value):
        """Validate BLEOID format when provided (null is allowed)"""
        if value is not None:
            return ValidationPatterns.validate_bleoid_format(value, "bleoid")
        return value

class AppParametersSerializer(serializers.Serializer):
    """Serializer for app parameters"""
    id = serializers.IntegerField(required=False, read_only=True)
    param_name = serializers.CharField(required=True)
    param_value = serializers.JSONField(required=True)
    
    def validate(self, data):
        """Validate parameter values based on parameter name"""
        param_name = data.get('param_name')
        param_value = data.get('param_value')
        
        # Validate debug_level parameter
        if param_name == AppParameters.PARAM_DEBUG_LEVEL:
            if param_value not in [level.value for level in DebugType]:
                raise serializers.ValidationError({
                    "param_value": f"Invalid debug level. Must be one of: {', '.join([level.value for level in DebugType])}"
                })
        
        return data

class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for EmailVerification model"""
    bleoid = serializers.CharField(max_length=6, required=True, allow_null=False)
    email = serializers.EmailField(max_length=254, required=True)
    token = serializers.CharField(required=True, write_only=True)
    created_at = serializers.DateTimeField(required=False, read_only=True)
    expires_at = serializers.DateTimeField(required=False, read_only=True)
    verified = serializers.BooleanField(default=False, read_only=True)
    attempts = serializers.IntegerField(default=0, read_only=True)
    verified_at = serializers.DateTimeField(required=False, read_only=True, allow_null=True)
    
    def validate_email(self, value):
        """Validate email format with stricter rules"""
        cleaned_email = value.lower().strip()
        
        # Basic checks
        if not cleaned_email:
            raise serializers.ValidationError("Email cannot be empty")
        
        if '@' not in cleaned_email:
            raise serializers.ValidationError("Email must contain @ symbol")
        
        if cleaned_email.count('@') != 1:
            raise serializers.ValidationError("Email must contain exactly one @ symbol")
        
        local_part, domain = cleaned_email.split('@')
        
        # Validate local part
        if not local_part:
            raise serializers.ValidationError("Email must have a local part before @")
        
        if local_part.startswith('.') or local_part.endswith('.'):
            raise serializers.ValidationError("Email local part cannot start or end with a dot")
        
        if '..' in local_part:
            raise serializers.ValidationError("Email local part cannot contain consecutive dots")
        
        # Validate domain
        if not domain:
            raise serializers.ValidationError("Email must have a domain after @")
        
        if domain.startswith('.') or domain.endswith('.'):
            raise serializers.ValidationError("Email domain cannot start or end with a dot")
        
        if '..' in domain:
            raise serializers.ValidationError("Email domain cannot contain consecutive dots")
        
        if '.' not in domain:
            raise serializers.ValidationError("Email domain must contain at least one dot")
        
        # Check for spaces
        if ' ' in cleaned_email:
            raise serializers.ValidationError("Email cannot contain spaces")
        
        return cleaned_email
    
    def validate_bleoid(self, value):
        """Validate BLEO ID format"""
        return ValidationPatterns.validate_bleoid_format(value, "bleoid")

    def validate_token(self, value):
        """Validate JWT token format"""
        return ValidationPatterns.validate_jwt_format(value, "token")
    
    def validate(self, data):
        """Cross-field validation"""
        return data

class EmailVerificationRequestSerializer(serializers.Serializer):
    """Serializer for email verification request (POST)"""
    email = serializers.EmailField(max_length=254, required=True)
    
    def validate_email(self, value):
        """Validate email format"""
        from utils.privacy_utils import PrivacyUtils
        if not PrivacyUtils.is_valid_email(value):
            raise serializers.ValidationError("Invalid email format")
        return value.lower().strip()

class EmailVerificationConfirmSerializer(serializers.Serializer):
    """Serializer for email verification confirmation (PUT)"""
    token = serializers.CharField(required=True)
    
    def validate_token(self, value):
        """Validate JWT token format"""
        return ValidationPatterns.validate_jwt_format(value, "token")

class EmailVerificationResponseSerializer(serializers.Serializer):
    """Serializer for email verification response data"""
    email_verified = serializers.BooleanField()
    email_verified_at = serializers.DateTimeField(allow_null=True)
    message = serializers.CharField()
    
    def to_representation(self, instance):
        """Custom representation"""
        if isinstance(instance, dict):
            # If it's already a dict, check if it has the expected structure
            if 'email_verified' in instance:
                return {
                    'email_verified': instance.get('email_verified', False),
                    'email_verified_at': instance.get('email_verified_at'),
                    'message': instance.get('message', '')
                }
            else:
                # Transform from model structure to response structure
                return {
                    'email_verified': instance.get('verified', False),
                    'email_verified_at': instance.get('verified_at'),
                    'message': instance.get('message', '')
                }
        
        # Handle object instances
        return {
            'email_verified': getattr(instance, 'email_verified', getattr(instance, 'verified', False)),
            'email_verified_at': getattr(instance, 'email_verified_at', getattr(instance, 'verified_at', None)),
            'message': getattr(instance, 'message', '')
        }

class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField(max_length=ValidationRules.MAX_LENGTHS['email'], required=True)
    
    def validate_email(self, value):
        """Validate and normalize email"""
        if not value:
            raise serializers.ValidationError(ValidationMessages.EMAIL_REQUIRED)
        
        # Normalize email
        normalized_email = value.lower().strip()
        
        # Additional validation can be added here
        return normalized_email

class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField(required=True, min_length=1)
    password = serializers.CharField(min_length=ValidationRules.MIN_LENGTHS['password'], required=True)
    
    def validate_token(self, value):
        """Validate token format"""
        return ValidationPatterns.validate_jwt_format(value, "token")
    
    def validate_password(self, value):
        """Validate password strength"""
        if len(value) < ValidationRules.MIN_LENGTHS['password']:
            raise serializers.ValidationError(ValidationMessages.PASSWORD_TOO_SHORT)
        
        return value

class PasswordResetResponseSerializer(serializers.Serializer):
    """Serializer for password reset response data"""
    password_reset = serializers.BooleanField(required=True)
    reset_at = serializers.CharField(required=False, allow_null=True)
    message = serializers.CharField(required=True)
    
    def validate_reset_at(self, value):
        """Validate reset_at is a valid ISO datetime string"""
        if value:
            try:
                from datetime import datetime
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return value
            except ValueError:
                raise serializers.ValidationError("reset_at must be a valid ISO datetime string")
        return value

class PasswordResetTokenValidationSerializer(serializers.Serializer):
    """Serializer for validating password reset token parameter"""
    token = serializers.CharField(
        required=True,
        allow_blank=False,
        min_length=10,
        error_messages={
            'required': 'Token parameter is required',
            'blank': 'Token cannot be blank',
            'min_length': 'Invalid token format'
        }
    )
