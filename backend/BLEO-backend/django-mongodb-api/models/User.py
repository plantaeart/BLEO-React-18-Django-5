from bson.binary import Binary
from typing import Dict, Any, Optional
from datetime import datetime

class User:
    """User schema"""
    def __init__(
        self,
        BLEOId: int,
        mail: str,
        password: str,
        userName: str = "NewUser",
        profilePic: Optional[Binary] = None,
        email_verified: bool = False,
        last_login: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        bio: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ):
        self.BLEOId = BLEOId
        self.mail = mail
        self.password = password
        self.userName = userName
        self.profilePic = profilePic
        self.email_verified = email_verified
        self.last_login = last_login or datetime.now()
        self.created_at = created_at or datetime.now()
        self.bio = bio
        self.preferences = preferences or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "BLEOId": self.BLEOId,
            "mail": self.mail,
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
        return cls(
            BLEOId=data.get("BLEOId"),
            mail=data.get("mail"),
            password=data.get("password"),
            userName=data.get("userName", "NewUser"),
            profilePic=data.get("profilePic"),
            email_verified=data.get("email_verified", False),
            last_login=data.get("last_login"),
            created_at=data.get("created_at"),
            bio=data.get("bio"),
            preferences=data.get("preferences")
        )