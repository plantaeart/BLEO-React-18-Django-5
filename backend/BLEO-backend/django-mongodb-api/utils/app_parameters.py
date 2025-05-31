from utils.mongodb_utils import MongoDB
from models.AppParameters import AppParameters
from models.enums.DebugType import DebugType

class AppConfig:
    """Utility class for accessing application parameters"""
    
    _instance = None
    _cached_params = None
    _last_refresh = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AppConfig()
        return cls._instance
    
    def refresh(self):
        """Refresh parameters from the database"""
        db = MongoDB.get_instance().get_collection('AppParameters')
        params = db.find_one({"id": "app_parameters"})
        
        if not params:
            # Create default parameters
            default_params = AppParameters()
            db.insert_one(default_params.to_dict())
            self._cached_params = default_params.to_dict()
        else:
            self._cached_params = params
            
        import time
        self._last_refresh = time.time()
        return self._cached_params
    
    def get_parameters(self, force_refresh=False):
        """Get application parameters"""
        import time
        
        # Refresh if never loaded or forced
        if self._cached_params is None or force_refresh:
            return self.refresh()
        
        # Refresh if cache is older than 5 minutes
        if time.time() - self._last_refresh > 300:  # 5 minutes in seconds
            return self.refresh()
            
        return self._cached_params
    
    def is_debug_enabled(self):
        """Check if debug mode is enabled"""
        params = self.get_parameters()
        return params.get('debug_level') == DebugType.DEBUG.value
    
    def get_app_version(self):
        """Get the current app version"""
        params = self.get_parameters()
        return params.get('app_version', '1.0.0')