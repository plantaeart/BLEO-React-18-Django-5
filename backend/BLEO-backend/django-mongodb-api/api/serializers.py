from rest_framework import serializers

class MessageInfosSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    text = serializers.CharField()
    type = serializers.ChoiceField(choices=['Joking', 'Thoughts', 'Love_message', 'Souvenir'])
    created_at = serializers.DateTimeField(required=False)

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    BLEOId = serializers.CharField(max_length=100)
    mail = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    profilePic = serializers.SerializerMethodField()
    
    def get_profilePic(self, obj):
        # Handle Binary data - return as base64 if needed
        if obj.get('profilePic'):
            import base64
            return base64.b64encode(obj['profilePic']).decode('utf-8')
        return None

class LinkSerializer(serializers.Serializer):
    BLEOIdPartner1 = serializers.IntegerField()
    BLEOIdPartner2 = serializers.IntegerField()
    created_at = serializers.DateTimeField(required=False)

class MessageDaySerializer(serializers.Serializer):
    BLEOId = serializers.IntegerField()
    date = serializers.DateField()
    messages = MessageInfosSerializer(many=True)
    mood = serializers.CharField(required=False, allow_null=True)