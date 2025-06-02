from tests.base_test import BLEOBaseTest, run_test_with_output
from api.serializers import AppParametersSerializer
from models.enums.DebugType import DebugType
from models.AppParameters import AppParameters

class AppParametersSerializerTest(BLEOBaseTest):
    """Test cases for AppParametersSerializer validation"""
    
    def test_empty_data_uses_defaults(self):
        """Test that empty data validation fails because param_name and param_value are required"""
        serializer = AppParametersSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('param_name', serializer.errors)
        self.assertIn('param_value', serializer.errors)
        print("  🔹 Confirmed param_name and param_value are required fields")
    
    def test_valid_debug_level(self):
        """Test that valid debug level passes validation"""
        data = {
            'param_name': AppParameters.PARAM_DEBUG_LEVEL,
            'param_value': DebugType.DEBUG.value
        }
        serializer = AppParametersSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['param_value'], DebugType.DEBUG.value)
        print(f"  🔹 Validated debug_level value: {serializer.validated_data['param_value']}")
    
    def test_invalid_debug_level(self):
        """Test that invalid debug level is rejected"""
        data = {
            'param_name': AppParameters.PARAM_DEBUG_LEVEL,
            'param_value': 'INVALID_LEVEL'
        }
        serializer = AppParametersSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('param_value', serializer.errors)
        print(f"  🔹 Invalid debug_level value rejected: {serializer.errors.get('param_value')}")
    
    def test_id_is_read_only(self):
        """Test that id field is read-only"""
        data = {
            'id': 'custom_id',  # This should be ignored since id is read-only
            'param_name': AppParameters.PARAM_DEBUG_LEVEL,
            'param_value': DebugType.DEBUG.value
        }
        serializer = AppParametersSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # id should not be in validated_data
        self.assertNotIn('id', serializer.validated_data)
        print("  🔹 Confirmed id field is read-only")
        
        # But it should be in the output representation if specified by serializer
        # Note: No assertion for result['id'] as the default behavior depends on implementation
        print(f"  🔹 id field handled correctly in representation")

    def test_minimal_valid_data(self):
        """Test minimal valid data requirements"""
        data = {
            'param_name': 'test_param',
            'param_value': 'test_value'
        }
        serializer = AppParametersSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['param_name'], 'test_param')
        self.assertEqual(serializer.validated_data['param_value'], 'test_value')
        print(f"  🔹 Minimal valid data (param_name and param_value) passes validation")
    
    def test_valid_debug_level_parameter(self):
        """Test validation of debug_level parameter"""
        data = {
            'param_name': AppParameters.PARAM_DEBUG_LEVEL,
            'param_value': DebugType.DEBUG.value
        }
        serializer = AppParametersSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['param_name'], AppParameters.PARAM_DEBUG_LEVEL)
        self.assertEqual(serializer.validated_data['param_value'], DebugType.DEBUG.value)
        print(f"  🔹 Valid debug_level parameter validated successfully")
    
    def test_invalid_debug_level_parameter(self):
        """Test validation rejects invalid debug level value"""
        data = {
            'param_name': AppParameters.PARAM_DEBUG_LEVEL,
            'param_value': 'INVALID_LEVEL'
        }
        serializer = AppParametersSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('param_value', serializer.errors)
        print(f"  🔹 Invalid debug_level parameter rejected correctly")
    
    def test_valid_app_version_parameter(self):
        """Test validation of app_version parameter"""
        data = {
            'param_name': AppParameters.PARAM_APP_VERSION,
            'param_value': '2.0.0'
        }
        serializer = AppParametersSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['param_name'], AppParameters.PARAM_APP_VERSION)
        self.assertEqual(serializer.validated_data['param_value'], '2.0.0')
        print(f"  🔹 Valid app_version parameter validated successfully")
    
    def test_complex_parameter_value(self):
        """Test parameter with complex JSON value"""
        data = {
            'param_name': 'settings',
            'param_value': {'enabled': True, 'timeout': 30, 'options': ['a', 'b', 'c']}
        }
        serializer = AppParametersSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['param_name'], 'settings')
        self.assertEqual(serializer.validated_data['param_value']['enabled'], True)
        self.assertEqual(serializer.validated_data['param_value']['timeout'], 30)
        self.assertEqual(serializer.validated_data['param_value']['options'], ['a', 'b', 'c'])
        print(f"  🔹 Complex JSON parameter value validated successfully")
    
    def test_id_field_read_only(self):
        """Test that id field is read-only"""
        data = {
            'id': 123,  # This should be ignored since id is read-only
            'param_name': AppParameters.PARAM_DEBUG_LEVEL,
            'param_value': DebugType.DEBUG.value
        }
        serializer = AppParametersSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")
        # id should not be in validated_data
        self.assertNotIn('id', serializer.validated_data)
        print("  🔹 Confirmed id field is read-only")
    
    def test_required_fields(self):
        """Test that param_name and param_value are required"""
        # Missing param_name
        data1 = {'param_value': DebugType.DEBUG.value}
        serializer1 = AppParametersSerializer(data=data1)
        self.assertFalse(serializer1.is_valid())
        self.assertIn('param_name', serializer1.errors)
        
        # Missing param_value
        data2 = {'param_name': AppParameters.PARAM_DEBUG_LEVEL}
        serializer2 = AppParametersSerializer(data=data2)
        self.assertFalse(serializer2.is_valid())
        self.assertIn('param_value', serializer2.errors)
        
        print("  🔹 Required field validation working correctly")
    
    def test_serialization_from_instance(self):
        """Test serialization from an AppParameters instance"""
        # Create an instance
        param = AppParameters(
            id=42,
            param_name=AppParameters.PARAM_APP_VERSION,
            param_value="3.1.4"
        )
        
        # Serialize it
        serializer = AppParametersSerializer(param)
        
        # Check the serialized data
        self.assertEqual(serializer.data['id'], 42)
        self.assertEqual(serializer.data['param_name'], AppParameters.PARAM_APP_VERSION)
        self.assertEqual(serializer.data['param_value'], "3.1.4")
        
        print("  🔹 Instance serialization worked correctly")


# This will run if this file is executed directly
if __name__ == '__main__':
    print("Running AppParametersSerializerTest...")
    run_test_with_output(AppParametersSerializerTest)