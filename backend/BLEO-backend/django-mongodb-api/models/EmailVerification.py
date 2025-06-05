# Create models/EmailVerification.py
from datetime import datetime
from typing import Optional, Dict, Any
from datetime import timezone
import re

class EmailVerification:
    """EmailVerification schema for email verification tokens"""
    
    def __init__(self, 
                 bleoid: str,
                 email: str, 
                 token: str,
                 created_at: Optional[datetime] = None,
                 expires_at: Optional[datetime] = None,
                 verified: bool = False,
                 attempts: int = 0,
                 verified_at: Optional[datetime] = None):
        """
        Initialize EmailVerification
        
        Args:
            bleoid (str): User's BLEO ID
            email (str): User's email address
            token (str): JWT verification token
            created_at (datetime, optional): When token was created
            expires_at (datetime, optional): When token expires
            verified (bool): Whether email has been verified
            attempts (int): Number of verification attempts
            verified_at (datetime, optional): When verification was completed
        """
        # Add BLEOID validation and normalization
        self.bleoid = self._validate_and_normalize_bleoid(bleoid)
        self.email = email
        self.token = token
        self.created_at = created_at or datetime.now(timezone.utc)
        self.expires_at = expires_at
        self.verified = verified
        self.attempts = attempts
        self.verified_at = verified_at
    
    @staticmethod
    def _validate_and_normalize_bleoid(bleoid: str) -> str:
        """Validate and normalize BLEOID format"""
        if not bleoid:
            raise ValueError("bleoid cannot be null or empty")
        
        # Normalize to uppercase and strip whitespace
        normalized_bleoid = bleoid.strip().upper()
        
        # Validate format matches pattern ^[A-Z0-9]{6}$
        if not re.match(r'^[A-Z0-9]{6}$', normalized_bleoid):
            raise ValueError("bleoid must be exactly 6 uppercase letters/numbers")
        
        return normalized_bleoid
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert EmailVerification to dictionary for MongoDB storage"""
        return {
            'bleoid': self.bleoid,
            'email': self.email,
            'token': self.token,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'verified': self.verified,
            'attempts': self.attempts,
            'verified_at': self.verified_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailVerification':
        """Create EmailVerification from dictionary with validation"""
        bleoid = data.get('bleoid')
        email = data.get('email')
        token = data.get('token')
        
        # Validate required fields
        if not bleoid:
            raise ValueError("bleoid is required")
        if not email:
            raise ValueError("email is required")
        if not token:
            raise ValueError("token is required")
            
        return cls(
            bleoid=bleoid,
            email=email,
            token=token,
            created_at=data.get('created_at'),
            expires_at=data.get('expires_at'),
            verified=data.get('verified', False),
            attempts=data.get('attempts', 0),
            verified_at=data.get('verified_at')
        )
    
    def is_expired(self) -> bool:
        """Check if verification token is expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_verified(self) -> bool:
        """Check if email is already verified"""
        return self.verified
    
    def increment_attempts(self) -> None:
        """Increment verification attempts counter"""
        self.attempts += 1
    
    def mark_as_verified(self) -> None:
        """Mark email as verified"""
        self.verified = True
        self.verified_at = datetime.now(timezone.utc)
    
    def __str__(self) -> str:
        """String representation of EmailVerification"""
        return f"EmailVerification(email={self.email}, verified={self.verified}, expires_at={self.expires_at})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"EmailVerification(bleoid='{self.bleoid}', email='{self.email}', "
                f"verified={self.verified}, attempts={self.attempts}, "
                f"created_at={self.created_at}, expires_at={self.expires_at})")