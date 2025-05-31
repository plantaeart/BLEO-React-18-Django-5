import os
import re
import importlib
from datetime import datetime

class ConfigManager:
    """Configuration file manager for app state tracking"""
    
    @staticmethod
    def get_app_state():
        """Get current app state from config file"""
        try:
            # Import the config module
            from config import AppCurrentState
            
            # Force reload to ensure we get the latest values
            importlib.reload(AppCurrentState)
            
            return {
                'app_version': AppCurrentState.APP_VERSION,
                'debug_level': AppCurrentState.DEBUG_LEVEL,
            }
        except (ImportError, AttributeError) as e:
            print(f"Error loading AppCurrentState: {e}")
            # Return defaults if file doesn't exist or has errors
            return {
                'app_version': "1.0.0",
                'debug_level': "DEBUG",
            }
    
    @staticmethod
    def update_app_version(new_version):
        """Update app version in config file"""
        file_path = ConfigManager._get_config_path()
        
        try:
            # Read existing file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Update APP_VERSION
            pattern = r'APP_VERSION\s*=\s*"[^"]*"'
            replacement = f'APP_VERSION = "{new_version}"'
            new_content = re.sub(pattern, replacement, content)
            
            # Write updated content
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            return True
        except Exception as e:
            print(f"Error updating app version: {e}")
            return False
    
    @staticmethod
    def update_debug_level(debug_level):
        """Update debug level in config file"""
        file_path = ConfigManager._get_config_path()
        
        try:
            # Read existing file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Update DEBUG_LEVEL
            pattern = r'DEBUG_LEVEL\s*=\s*"[^"]*"'
            replacement = f'DEBUG_LEVEL = "{debug_level}"'
            new_content = re.sub(pattern, replacement, content)
            
            # Write updated content
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            return True
        except Exception as e:
            print(f"Error updating debug level: {e}")
            return False

    @staticmethod
    def _get_config_path():
        """Get path to AppCurrentState.py file"""
        # Get project root directory
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Create config directory if it doesn't exist
        config_dir = os.path.join(root_dir, 'config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # Return full path to config file
        return os.path.join(config_dir, 'AppCurrentState.py')