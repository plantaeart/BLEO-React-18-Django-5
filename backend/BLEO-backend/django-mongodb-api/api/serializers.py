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

def validate_bleoid_format(value, field_name="bleoid"):
    """Centralized BLEOID validation function"""
    if not value or len(value.strip()) == 0:
        raise serializers.ValidationError(f"{field_name} cannot be empty")
    
    # Normalize to uppercase and strip whitespace
    normalized_value = value.strip().upper()
    
    # Validate format matches pattern ^[A-Z0-9]{6}$
    if not re.match(r'^[A-Z0-9]{6}$', normalized_value):
        raise serializers.ValidationError(f"{field_name} must be exactly 6 uppercase letters/numbers")
    
    return normalized_value

class FlexibleDateField(serializers.Field):
    """Custom field to handle multiple date formats"""
    
    def to_internal_value(self, value):
        """Convert string date to Python date object"""
        if not value:
            return None
            
        # Try formats in order of preference
        formats = ['%d-%m-%Y', '%Y-%m-%d']
        
        for date_format in formats:
            try:
                return datetime.strptime(value, date_format).date()
            except (ValueError, TypeError):
                continue
                
        raise serializers.ValidationError(
            f"Date format invalid. Please use DD-MM-YYYY or YYYY-MM-DD format."
        )
    
    def to_representation(self, value):
        """Convert Python date object to string"""
        if not value:
            return None
            
        if isinstance(value, str):
            return value
            
        # Standardize output format to DD-MM-YYYY
        return value.strftime('%d-%m-%Y')

class MessageInfosSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, read_only=True)
    title = serializers.CharField(max_length=255)
    text = serializers.CharField()
    type = serializers.ChoiceField(choices=[t.value for t in MessageType])
    created_at = serializers.DateTimeField(default=datetime.now, format="%Y-%m-%dT%H:%M:%S")
    date = serializers.CharField(required=False, read_only=True)
    
    def validate_type(self, value):
        """Additional validation for message type"""
        if value not in [t.value for t in MessageType]:
            raise serializers.ValidationError(f"Invalid message type: '{value}'. Valid types are: {', '.join([t.value for t in MessageType])}")
        return value

class UserSerializer(serializers.Serializer):
    bleoid = serializers.CharField(max_length=6, required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(min_length=8, required=False)
    userName = serializers.CharField(max_length=50, required=False)
    bio = serializers.CharField(max_length=500, required=False)
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
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(6))
    
    def validate_bleoid(self, value):
        """Validate BLEOID format when provided"""
        if value:
            import re
            normalized_value = value.strip().upper()
            if not re.match(r'^[A-Z0-9]{6}$', normalized_value):
                raise serializers.ValidationError("BLEOID must be exactly 6 uppercase letters/numbers")
            return normalized_value
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
                    'email': 'Email is required for user creation'
                })
            if not data.get('password'):
                raise serializers.ValidationError({
                    'password': 'Password is required for user creation'
                })
            
            # Require bleoid for full creation (unless auto-generating)
            if not auto_generate and not data.get('bleoid'):
                raise serializers.ValidationError({
                    'bleoid': 'BLEOID is required for user creation'
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
    bleoidPartner1 = serializers.CharField(max_length=6, required=True, allow_null=False)
    bleoidPartner2 = serializers.CharField(max_length=6, required=True, allow_null=False)
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
            raise serializers.ValidationError("bleoidPartner2 cannot be empty")
        
        return value.strip().upper()
    
    def validate_bleoidPartner1(self, value):
        """Validate that bleoidPartner1 is not null or empty"""
        if value is None:
            raise serializers.ValidationError("bleoidPartner1 cannot be null")
        
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("bleoidPartner1 cannot be empty")
        
        return value.strip().upper()
    
    def validate(self, data):
        """Validate that a user isn't linking to themselves"""
        p1 = data.get('bleoidPartner1')
        p2 = data.get('bleoidPartner2')
        
        if p1 and p2 and p1 == p2:
            raise serializers.ValidationError({"bleoidPartner2": "Cannot link a user to themselves"})
            
        return data

class MessagesDaysSerializer(serializers.Serializer):
    """Serializer for MessagesDays"""
    from_bleoid = serializers.CharField(max_length=6, required=True, allow_null=False)
    to_bleoid = serializers.CharField(max_length=6, required=False, allow_null=False)
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
            raise serializers.ValidationError({"to_bleoid": "Cannot send messages to yourself"})
            
        return data

    def validate_from_bleoid(self, value):
        """Validate from_bleoid format"""
        return validate_bleoid_format(value, "from_bleoid")

    def validate_to_bleoid(self, value):
        """Validate to_bleoid format (when provided)"""
        if value:
            return validate_bleoid_format(value, "to_bleoid")
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
        return validate_bleoid_format(value, "from_bleoid")

    def validate_to_bleoid(self, value):
        """Validate to_bleoid format"""
        return validate_bleoid_format(value, "to_bleoid")
    
    def validate(self, data):
        """Cross-field validation"""
        from_bleoid = data.get('from_bleoid')
        to_bleoid = data.get('to_bleoid')
        
        if from_bleoid and to_bleoid and from_bleoid == to_bleoid:
            raise serializers.ValidationError({
                'to_bleoid': 'Cannot send connection request to yourself'
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
        return validate_bleoid_format(value, "bleoidPartner1")

    def validate_bleoidPartner2(self, value):
        """Validate bleoidPartner2 format"""
        return validate_bleoid_format(value, "bleoidPartner2")

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
        return validate_bleoid_format(value, "bleoid")

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
            return validate_bleoid_format(value, "bleoid")
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
        return validate_bleoid_format(value, "bleoid")

    def validate_token(self, value):
        """Validate JWT token format"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Token cannot be empty")
        
        # Basic JWT format check (3 parts separated by dots)
        parts = value.split('.')
        if len(parts) != 3:
            raise serializers.ValidationError("Invalid JWT token format")
        
        return value.strip()
    
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
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Token cannot be empty")
        
        # Basic JWT format check
        parts = value.split('.')
        if len(parts) != 3:
            raise serializers.ValidationError("Invalid JWT token format")
        
        return value.strip()

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