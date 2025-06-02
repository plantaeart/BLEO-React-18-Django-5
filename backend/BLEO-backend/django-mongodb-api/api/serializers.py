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
    BLEOId = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField() 
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    userName = serializers.CharField(required=False, default="NewUser") 
    profilePic = serializers.SerializerMethodField()
    email_verified = serializers.BooleanField(default=False, required=False)
    last_login = serializers.DateTimeField(required=False)
    created_at = serializers.DateTimeField(required=False)
    bio = serializers.CharField(required=False, allow_null=True)
    preferences = serializers.DictField(required=False, default=dict) 
    
    def get_profilePic(self, obj):
        # Handle Binary data - return as base64 if needed
        if obj.get('profilePic'):
            import base64
            return base64.b64encode(obj['profilePic']).decode('utf-8')
        return None

    def validate(self, data):
        """
        Add validation if needed
        """
        # Example: Validate password strength
        if 'password' in data and len(data['password']) < 8:
            raise serializers.ValidationError({"password": "Password must be at least 8 characters long"})
        data = super().validate(data)
        
        # Auto-generate BLEOId if requested and not provided
        if self.context.get('auto_generate_id') and 'BLEOId' not in data:
            import random
            import string
            # Generate a random 6-character ID (like your existing logic)
            chars = string.ascii_uppercase + string.digits
            data['BLEOId'] = ''.join(random.choice(chars) for _ in range(6))
            
        return data

class LinkSerializer(serializers.Serializer):
    BLEOIdPartner1 = serializers.CharField()
    BLEOIdPartner2 = serializers.CharField(allow_null=True, required=False)
    status = serializers.ChoiceField(
        choices=["pending", "accepted", "rejected", "blocked"],
        default="pending"
    )
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)
    
    def validate(self, data):
        """Validate that a user isn't linking to themselves"""
        p1 = data.get('BLEOIdPartner1')
        p2 = data.get('BLEOIdPartner2')
        
        if p1 and p2 and p1 == p2:
            raise serializers.ValidationError({"BLEOIdPartner2": "Cannot link a user to themselves"})
            
        return data

class MessagesDaysSerializer(serializers.Serializer):
    """Serializer for MessagesDays"""
    fromBLEOId = serializers.CharField(required=True)
    toBLEOId = serializers.CharField(required=True)
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
            
        return data

class ConnectionRequestSerializer(serializers.Serializer):
    """Serializer for connection requests"""
    from_bleoid = serializers.CharField()
    to_bleoid = serializers.CharField()
    
    def validate(self, data):
        if data.get('from_bleoid') == data.get('to_bleoid'):
            raise serializers.ValidationError({"to_bleoid": "Cannot connect a user to themselves"})
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
    BLEOIdPartner1 = serializers.CharField()
    BLEOIdPartner2 = serializers.CharField(allow_null=True)
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
            
        if obj.get('BLEOIdPartner1') == current_user:
            return "outgoing"
        elif obj.get('BLEOIdPartner2') == current_user:
            return "incoming"
        return None
    
    # Add this field to show the direction (when context is provided)
    direction = serializers.SerializerMethodField(read_only=True)

class ConnectionFilterSerializer(serializers.Serializer):
    """Serializer for connection list filtering"""
    bleoid = serializers.CharField(required=True)
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

class DebugLogSerializer(serializers.Serializer):
    """Serializer for validating log data from API requests"""
    message = serializers.CharField(required=True)
    type = serializers.CharField(required=True)
    code = serializers.IntegerField(required=True)
    BLEOId = serializers.CharField(required=False, allow_null=True)
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