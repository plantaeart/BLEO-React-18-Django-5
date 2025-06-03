from utils.jwt_rotation import JWTSecretRotationManager
from utils.logger import Logger
from models.enums.LogType import LogType
import threading
import time

class JWTRotationMiddleware:
    """Middleware to check JWT rotation status periodically"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_check = 0
        self.check_interval = 3600  # Check every hour
        self.rotation_manager = JWTSecretRotationManager()
    
    def __call__(self, request):
        # Perform periodic rotation check (non-blocking)
        current_time = time.time()
        if current_time - self.last_check > self.check_interval:
            self.last_check = current_time
            threading.Thread(target=self._check_rotation, daemon=True).start()
        
        return self.get_response(request)
    
    def _check_rotation(self):
        """Background rotation check"""
        try:
            if self.rotation_manager.needs_rotation():
                Logger.log_system_event(
                    "JWT secret rotation is due - consider running rotation command",
                    LogType.WARNING.value
                )
        except Exception as e:
            Logger.log_error(
                "JWT_ROTATION_MIDDLEWARE",
                f"Rotation check failed: {str(e)}",
                LogType.ERROR.value
            )