from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import DebugLogSerializer
from models.enums.LogType import LogType
from models.enums.UserType import UserType
from models.enums.ErrorSourceType import ErrorSourceType

class DebugLogSerializerTest(BLEOBaseTest):
    """Test cases for DebugLogSerializer validation"""
    
    def test_valid_debug_log(self):
        """Test that valid debug log passes validation"""
        data = {
            'message': 'Test debug message',
            'type': LogType.INFO.value,
            'code': 200,
            'BLEOId': 'USER123',
            'user_type': UserType.USER.value,
            'error_source': ErrorSourceType.SERVER.value
        }
        serializer = DebugLogSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['message'], 'Test debug message')
        self.assertEqual(serializer.validated_data['type'], LogType.INFO.value)
        print(f"  🔹 Validated message: {serializer.validated_data['message']}")
        print(f"  🔹 Validated type: {serializer.validated_data['type']}")
    
    def test_required_fields(self):
        """Test that required fields are enforced"""
        required_fields = ['message', 'type', 'code']
        
        for field in required_fields:
            data = {
                'message': 'Test message',
                'type': LogType.ERROR.value,
                'code': 404
            }
            # Remove the field being tested
            data.pop(field)
            
            serializer = DebugLogSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)
            print(f"  🔹 Missing {field} error detected: {serializer.errors.get(field)}")
    
    def test_invalid_log_type(self):
        """Test that invalid log type is rejected"""
        data = {
            'message': 'Test message',
            'type': 'INVALID_TYPE',
            'code': 200
        }
        serializer = DebugLogSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)
        print(f"  🔹 Invalid type error detected: {serializer.errors.get('type')}")
    
    def test_invalid_user_type(self):
        """Test that invalid user type is rejected"""
        data = {
            'message': 'Test message',
            'type': LogType.INFO.value,
            'code': 200,
            'user_type': 'INVALID_USER'
        }
        serializer = DebugLogSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user_type', serializer.errors)
        print(f"  🔹 Invalid user_type error detected: {serializer.errors.get('user_type')}")
    
    def test_invalid_error_source(self):
        """Test that invalid error source is rejected"""
        data = {
            'message': 'Test message',
            'type': LogType.ERROR.value,
            'code': 500,
            'error_source': 'INVALID_SOURCE'
        }
        serializer = DebugLogSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('error_source', serializer.errors)
        print(f"  🔹 Invalid error_source error detected: {serializer.errors.get('error_source')}")
    
    def test_null_error_source_is_valid(self):
        """Test that null error source is valid"""
        data = {
            'message': 'Test message',
            'type': LogType.INFO.value,
            'code': 200,
            'error_source': None
        }
        serializer = DebugLogSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.validated_data['error_source'])
        print("  🔹 Confirmed null error_source is valid")
    
    def test_default_user_type(self):
        """Test default user_type is set correctly"""
        data = {
            'message': 'Test message',
            'type': LogType.SUCCESS.value,
            'code': 201
            # No user_type specified
        }
        serializer = DebugLogSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user_type'], UserType.USER.value)
        print(f"  🔹 Default user_type: {serializer.validated_data['user_type']}")


# This will run if this file is executed directly
if __name__ == '__main__':
    print("Running DebugLogSerializerTest...")
    run_test_with_output(DebugLogSerializerTest)