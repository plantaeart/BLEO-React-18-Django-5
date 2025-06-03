from celery import shared_task
from utils.jwt_rotation import JWTSecretRotationManager
from utils.logger import Logger
from models.enums.LogType import LogType

@shared_task
def check_jwt_rotation():
    """Celery task to check and perform JWT rotation"""
    try:
        manager = JWTSecretRotationManager()
        result = manager.schedule_rotation_check()
        
        if result['success'] and result['rotated']:
            Logger.log_system_event(
                f"Automated JWT secret rotation completed via Celery task",
                LogType.INFO.value
            )
        
        return result
    except Exception as e:
        error_msg = f"Celery JWT rotation task failed: {str(e)}"
        Logger.log_error(
            "JWT_ROTATION_TASK",
            error_msg,
            LogType.ERROR.value
        )
        return {
            'success': False,
            'message': error_msg
        }