import unittest
from models.AppParameters import AppParameters
from models.enums.DebugType import DebugType
from tests.base_test import BLEOBaseTest, run_test_with_output

class TestAppParameters(BLEOBaseTest):
    """Test case for the AppParameters model"""
    
    def test_init_debug_level_parameter(self):
        """Test initialization of debug_level parameter"""
        param = AppParameters(
            param_name=AppParameters.PARAM_DEBUG_LEVEL,
            param_value=DebugType.DEBUG.value,
            id=0
        )
        
        self.assertEqual(param.id, 0)
        self.assertEqual(param.param_name, "debug_level")
        self.assertEqual(param.param_value, DebugType.DEBUG.value)
        
        print("  🔹 Debug level parameter initialized correctly with ID=0")
    
    def test_init_app_version_parameter(self):
        """Test initialization of app_version parameter"""
        param = AppParameters(
            param_name=AppParameters.PARAM_APP_VERSION,
            param_value="2.1.3",
            id=1
        )
        
        self.assertEqual(param.id, 1)
        self.assertEqual(param.param_name, "app_version")
        self.assertEqual(param.param_value, "2.1.3")
        
        print("  🔹 App version parameter initialized correctly with ID=1")
    
    def test_init_without_id(self):
        """Test initialization without specifying id"""
        param = AppParameters(
            param_name="test_param",
            param_value="test_value"
        )
        
        self.assertIsNone(param.id)
        self.assertEqual(param.param_name, "test_param")
        self.assertEqual(param.param_value, "test_value")
        
        print("  🔹 Parameter created successfully with None ID")
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        param = AppParameters(
            param_name=AppParameters.PARAM_DEBUG_LEVEL,
            param_value=DebugType.NO_DEBUG.value,
            id=5
        )
        
        result = param.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], 5)
        self.assertEqual(result["param_name"], AppParameters.PARAM_DEBUG_LEVEL)
        self.assertEqual(result["param_value"], DebugType.NO_DEBUG.value)
        
        print("  🔹 Parameter converted to dictionary successfully")
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "id": 10,
            "param_name": AppParameters.PARAM_APP_VERSION,
            "param_value": "3.0.0"
        }
        
        param = AppParameters.from_dict(data)
        
        self.assertIsInstance(param, AppParameters)
        self.assertEqual(param.id, 10)
        self.assertEqual(param.param_name, AppParameters.PARAM_APP_VERSION)
        self.assertEqual(param.param_value, "3.0.0")
        
        print("  🔹 Parameter created from dictionary with correct values")
    
    def test_from_dict_with_missing_values(self):
        """Test creation from dictionary with missing values"""
        data = {
            # Missing id - should be None
            "param_name": "custom_setting", 
            "param_value": True
        }
        
        param = AppParameters.from_dict(data)
        
        self.assertIsNone(param.id)
        self.assertEqual(param.param_name, "custom_setting")
        self.assertEqual(param.param_value, True)
        
        print("  🔹 Parameter created with missing values handled correctly")


# This will run if this file is executed directly
if __name__ == "__main__":
    run_test_with_output(TestAppParameters)