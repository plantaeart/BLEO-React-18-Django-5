import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from utils.jwt_utils import JWTSecretGenerator
from utils.logger import Logger
from models.enums.LogType import LogType

class JWTSecretRotationManager:
    """Manages automatic JWT secret rotation"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / '.env'
        self.rotation_data_file = self.project_root / '.jwt_rotation.json'
        self.rotation_days = int(os.getenv('JWT_SECRET_ROTATION_DAYS', 30))
    
    def get_rotation_data(self):
        """Get current rotation metadata"""
        try:
            if self.rotation_data_file.exists():
                with open(self.rotation_data_file, 'r') as f:
                    return json.load(f)
            else:
                # Create initial rotation data
                initial_data = {
                    'last_rotation': datetime.now().isoformat(),
                    'next_rotation': (datetime.now() + timedelta(days=self.rotation_days)).isoformat(),
                    'rotation_count': 0,
                    'rotation_days': self.rotation_days
                }
                self.save_rotation_data(initial_data)
                return initial_data
        except Exception as e:
            Logger.log_error(
                "JWT_ROTATION",
                f"Failed to read rotation data: {str(e)}",
                LogType.ERROR.value
            )
            return None
    
    def save_rotation_data(self, data):
        """Save rotation metadata"""
        try:
            with open(self.rotation_data_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            Logger.log_error(
                "JWT_ROTATION",
                f"Failed to save rotation data: {str(e)}",
                LogType.ERROR.value
            )
            return False
    
    def needs_rotation(self):
        """Check if JWT secret needs rotation"""
        rotation_data = self.get_rotation_data()
        if not rotation_data:
            return True
        
        try:
            next_rotation = datetime.fromisoformat(rotation_data['next_rotation'])
            return datetime.now() >= next_rotation
        except Exception:
            return True
    
    def rotate_secret(self, force=False):
        """
        Rotate JWT secret
        
        Args:
            force (bool): Force rotation even if not due
            
        Returns:
            dict: Rotation result
        """
        try:
            if not force and not self.needs_rotation():
                rotation_data = self.get_rotation_data()
                next_rotation = datetime.fromisoformat(rotation_data['next_rotation'])
                days_left = (next_rotation - datetime.now()).days
                
                return {
                    'success': True,
                    'rotated': False,
                    'message': f'Rotation not needed. Next rotation in {days_left} days',
                    'next_rotation': rotation_data['next_rotation']
                }
            
            # Generate new JWT secret
            new_secret = JWTSecretGenerator.generate_secure_secret()
            
            # Update .env file
            save_result = JWTSecretGenerator.save_secret_to_env(new_secret)
            
            if not save_result['success']:
                return {
                    'success': False,
                    'message': f'Failed to save new secret: {save_result["message"]}'
                }
            
            # Update rotation data
            rotation_data = self.get_rotation_data() or {}
            rotation_data.update({
                'last_rotation': datetime.now().isoformat(),
                'next_rotation': (datetime.now() + timedelta(days=self.rotation_days)).isoformat(),
                'rotation_count': rotation_data.get('rotation_count', 0) + 1,
                'rotation_days': self.rotation_days,
                'previous_secret_rotated_at': datetime.now().isoformat()
            })
            
            if not self.save_rotation_data(rotation_data):
                Logger.log_error(
                    "JWT_ROTATION",
                    "Secret rotated but failed to save rotation metadata",
                    LogType.WARNING.value
                )
            
            # Log the rotation
            Logger.log_system_event(
                f"JWT secret rotated successfully. Rotation #{rotation_data['rotation_count']}",
                LogType.INFO.value
            )
            
            return {
                'success': True,
                'rotated': True,
                'message': 'JWT secret rotated successfully',
                'rotation_count': rotation_data['rotation_count'],
                'next_rotation': rotation_data['next_rotation'],
                'secret_strength': JWTSecretGenerator.validate_secret_strength(new_secret)
            }
            
        except Exception as e:
            error_msg = f"JWT secret rotation failed: {str(e)}"
            Logger.log_error(
                "JWT_ROTATION",
                error_msg,
                LogType.ERROR.value
            )
            return {
                'success': False,
                'message': error_msg,
                'error': str(e)
            }
    
    def get_rotation_status(self):
        """Get current rotation status"""
        rotation_data = self.get_rotation_data()
        if not rotation_data:
            return {
                'status': 'unknown',
                'message': 'No rotation data available'
            }
        
        try:
            last_rotation = datetime.fromisoformat(rotation_data['last_rotation'])
            next_rotation = datetime.fromisoformat(rotation_data['next_rotation'])
            now = datetime.now()
            
            days_since = (now - last_rotation).days
            days_until = (next_rotation - now).days
            
            if days_until <= 0:
                status = 'overdue'
                message = f'Rotation is {abs(days_until)} days overdue'
            elif days_until <= 7:
                status = 'due_soon'
                message = f'Rotation due in {days_until} days'
            else:
                status = 'current'
                message = f'Next rotation in {days_until} days'
            
            return {
                'status': status,
                'message': message,
                'last_rotation': rotation_data['last_rotation'],
                'next_rotation': rotation_data['next_rotation'],
                'days_since_last': days_since,
                'days_until_next': days_until,
                'rotation_count': rotation_data.get('rotation_count', 0),
                'rotation_days': rotation_data.get('rotation_days', self.rotation_days)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error reading rotation status: {str(e)}'
            }
    
    def schedule_rotation_check(self):
        """Check and perform rotation if needed (for scheduled tasks)"""
        try:
            if self.needs_rotation():
                result = self.rotate_secret()
                if result['success'] and result['rotated']:
                    Logger.log_system_event(
                        f"Automatic JWT secret rotation completed. Next rotation: {result['next_rotation']}",
                        LogType.INFO.value
                    )
                return result
            else:
                return {
                    'success': True,
                    'rotated': False,
                    'message': 'No rotation needed at this time'
                }
        except Exception as e:
            error_msg = f"Scheduled rotation check failed: {str(e)}"
            Logger.log_error(
                "JWT_ROTATION",
                error_msg,
                LogType.ERROR.value
            )
            return {
                'success': False,
                'message': error_msg
            }

# Convenience functions
def check_jwt_rotation():
    """Check if JWT secret needs rotation (convenience function)"""
    manager = JWTSecretRotationManager()
    return manager.needs_rotation()

def rotate_jwt_secret(force=False):
    """Rotate JWT secret (convenience function)"""
    manager = JWTSecretRotationManager()
    return manager.rotate_secret(force=force)

def get_jwt_rotation_status():
    """Get JWT rotation status (convenience function)"""
    manager = JWTSecretRotationManager()
    return manager.get_rotation_status()