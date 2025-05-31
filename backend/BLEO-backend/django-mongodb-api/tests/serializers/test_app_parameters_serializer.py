from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import AppParametersSerializer
from models.enums.DebugType import DebugType

class AppParametersSerializerTest(BLEOBaseTest):
    """Test cases for AppParametersSerializer validation"""
    
    def test_empty_data_uses_defaults(self):
        """Test that empty data uses default values"""
        serializer = AppParametersSerializer(data={})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['debug_level'], DebugType.NO_DEBUG.value)
        self.assertEqual(serializer.validated_data['app_version'], "1.0.0")
        print(f"  🔹 Default debug_level: {serializer.validated_data['debug_level']}")
        print(f"  🔹 Default app_version: {serializer.validated_data['app_version']}")
    
    def test_valid_debug_level(self):
        """Test that valid debug level passes validation"""
        data = {
            'debug_level': DebugType.DEBUG.value,
            'app_version': '2.0.0'
        }
        serializer = AppParametersSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['debug_level'], DebugType.DEBUG.value)
        print(f"  🔹 Validated debug_level: {serializer.validated_data['debug_level']}")
    
    def test_invalid_debug_level(self):
        """Test that invalid debug level is rejected"""
        data = {
            'debug_level': 'INVALID_LEVEL',
            'app_version': '1.5.0'
        }
        serializer = AppParametersSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('debug_level', serializer.errors)
        print(f"  🔹 Invalid debug_level error detected: {serializer.errors.get('debug_level')}")
    
    def test_id_is_read_only(self):
        """Test that id field is read-only"""
        data = {
            'id': 'custom_id',  # This should be ignored since id is read-only
            'debug_level': DebugType.DEBUG.value,
            'app_version': '1.0.0'
        }
        serializer = AppParametersSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # id should not be in validated_data
        self.assertNotIn('id', serializer.validated_data)
        print("  🔹 Confirmed id field is read-only")
        
        # But it should be in the output representation
        result = serializer.data
        self.assertEqual(result['id'], 'app_parameters')
        print(f"  🔹 Default id in representation: {result['id']}")


# This will run if this file is executed directly
if __name__ == '__main__':
    print("Running AppParametersSerializerTest...")
    run_test_with_output(AppParametersSerializerTest)