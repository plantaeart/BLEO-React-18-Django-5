from datetime import datetime, timezone
from bson import Binary
import base64

class PasswordResets:
    """Model for password reset tokens"""
    
    def __init__(self, bleoid=None, email=None, token=None, created_at=None, expires_at=None, used=False, attempts=0, used_at=None):
        """
        Initialize PasswordResets model
        
        Args:
            bleoid (str): User's BLEO identifier
            email (str): User's email address
            token (str): JWT reset token
            created_at (datetime): When the reset token was created
            expires_at (datetime): When the reset token expires
            used (bool): Whether the token has been used
            attempts (int): Number of reset attempts
            used_at (datetime): When the token was used
        """
        self.bleoid = bleoid
        self.email = email
        self.token = token
        self.created_at = created_at or datetime.now(timezone.utc)
        self.expires_at = expires_at
        self.used = used
        self.attempts = attempts
        self.used_at = used_at
    
    def to_dict(self):
        """Convert PasswordResets to dictionary for MongoDB storage"""
        data = {
            'bleoid': self.bleoid,
            'email': self.email,
            'token': self.token,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'used': self.used,
            'attempts': self.attempts
        }
        
        # Only include used_at if it exists
        if self.used_at:
            data['used_at'] = self.used_at
            
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create PasswordResets instance from dictionary"""
        return cls(
            bleoid=data.get('bleoid'),
            email=data.get('email'),
            token=data.get('token'),
            created_at=data.get('created_at'),
            expires_at=data.get('expires_at'),
            used=data.get('used', False),
            attempts=data.get('attempts', 0),
            used_at=data.get('used_at')
        )
    
    def is_expired(self):
        """Check if the reset token has expired"""
        if not self.expires_at:
            return True
        
        # Ensure timezone awareness
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        return expires_at < now
    
    def is_valid(self):
        """Check if the reset token is valid (not used and not expired)"""
        return not self.used and not self.is_expired()
    
    def mark_as_used(self):
        """Mark the reset token as used"""
        self.used = True
        self.used_at = datetime.now(timezone.utc)
    
    def increment_attempts(self):
        """Increment the number of reset attempts"""
        self.attempts += 1
    
    def __str__(self):
        """String representation of PasswordResets"""
        status = "used" if self.used else ("expired" if self.is_expired() else "valid")
        return f"PasswordReset(bleoid={self.bleoid}, email={self.email}, status={status})"
    
    def __repr__(self):
        """Detailed representation of PasswordResets"""
        return f"PasswordResets(bleoid='{self.bleoid}', email='{self.email}', token='{self.token[:20]}...', created_at='{self.created_at}', expires_at='{self.expires_at}', used={self.used}, attempts={self.attempts})"