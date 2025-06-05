from bson.binary import Binary
from typing import Dict, Any, Optional
from datetime import datetime
import random
import string
import re

class User:
    """User schema"""
    def __init__(
        self,
        bleoid: str,
        email: str,
        password: str,
        userName: str = "NewUser",
        profilePic: Optional[Binary] = None,
        email_verified: bool = False,
        last_login: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        bio: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ):
        # Add BLEOID validation
        self._validate_bleoid(bleoid)
        
        self.bleoid = bleoid
        self.email = email
        self.password = password
        self.userName = userName
        self.profilePic = profilePic
        self.email_verified = email_verified
        self.last_login = last_login or datetime.now()
        self.created_at = created_at or datetime.now()
        self.bio = bio
        self.preferences = preferences or {}
    
    @staticmethod
    def _validate_bleoid(bleoid: str):
        """Validate BLEOID format matches schema pattern ^[A-Z0-9]{6}$"""
        if not bleoid:
            raise ValueError("bleoid cannot be null or empty")
        
        if not re.match(r'^[A-Z0-9]{6}$', bleoid):
            raise ValueError("bleoid must be exactly 6 uppercase letters/numbers")
    
    @staticmethod
    def generate_bleoid() -> str:
        """Generate a random bleoid with format XXXXXX that matches schema"""
        chars = string.ascii_uppercase + string.digits
        bleoid = ''.join(random.choice(chars) for _ in range(6))
        # Ensure it matches the pattern (it should, but double-check)
        User._validate_bleoid(bleoid)
        return bleoid
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bleoid": self.bleoid,
            "email": self.email,
            "password": self.password,
            "userName": self.userName,
            "profilePic": self.profilePic,
            "email_verified": self.email_verified,
            "last_login": self.last_login,
            "created_at": self.created_at,
            "bio": self.bio,
            "preferences": self.preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary with validation"""
        bleoid = data.get("bleoid")
        email = data.get("email")
        password = data.get("password")
        
        if not bleoid:
            raise ValueError("bleoid is required")
        if not email:
            raise ValueError("email is required")
        if not password:
            raise ValueError("password is required")
            
        return cls(
            bleoid=bleoid,
            email=email,
            password=password,
            userName=data.get("userName", "NewUser"),
            profilePic=data.get("profilePic"),
            email_verified=data.get("email_verified", False),
            last_login=data.get("last_login"),
            created_at=data.get("created_at"),
            bio=data.get("bio"),
            preferences=data.get("preferences")
        )