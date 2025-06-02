from tests.base_test import BLEOBaseTest, run_test_with_output
from rest_framework.test import APIClient
from api.Views.DebugLogs.DebugLogViews import LoggingView, AdminLogsView, AdminLogDetailView
from models.enums.LogType import LogType
from utils.mongodb_utils import MongoDB
import json
import time
import random
from datetime import datetime, timedelta
from django.urls import path
from django.test import override_settings
from utils.logger import Logger
from models.enums.UserType import UserType
from models.enums.ErrorSourceType import ErrorSourceType
from models.enums.DebugType import DebugType
from models.AppParameters import AppParameters

# Set up URL configuration for testing
urlpatterns = [
    path('logs/', LoggingView.as_view(), name='log-create'),
    path('admin/logs/', AdminLogsView.as_view(), name='admin-logs'),
    path('admin/logs/<str:log_id>/', AdminLogDetailView.as_view(), name='admin-log-detail'),
]

@override_settings(ROOT_URLCONF=__name__)
class DebugLogViewsTest(BLEOBaseTest):
    """Test cases for debug log view endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        super().setUpClass()
        # Create MongoDB connection with test collections
        cls.db_client = MongoDB.get_client()
        
        # Use test collections with timestamp to avoid conflicts
        timestamp = int(time.time())
        cls.test_suffix = f"test_{timestamp}_{random.randint(1000, 9999)}"
        cls.debug_logs_collection_name = f"DebugLogs_{cls.test_suffix}"
        cls.app_params_collection_name = f"AppParameters_{cls.test_suffix}"
        
        # Store original collection names to restore later
        cls.original_debug_logs_collection = MongoDB.COLLECTIONS['DebugLogs']
        cls.original_app_params_collection = MongoDB.COLLECTIONS['AppParameters']
        
        # Override collection names for testing
        MongoDB.COLLECTIONS['DebugLogs'] = cls.debug_logs_collection_name
        MongoDB.COLLECTIONS['AppParameters'] = cls.app_params_collection_name
        
        print(f"🔧 Created test collections: {cls.debug_logs_collection_name}, {cls.app_params_collection_name}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        try:
            # Use the MongoDB instance to get the database
            db = MongoDB.get_instance().get_db()
            
            # Drop test collections
            db.drop_collection(cls.debug_logs_collection_name)
            db.drop_collection(cls.app_params_collection_name)
            
            # Restore original collection names
            MongoDB.COLLECTIONS['DebugLogs'] = cls.original_debug_logs_collection
            MongoDB.COLLECTIONS['AppParameters'] = cls.original_app_params_collection
            
            print(f"🧹 Dropped test collections: {cls.debug_logs_collection_name}, {cls.app_params_collection_name}")
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
            # Get test collections
            self.db_logs = MongoDB.get_instance().get_collection('DebugLogs')
            self.db_params = MongoDB.get_instance().get_collection('AppParameters')
            
            # Clear collections before each test
            self.db_logs.delete_many({})
            self.db_params.delete_many({})
            
            # Create AppParameters document with debug enabled using the new model structure
            debug_param = {
                'param_name': AppParameters.PARAM_DEBUG_LEVEL,
                'param_value': DebugType.DEBUG.value
            }
            self.db_params.insert_one(debug_param)
            
            # Add version parameter (optional but consistent with the model)
            version_param = {
                'param_name': AppParameters.PARAM_APP_VERSION,
                'param_value': '1.0.0'
            }
            self.db_params.insert_one(version_param)
            
            # Create sample test logs
            now = datetime.now()
            self.test_logs = [
                {
                    'id': 1001,
                    'BLEOId': 'USER1',
                    'message': 'Test user action log',
                    'type': LogType.INFO.value,
                    'code': 200,
                    'user_type': UserType.USER.value,
                    'date': now - timedelta(days=1)
                },
                {
                    'id': 1002,
                    'BLEOId': 'USER2',
                    'message': 'Test error log',
                    'type': LogType.ERROR.value,
                    'code': 500,
                    'error_source': ErrorSourceType.APPLICATION.value,
                    'user_type': UserType.USER.value,
                    'date': now - timedelta(hours=12)
                },
                {
                    'id': 1003,
                    'message': 'Test system log',
                    'type': LogType.INFO.value, 
                    'code': 0,
                    'user_type': UserType.SYSTEM.value,
                    'date': now - timedelta(hours=1)
                }
            ]
            
            # Insert test logs
            self.log_ids = []
            for i, log in enumerate(self.test_logs):
                result = self.db_logs.insert_one(log)
                self.log_ids.append(result.inserted_id)
                print(f"  ✅ Created test log {i+1}: {log['id']}")
            
            print(f"🔧 Test environment setup with {len(self.log_ids)} logs")
            
        except Exception as e:
            print(f"❌ Test setup failed: {str(e)}")
            raise
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear collections
        self.db_logs.delete_many({})
        super().tearDown()
    
    # ====== LoggingView Tests ======
    
    def test_create_log_success(self):
        """Test creating a new log entry successfully"""
        # Request data for user action log
        log_data = {
            'BLEOId': 'TEST_USER',
            'message': 'User performed an action',
            'type': LogType.INFO.value,
            'code': 200
        }
        
        # Make request
        response = self.client.post('/logs/', log_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['success'])
        self.assertIsNotNone(response.data['log_id'])
        
        # Verify log was created in database
        log_count = self.db_logs.count_documents({})
        self.assertEqual(log_count, len(self.test_logs) + 1)
        
        print("  🔹 Successfully created user action log")
    
    def test_create_error_log(self):
        """Test creating an error log entry"""
        # Request data for error log
        log_data = {
            'BLEOId': 'TEST_USER',
            'message': 'Something went wrong',
            'type': LogType.ERROR.value,
            'code': 500,
            'error_source': ErrorSourceType.APPLICATION.value
        }
        
        # Make request
        response = self.client.post('/logs/', log_data, format='json')

        print(f"response data: {json.dumps(response.data, indent=2)}")
             
        # Check response
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['success'])
        self.assertIsNotNone(response.data['log_id'])
        
        # Verify log was created in database with correct type
        created_log = self.db_logs.find_one({'message': 'Something went wrong'})
        self.assertIsNotNone(created_log)
        self.assertEqual(created_log['type'], LogType.ERROR.value)
        self.assertEqual(created_log['error_source'], ErrorSourceType.APPLICATION.value)
        
        print("  🔹 Successfully created error log")
    
    def test_create_log_invalid_data(self):
        """Test error when creating log with invalid data"""
        # Request data missing required fields
        log_data = {
            'BLEOId': 'TEST_USER'
            # Missing message, type, and code
        }
        
        # Make request
        response = self.client.post('/logs/', log_data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Invalid log data')
        self.assertIn('message', response.data['details'])
        self.assertIn('type', response.data['details'])
        self.assertIn('code', response.data['details'])
        
        print("  🔹 Properly rejected invalid log data")
    
    # ====== AdminLogsView Tests ======
    
    def test_get_all_logs(self):
        """Test getting all logs"""
        # Make request
        response = self.client.get('/admin/logs/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['logs']), 3)
        self.assertEqual(response.data['total'], 3)
        
        print("  🔹 Successfully retrieved all logs")
    
    def test_filter_logs_by_type(self):
        """Test filtering logs by type"""
        # Make request
        response = self.client.get('/admin/logs/', {'type': LogType.ERROR.value})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['logs']), 1)
        self.assertEqual(response.data['logs'][0]['type'], LogType.ERROR.value)
        self.assertEqual(response.data['total'], 1)
        
        print("  🔹 Successfully filtered logs by type")
    
    def test_filter_logs_by_bleoid(self):
        """Test filtering logs by BLEOId"""
        # Make request
        response = self.client.get('/admin/logs/', {'bleoid': 'USER1'})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['logs']), 1)
        self.assertEqual(response.data['logs'][0]['BLEOId'], 'USER1')
        self.assertEqual(response.data['total'], 1)
        
        print("  🔹 Successfully filtered logs by BLEOId")
    
    def test_filter_logs_by_days(self):
        """Test filtering logs by days"""
        # Get logs from the last day
        response = self.client.get('/admin/logs/', {'days': '1'})
        
        # Check response - should include 2 logs (the ones from last 12 hours and 1 hour)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['logs']), 2)
        self.assertEqual(response.data['total'], 2)
        
        print("  🔹 Successfully filtered logs by days")
    
    def test_pagination(self):
        """Test log pagination"""
        # Add more logs to test pagination
        now = datetime.now()
        for i in range(10):
            self.db_logs.insert_one({
                'id': 2000 + i,
                'message': f'Pagination test log {i}',
                'type': LogType.INFO.value,
                'user_type': UserType.USER.value,
                'code': 200,
                'date': now + timedelta(minutes=i)
            })
        
        # Get first page with limit 5 and explicit sort
        response = self.client.get('/admin/logs/', {'limit': '5', 'skip': '0', 'sort_by': 'id'})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['logs']), 5)
        self.assertEqual(response.data['total'], 13)  # 3 original + 10 new
        
        # Get second page with same sorting parameter
        response2 = self.client.get('/admin/logs/', {'limit': '5', 'skip': '5', 'sort_by': 'id'})
        
        # Check second page
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.data['logs']), 5)
        
        # Make sure pages have different logs
        first_page_ids = [log['id'] for log in response.data['logs']]
        second_page_ids = [log['id'] for log in response2.data['logs']]
        
        for log_id in second_page_ids:
            self.assertNotIn(log_id, first_page_ids)
        
        print("  🔹 Successfully tested pagination")
    
    # ====== AdminLogDetailView Tests ======
    
    def test_get_log_by_id(self):
        """Test getting a specific log by ID"""
        # Make request
        response = self.client.get('/admin/logs/1001/')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], 1001)
        self.assertEqual(response.data['BLEOId'], 'USER1')
        self.assertEqual(response.data['type'], LogType.INFO.value)
        
        print("  🔹 Successfully retrieved log by ID")
    
    def test_get_nonexistent_log(self):
        """Test error when getting a nonexistent log"""
        # Make request with nonexistent ID
        response = self.client.get('/admin/logs/9999/')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'Log with ID 9999 not found')
        
        print("  🔹 Properly handled nonexistent log")
    
    def test_get_log_invalid_id(self):
        """Test error when getting a log with invalid ID format"""
        # Make request with invalid ID format
        response = self.client.get('/admin/logs/invalid/')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Invalid log ID format')
        
        print("  🔹 Properly rejected invalid log ID format")
    
    def test_filter_logs_by_user_type(self):
        """Test filtering logs by user_type"""
        # Make request
        response = self.client.get('/admin/logs/', {'user_type': UserType.SYSTEM.value})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['logs']), 1)
        self.assertEqual(response.data['logs'][0]['user_type'], UserType.SYSTEM.value)
        self.assertEqual(response.data['total'], 1)
        
        print("  🔹 Successfully filtered logs by user_type")
    
    def test_filter_logs_by_error_source(self):
        """Test filtering logs by error_source"""
        # Make request
        response = self.client.get('/admin/logs/', {'error_source': ErrorSourceType.APPLICATION.value})
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['logs']), 1)
        self.assertEqual(response.data['logs'][0]['error_source'], ErrorSourceType.APPLICATION.value)
        self.assertEqual(response.data['total'], 1)
        
        print("  🔹 Successfully filtered logs by error_source")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(DebugLogViewsTest)