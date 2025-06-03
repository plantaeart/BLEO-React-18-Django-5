from tests.base_test import BLEOBaseTest, run_test_with_output
from rest_framework.test import APIClient
from models.AppParameters import AppParameters
from models.enums.DebugType import DebugType
from utils.mongodb_utils import MongoDB
import json
import time
import random
from django.urls import path
from django.test import override_settings
from api.Views.AppParameters.AppParametersView import AppParametersView, AppParameterDetailView

# Set up URL configuration for testing
urlpatterns = [
    path('app-parameters/', AppParametersView.as_view(), name='app-parameters'),
    path('app-parameters/<str:param_name>/', AppParameterDetailView.as_view(), name='app-parameter-detail'),
]

@override_settings(ROOT_URLCONF=__name__)
class AppParametersViewTest(BLEOBaseTest):
    """Test cases for application parameters view endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        super().setUpClass()
        # Create MongoDB connection with test collections
        cls.db_client = MongoDB.get_client()
        
        # Use test collections with timestamp to avoid conflicts
        timestamp = int(time.time())
        cls.test_suffix = f"test_{timestamp}_{random.randint(1000, 9999)}"
        cls.app_params_collection_name = f"AppParameters_{cls.test_suffix}"
        
        # Store original collection name to restore later
        cls.original_app_params_collection = MongoDB.COLLECTIONS['AppParameters']
        
        # Override collection name for testing
        MongoDB.COLLECTIONS['AppParameters'] = cls.app_params_collection_name
        
        print(f"🔧 Created test collection: {cls.app_params_collection_name}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Use the MongoDB instance to get the database
            db = MongoDB.get_instance().get_db()
            
            # Drop test collection
            db.drop_collection(cls.app_params_collection_name)
            
            # Restore original collection name
            MongoDB.COLLECTIONS['AppParameters'] = cls.original_app_params_collection
            
            print(f"🧹 Dropped test collection: {cls.app_params_collection_name}")
        except Exception as e:
            print(f"❌ Error during teardown: {str(e)}")
        finally:
            super().tearDownClass()
    
    def setUp(self):
        """Set up the test environment before each test"""
        super().setUp()
        # Use APIClient for testing
        self.client = APIClient()
        
        try:
            # Get test collection
            self.db_params = MongoDB.get_instance().get_collection('AppParameters')
            
            # Clear collection before each test
            self.db_params.delete_many({})
            
            # Create sample test parameters
            self.test_params = [
                {
                    'id': 1,
                    'param_name': AppParameters.PARAM_DEBUG_LEVEL,
                    'param_value': DebugType.DEBUG.value
                },
                {
                    'id': 2,
                    'param_name': AppParameters.PARAM_APP_VERSION,
                    'param_value': '1.0.0'
                },
                {
                    'id': 3,
                    'param_name': 'max_retries',
                    'param_value': 5
                }
            ]
            
            # Insert test parameters
            for param in self.test_params:
                self.db_params.insert_one(param)
                print(f"  ✅ Created test parameter: {param['param_name']} = {param['param_value']}")
            
            print(f"🔧 Test environment setup with {len(self.test_params)} parameters")
            
        except Exception as e:
            print(f"❌ Test setup failed: {str(e)}")
            raise
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear collection
        self.db_params.delete_many({})
        super().tearDown()
    
    # ====== AppParametersView Tests ======
    
    def test_get_all_parameters(self):
        """Test getting all application parameters"""
        # Make request
        response = self.client.get('/app-parameters/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['parameters']), 3)
        
        # Check specific parameter values
        params_dict = {p['param_name']: p['param_value'] for p in response.data['data']['parameters']}
        self.assertEqual(params_dict[AppParameters.PARAM_DEBUG_LEVEL], DebugType.DEBUG.value)
        self.assertEqual(params_dict[AppParameters.PARAM_APP_VERSION], '1.0.0')
        self.assertEqual(params_dict['max_retries'], 5)
        
        print("  🔹 Successfully retrieved all parameters")
    
    def test_get_parameter_by_name(self):
        """Test getting a specific parameter by name"""
        # Make request
        response = self.client.get(f'/app-parameters/{AppParameters.PARAM_APP_VERSION}/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['param_name'], AppParameters.PARAM_APP_VERSION)
        self.assertEqual(response.data['data']['param_value'], '1.0.0')
        
        print("  🔹 Successfully retrieved parameter by name")
    
    def test_get_nonexistent_parameter(self):
        """Test getting a nonexistent parameter"""
        # Make request
        response = self.client.get('/app-parameters/nonexistent_param/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorMessage'], 'Parameter nonexistent_param not found')
        
        print("  🔹 Properly handled nonexistent parameter")
    
    def test_create_new_parameter(self):
        """Test creating a new parameter"""
        # Request data
        param_data = {
            'param_name': 'new_timeout',
            'param_value': 30
        }
        
        # Make request
        response = self.client.post('/app-parameters/', param_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['successMessage'])
        self.assertEqual(response.data['data']['param_name'], 'new_timeout')
        
        # Verify parameter was created in database
        created_param = self.db_params.find_one({'param_name': 'new_timeout'})
        self.assertIsNotNone(created_param)
        self.assertEqual(created_param['param_value'], 30)
        
        print("  🔹 Successfully created new parameter")
    
    def test_create_parameter_invalid_data(self):
        """Test creating a parameter with invalid data"""
        # Missing param_value
        param_data = {
            'param_name': 'invalid_param'
            # Missing param_value
        }
        
        # Make request
        response = self.client.post('/app-parameters/', param_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(response.data['successMessage'])
        self.assertIn('param_value', response.data['validationErrors'])
        
        print("  🔹 Properly rejected invalid parameter data")
    
    def test_update_parameter(self):
        """Test updating an existing parameter"""
        # Request data for update
        update_data = {
            'param_value': DebugType.NO_DEBUG.value
        }
        
        # Make request
        response = self.client.put(f'/app-parameters/{AppParameters.PARAM_DEBUG_LEVEL}/', 
                                  update_data, format='json')
        
        print(f"Test : {response.data}")

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['successMessage'])
        self.assertEqual(response.data['data']['param_name'], AppParameters.PARAM_DEBUG_LEVEL)
        self.assertEqual(response.data['data']['param_value'], DebugType.NO_DEBUG.value)
        
        # Verify parameter was updated in database
        updated_param = self.db_params.find_one({'param_name': AppParameters.PARAM_DEBUG_LEVEL})
        self.assertEqual(updated_param['param_value'], DebugType.NO_DEBUG.value)
        
        print("  🔹 Successfully updated parameter")
    
    def test_update_nonexistent_parameter(self):
        """Test updating a nonexistent parameter"""
        # Request data
        update_data = {
            'param_value': 'new_value'
        }
        
        # Make request
        response = self.client.put('/app-parameters/nonexistent_param/', 
                                  update_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorMessage'], 'Parameter nonexistent_param not found')
        
        print("  🔹 Properly handled updating nonexistent parameter")
    
    def test_delete_parameter(self):
        """Test deleting a parameter"""
        # Make request
        response = self.client.delete(f'/app-parameters/max_retries/')
        
        # Check response
        self.assertEqual(response.status_code, 204)
        
        # Verify parameter was deleted from database
        deleted_param = self.db_params.find_one({'param_name': 'max_retries'})
        self.assertIsNone(deleted_param)
        
        print("  🔹 Successfully deleted parameter")
    
    def test_delete_nonexistent_parameter(self):
        """Test deleting a nonexistent parameter"""
        # Make request
        response = self.client.delete('/app-parameters/nonexistent_param/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['errorMessage'], 'Parameter nonexistent_param not found')
        
        print("  🔹 Properly handled deleting nonexistent parameter")
    
    def test_create_duplicate_parameter(self):
        """Test creating a parameter that already exists"""
        # Request data for existing parameter
        param_data = {
            'param_name': AppParameters.PARAM_DEBUG_LEVEL,
            'param_value': DebugType.NO_DEBUG.value
        }
        
        # Make request
        response = self.client.post('/app-parameters/', param_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 409)
        self.assertIsNone(response.data['successMessage'])
        self.assertEqual(response.data['errorMessage'], f"Parameter {AppParameters.PARAM_DEBUG_LEVEL} already exists")
        
        print("  🔹 Properly rejected duplicate parameter creation")
    
    def test_validate_debug_level_value(self):
        """Test validation of debug_level parameter value"""
        # Make valid update request
        response = self.client.put(f'/app-parameters/{AppParameters.PARAM_DEBUG_LEVEL}/', 
                                  {'param_value': DebugType.NO_DEBUG.value}, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['successMessage'])
        
        # Invalid debug level
        response = self.client.put(f'/app-parameters/{AppParameters.PARAM_DEBUG_LEVEL}/', 
                                  {'param_value': 'INVALID_LEVEL'}, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(response.data['successMessage'])
        self.assertIn('param_value', response.data['validationErrors'])
        
        print("  🔹 Debug level parameter validation working correctly")
    
    def test_complex_json_parameter(self):
        """Test handling complex JSON parameter values"""
        # Complex JSON value
        complex_data = {
            'param_name': 'user_settings',
            'param_value': {
                'theme': 'dark',
                'notifications': {
                    'email': True,
                    'push': False
                },
                'preferences': ['dashboard', 'reports', 'analytics']
            }
        }
        
        # Make request
        response = self.client.post('/app-parameters/', complex_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['successMessage'])
        
        # Get the parameter back
        response = self.client.get('/app-parameters/user_settings/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['param_name'], 'user_settings')
        self.assertEqual(response.data['data']['param_value']['theme'], 'dark')
        self.assertEqual(response.data['data']['param_value']['notifications']['email'], True)
        self.assertEqual(response.data['data']['param_value']['preferences'], ['dashboard', 'reports', 'analytics'])
        
        print("  🔹 Successfully handled complex JSON parameter values")


# This will run if this file is executed directly
if __name__ == '__main__':
    print("Running AppParametersViewTest...")
    run_test_with_output(AppParametersViewTest)