from tests.base_test import BLEOBaseTest, run_test_with_output
from models.response.BLEOResponse import BLEOResponse
from rest_framework import status
from rest_framework.response import Response

class BLEOResponseModelTest(BLEOBaseTest):
    """Test cases for BLEOResponse model"""
    
    def test_initialization_with_data(self):
        """Test BLEOResponse initialization with data"""
        data = {"id": 1, "name": "Test"}
        response = BLEOResponse(
            data=data,
            success_message="Data retrieved",
            error_type=None,
            error_message=None
        )
        
        # Check fields
        self.assertEqual(response.data, data)
        self.assertEqual(response.success_message, "Data retrieved")
        self.assertIsNone(response.error_type)
        self.assertIsNone(response.error_message)
        
        print("  🔹 BLEOResponse initialized with data and success message")
    
    def test_initialization_with_error(self):
        """Test BLEOResponse initialization with error"""
        response = BLEOResponse(
            data=None,
            success_message=None,
            error_type="ValidationError",
            error_message="Invalid data"
        )
        
        # Check fields
        self.assertIsNone(response.data)
        self.assertIsNone(response.success_message)
        self.assertEqual(response.error_type, "ValidationError")
        self.assertEqual(response.error_message, "Invalid data")
        
        print("  🔹 BLEOResponse initialized with error type and message")
    
    def test_to_dict_method(self):
        """Test BLEOResponse to_dict method returns correct structure"""
        data = {"id": 1, "name": "Test"}
        response = BLEOResponse(
            data=data,
            success_message="Data retrieved",
            error_type=None,
            error_message=None
        )
        
        response_dict = response.to_dict()
        
        # Check structure
        self.assertEqual(response_dict["data"], data)
        self.assertEqual(response_dict["successMessage"], "Data retrieved")
        self.assertIsNone(response_dict["errorType"])
        self.assertIsNone(response_dict["errorMessage"])
        
        print("  🔹 to_dict method returns correctly structured dictionary")
    
    def test_to_response_method_success(self):
        """Test BLEOResponse to_response method for success response"""
        data = {"id": 1, "name": "Test"}
        response = BLEOResponse(
            data=data,
            success_message="Data retrieved",
            error_type=None,
            error_message=None
        )
        
        drf_response = response.to_response()
        
        # Check it's a DRF Response
        self.assertIsInstance(drf_response, Response)
        
        # Check status code defaults to 200 for success
        self.assertEqual(drf_response.status_code, 200)
        
        # Check data structure
        self.assertEqual(drf_response.data["data"], data)
        self.assertEqual(drf_response.data["successMessage"], "Data retrieved")
        
        print("  🔹 to_response method creates DRF Response with 200 status code")
    
    def test_to_response_method_error(self):
        """Test BLEOResponse to_response method for error response"""
        response = BLEOResponse(
            data=None,
            success_message=None,
            error_type="ValidationError",
            error_message="Invalid data"
        )
        
        drf_response = response.to_response()
        
        # Check status code defaults to 400 for error
        self.assertEqual(drf_response.status_code, 400)
        
        # Check explicit status code
        explicit_response = response.to_response(status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(explicit_response.status_code, 422)
        
        print("  🔹 to_response method creates DRF Response with appropriate error status code")
    
    def test_success_class_method(self):
        """Test BLEOResponse.success class method"""
        data = {"id": 1, "name": "Test"}
        response = BLEOResponse.success(data=data, message="Success message")
        
        # Check fields
        self.assertEqual(response.data, data)
        self.assertEqual(response.success_message, "Success message")
        self.assertIsNone(response.error_type)
        self.assertIsNone(response.error_message)
        
        # Check default message
        default_response = BLEOResponse.success(data=data)
        self.assertEqual(default_response.success_message, "Operation successful")
        
        print("  🔹 success class method creates response with data and message")
    
    def test_error_class_method(self):
        """Test BLEOResponse.error class method"""
        response = BLEOResponse.error(
            error_type="TestError",
            error_message="Test error message"
        )
        
        # Check fields
        self.assertIsNone(response.data)
        self.assertIsNone(response.success_message)
        self.assertEqual(response.error_type, "TestError")
        self.assertEqual(response.error_message, "Test error message")
        
        print("  🔹 error class method creates response with error type and message")
    
    def test_convenience_error_methods(self):
        """Test BLEOResponse convenience error methods"""
        # not_found
        not_found = BLEOResponse.not_found("Resource not found")
        self.assertEqual(not_found.error_type, "NotFoundError")
        self.assertEqual(not_found.error_message, "Resource not found")
        
        # validation_error
        validation_error = BLEOResponse.validation_error(
            "Invalid data",
            {"field": ["Field error"]}
        )
        self.assertEqual(validation_error.error_type, "ValidationError")
        self.assertEqual(validation_error.error_message, "Invalid data")
        self.assertEqual(validation_error.validation_errors["field"][0], "Field error")
        
        # server_error
        server_error = BLEOResponse.server_error("Server crashed")
        self.assertEqual(server_error.error_type, "ServerError")
        self.assertEqual(server_error.error_message, "Server crashed")
        
        # unauthorized
        unauthorized = BLEOResponse.unauthorized("Login required")
        self.assertEqual(unauthorized.error_type, "UnauthorizedError")
        self.assertEqual(unauthorized.error_message, "Login required")
        
        print("  🔹 Convenience error methods create appropriate error responses")


# This will run if this file is executed directly
if __name__ == '__main__':
    run_test_with_output(BLEOResponseModelTest)