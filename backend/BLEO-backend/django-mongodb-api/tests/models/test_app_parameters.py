import unittest
from models.AppParameters import AppParameters
from models.enums.DebugType import DebugType

class TestAppParameters(unittest.TestCase):
    """Test case for the AppParameters model"""
    
    def test_init_with_defaults(self):
        """Test initialization with default values"""
        app_params = AppParameters()
        
        self.assertEqual(app_params.id, "app_parameters")
        self.assertEqual(app_params.debug_level, DebugType.DEBUG.value)
        self.assertEqual(app_params.app_version, "1.0.0")
    
    def test_init_with_custom_values(self):
        """Test initialization with custom values"""
        app_params = AppParameters(
            debug_level=DebugType.NO_DEBUG.value,
            app_version="2.1.3",
            id="custom_params"
        )
        
        self.assertEqual(app_params.id, "custom_params")
        self.assertEqual(app_params.debug_level, DebugType.NO_DEBUG.value)
        self.assertEqual(app_params.app_version, "2.1.3")
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        app_params = AppParameters(
            debug_level=DebugType.NO_DEBUG.value,
            app_version="1.5.0"
        )
        
        result = app_params.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "app_parameters")
        self.assertEqual(result["debug_level"], DebugType.NO_DEBUG.value)
        self.assertEqual(result["app_version"], "1.5.0")
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "id": "test_params",
            "debug_level": DebugType.NO_DEBUG.value,
            "app_version": "3.0.0"
        }
        
        app_params = AppParameters.from_dict(data)
        
        self.assertIsInstance(app_params, AppParameters)
        self.assertEqual(app_params.id, "test_params")
        self.assertEqual(app_params.debug_level, DebugType.NO_DEBUG.value)
        self.assertEqual(app_params.app_version, "3.0.0")
    
    def test_from_dict_with_missing_values(self):
        """Test creation from dictionary with missing values"""
        data = {
            # Missing id, debug_level and app_version - should use defaults
        }
        
        app_params = AppParameters.from_dict(data)
        
        self.assertEqual(app_params.id, "app_parameters")
        self.assertEqual(app_params.debug_level, DebugType.DEBUG.value)
        self.assertEqual(app_params.app_version, "1.0.0")


if __name__ == "__main__":
    unittest.main()