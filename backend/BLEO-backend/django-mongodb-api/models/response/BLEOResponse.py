from typing import Any, Dict, Optional, TypeVar, Generic
from rest_framework.response import Response
from rest_framework import status

T = TypeVar('T')

class BLEOResponse(Generic[T]):
    """
    Standardized API response class for consistent formatting across all endpoints.
    
    Attributes:
        data (Any): The response data payload (null if there's an error)
        success_message (str): A message describing success (null if there's an error)
        error_type (str): Type of error encountered (null if successful)
        error_message (str): Detailed error message (null if successful)
    """
    
    def __init__(
        self, 
        data: Optional[T] = None,
        success_message: Optional[str] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.data = data
        self.success_message = success_message
        self.error_type = error_type
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for JSON serialization."""
        return {
            "data": self.data,
            "successMessage": self.success_message,
            "errorType": self.error_type,
            "errorMessage": self.error_message
        }
    
    def to_response(self, status_code: int = None) -> Response:
        """Convert to DRF Response with appropriate status code."""
        # Determine status code if not explicitly provided
        if status_code is None:
            if self.error_type:
                # Default error status
                status_code = status.HTTP_400_BAD_REQUEST
            else:
                # Default success status
                status_code = status.HTTP_200_OK
        
        return Response(self.to_dict(), status=status_code)
    
    @classmethod
    def success(cls, data: T = None, message: str = "Operation successful") -> 'BLEOResponse[T]':
        """Create a success response."""
        return cls(
            data=data,
            success_message=message,
            error_type=None,
            error_message=None
        )
    
    @classmethod
    def error(cls, error_type: str, error_message: str) -> 'BLEOResponse[None]':
        """Create an error response."""
        return cls(
            data=None,
            success_message=None,
            error_type=error_type,
            error_message=error_message
        )
    
    # Convenience methods for common errors
    @classmethod
    def not_found(cls, message: str = "Resource not found") -> 'BLEOResponse[None]':
        """Create a not found error response."""
        return cls.error("NotFoundError", message)
    
    @classmethod
    def validation_error(cls, message: str, errors=None) -> 'BLEOResponse[None]':
        """Create a validation error response."""
        response = cls()
        response.error_type = "ValidationError"
        response.error_message = message
        
        # Add validation errors if provided
        if errors:
            response.data = {"validation_errors": errors}
            
        return response
    
    @classmethod
    def server_error(cls, message: str = "Internal server error") -> 'BLEOResponse[None]':
        """Create a server error response."""
        return cls.error("ServerError", message)
        
    @classmethod
    def unauthorized(cls, message: str = "Unauthorized access") -> 'BLEOResponse[None]':
        """Create an unauthorized error response."""
        return cls.error("UnauthorizedError", message)