import unittest
from datetime import datetime
from models.DebugLogs import DebugLogs
from models.enums.UserType import UserType
from models.enums.LogType import LogType
from models.enums.ErrorSourceType import ErrorSourceType
from tests.base_test import BLEOBaseTest

class TestDebugLogs(BLEOBaseTest):
    """Test case for the DebugLogs model"""
    
    def test_init_with_required_params(self):
        """Test initialization with only required parameters"""
        log = DebugLogs(
            message="Test message",
            type=LogType.INFO.value,
            code=200
        )
        
        self.assertEqual(log.id, 0)
        self.assertEqual(log.message, "Test message")
        self.assertEqual(log.type, LogType.INFO.value)
        self.assertEqual(log.code, 200)
        self.assertEqual(log.user_type, UserType.SYSTEM.value)
        self.assertIsNone(log.BLEOId)
        self.assertIsNone(log.error_source)
        self.assertIsInstance(log.date, datetime)
    
    def test_init_with_all_params(self):
        """Test initialization with all parameters"""
        test_date = datetime(2025, 5, 31, 14, 30, 0)
        
        log = DebugLogs(
            id=123,
            date=test_date,
            message="Full test message",
            type=LogType.WARNING.value,
            code=400,
            BLEOId="TEST123",
            user_type=UserType.USER.value,
            error_source=ErrorSourceType.SERVER.value
        )
        
        self.assertEqual(log.id, 123)
        self.assertEqual(log.date, test_date)
        self.assertEqual(log.message, "Full test message")
        self.assertEqual(log.type, LogType.WARNING.value)
        self.assertEqual(log.code, 400)
        self.assertEqual(log.BLEOId, "TEST123")
        self.assertEqual(log.user_type, UserType.USER.value)
        self.assertEqual(log.error_source, ErrorSourceType.SERVER.value)
    
    def test_id_validation(self):
        """Test validation for id (cannot be None)"""
        with self.assertRaises(ValueError):
            DebugLogs(
                id=None,
                message="Invalid ID test",
                type=LogType.ERROR.value,
                code=500
            )
    
    def test_id_setter(self):
        """Test setter for id property"""
        log = DebugLogs(
            message="ID Setter Test",
            type=LogType.INFO.value,
            code=200
        )
        
        # Initial value
        self.assertEqual(log.id, 0)
        
        # Set new value
        log.id = 456
        self.assertEqual(log.id, 456)
        
        # Try setting to None (should raise ValueError)
        with self.assertRaises(ValueError):
            log.id = None
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        test_date = datetime(2025, 5, 31, 15, 45, 0)
        
        log = DebugLogs(
            id=789,
            date=test_date,
            message="Dict test",
            type=LogType.SUCCESS.value,
            code=200,
            BLEOId="USER456",
            user_type=UserType.USER.value,
            error_source=ErrorSourceType.SERVER.value
        )
        
        result = log.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], 789)
        self.assertEqual(result["date"], test_date)
        self.assertEqual(result["message"], "Dict test")
        self.assertEqual(result["type"], LogType.SUCCESS.value)
        self.assertEqual(result["code"], 200)
        self.assertEqual(result["BLEOId"], "USER456")
        self.assertEqual(result["user_type"], UserType.USER.value)
        self.assertEqual(result["error_source"], ErrorSourceType.SERVER.value)
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        test_date = datetime(2025, 5, 31, 16, 15, 0)
        
        data = {
            "id": 999,
            "date": test_date,
            "message": "From dict test",
            "type": LogType.ERROR.value,
            "code": 500,
            "BLEOId": "ADMIN789",
            "user_type": UserType.USER.value,
            "error_source": ErrorSourceType.SERVER.value
        }
        
        log = DebugLogs.from_dict(data)
        
        self.assertIsInstance(log, DebugLogs)
        self.assertEqual(log.id, 999)
        self.assertEqual(log.date, test_date)
        self.assertEqual(log.message, "From dict test")
        self.assertEqual(log.type, LogType.ERROR.value)
        self.assertEqual(log.code, 500)
        self.assertEqual(log.BLEOId, "ADMIN789")
        self.assertEqual(log.user_type, UserType.USER.value)
        self.assertEqual(log.error_source, ErrorSourceType.SERVER.value)
    
    def test_from_dict_validation(self):
        """Test from_dict validation (id and date required)"""
        # Missing ID
        with self.assertRaises(ValueError):
            DebugLogs.from_dict({
                "date": datetime.now(),
                "message": "Missing ID test"
            })
        
        # None ID
        with self.assertRaises(ValueError):
            DebugLogs.from_dict({
                "id": None,
                "date": datetime.now(),
                "message": "None ID test"
            })
        
        # Missing date
        with self.assertRaises(ValueError):
            DebugLogs.from_dict({
                "id": 123,
                "message": "Missing date test"
            })
        
        # None date
        with self.assertRaises(ValueError):
            DebugLogs.from_dict({
                "id": 123,
                "date": None,
                "message": "None date test"
            })
    
    def test_log_user_action(self):
        """Test log_user_action helper method"""
        log = DebugLogs.log_user_action(
            BLEOId="USER123",
            message="User action test",
            type=LogType.INFO.value,
            code=200
        )
        
        self.assertEqual(log.id, 0)
        self.assertEqual(log.BLEOId, "USER123")
        self.assertEqual(log.message, "User action test")
        self.assertEqual(log.type, LogType.INFO.value)
        self.assertEqual(log.code, 200)
        self.assertEqual(log.user_type, UserType.USER.value)
        self.assertIsNone(log.error_source)
        self.assertIsInstance(log.date, datetime)
    
    def test_log_system_action(self):
        """Test log_system_action helper method"""
        log = DebugLogs.log_system_action(
            message="System action test",
            type=LogType.INFO.value,
            code=200
        )
        
        self.assertEqual(log.id, 0)
        self.assertIsNone(log.BLEOId)
        self.assertEqual(log.message, "System action test")
        self.assertEqual(log.type, LogType.INFO.value)
        self.assertEqual(log.code, 200)
        self.assertEqual(log.user_type, UserType.SYSTEM.value)
        self.assertIsNone(log.error_source)
        self.assertIsInstance(log.date, datetime)
    
    def test_log_error(self):
        """Test log_error helper method"""
        # System error
        sys_error = DebugLogs.log_error(
            message="System error test",
            code=500,
            error_source=ErrorSourceType.SERVER.value
        )
        
        self.assertEqual(sys_error.id, 0)
        self.assertIsNone(sys_error.BLEOId)
        self.assertEqual(sys_error.message, "System error test")
        self.assertEqual(sys_error.type, LogType.ERROR.value)
        self.assertEqual(sys_error.code, 500)
        self.assertEqual(sys_error.user_type, UserType.SYSTEM.value)
        self.assertEqual(sys_error.error_source, ErrorSourceType.SERVER.value)
        
        # User error
        user_error = DebugLogs.log_error(
            message="User error test",
            code=400,
            BLEOId="USER456",
            error_source=ErrorSourceType.SERVER.value
        )
        
        self.assertEqual(user_error.id, 0)
        self.assertEqual(user_error.BLEOId, "USER456")
        self.assertEqual(user_error.message, "User error test")
        self.assertEqual(user_error.type, LogType.ERROR.value)
        self.assertEqual(user_error.code, 400)
        self.assertEqual(user_error.user_type, UserType.USER.value)
        self.assertEqual(user_error.error_source, ErrorSourceType.SERVER.value)
    
    def test_log_success(self):
        """Test log_success helper method"""
        # System success
        sys_success = DebugLogs.log_success(
            message="System success test",
            code=200
        )
        
        self.assertEqual(sys_success.id, 0)
        self.assertIsNone(sys_success.BLEOId)
        self.assertEqual(sys_success.message, "System success test")
        self.assertEqual(sys_success.type, LogType.SUCCESS.value)
        self.assertEqual(sys_success.code, 200)
        self.assertEqual(sys_success.user_type, UserType.SYSTEM.value)
        
        # User success
        user_success = DebugLogs.log_success(
            message="User success test",
            code=201,
            BLEOId="USER789"
        )
        
        self.assertEqual(user_success.id, 0)
        self.assertEqual(user_success.BLEOId, "USER789")
        self.assertEqual(user_success.message, "User success test")
        self.assertEqual(user_success.type, LogType.SUCCESS.value)
        self.assertEqual(user_success.code, 201)
        self.assertEqual(user_success.user_type, UserType.USER.value)


if __name__ == "__main__":
    unittest.main()