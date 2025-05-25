from bson.binary import Binary
from typing import Dict, Any, Optional

class User:
    """User schema"""
    def __init__(
        self,
        BLEOId: int,
        mail: str,
        password: str,
        userName: str = "NewUser",
        profilePic: Optional[Binary] = None
    ):
        self.BLEOId = BLEOId
        self.mail = mail
        self.password = password
        self.userName = userName
        self.profilePic = profilePic
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "BLEOId": self.BLEOId,
            "mail": self.mail,
            "password": self.password,
            "userName": self.userName,
            "profilePic": self.profilePic
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(
            BLEOId=data.get("BLEOId"),
            mail=data.get("mail"),
            password=data.get("password"),
            userName=data.get("userName", "NewUser"),
            profilePic=data.get("profilePic")
        )