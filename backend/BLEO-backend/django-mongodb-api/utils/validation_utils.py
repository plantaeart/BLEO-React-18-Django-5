from rest_framework import status
from rest_framework.exceptions import ValidationError
from models.response.BLEOResponse import BLEOResponse

def validate_url_bleoid(bleoid_str, field_name="bleoid"):
    """Validate BLEOID from URL parameters"""
    try:
        from api.serializers import validate_bleoid_format
        return validate_bleoid_format(bleoid_str, field_name)
    except Exception as e:
        from rest_framework import serializers
        raise serializers.ValidationError(f"Invalid {field_name} in URL: {str(e)}")