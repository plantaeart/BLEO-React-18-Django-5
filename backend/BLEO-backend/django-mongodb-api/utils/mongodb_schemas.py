# MongoDB schema validators

USER_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["BLEOId", "email", "password", "userName", "created_at"],
        "properties": {
            "BLEOId": {
                "bsonType": "string",
                "description": "Unique BLEO identifier with format #XXXXXX"
            },
            "email": {
                "bsonType": "string",
                "description": "User email"
            },
            "password": {
                "bsonType": "string",
                "description": "Hashed password"
            },
            "userName": {
                "bsonType": "string",
                "description": "User's display name (defaults to 'NewUser')"
            },
            "profilePic": {
                "bsonType": ["binData", "null"],
                "description": "Profile picture binary data (optional)"
            },
            "email_verified": {
                "bsonType": "bool",
                "description": "Whether the user's email has been verified"
            },
            "last_login": {
                "bsonType": ["date", "null"],
                "description": "Last login timestamp"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Account creation timestamp"
            },
            "bio": {
                "bsonType": ["string", "null"],
                "description": "User biography or profile description"
            },
            "preferences": {
                "bsonType": ["object", "null"],
                "description": "User preferences and settings"
            }
        }
    }
}

LINK_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["BLEOIdPartner1", "status", "created_at", "updated_at"],
        "properties": {
            "BLEOIdPartner1": {
                "bsonType": "string",
                "description": "BLEO ID of first partner"
            },
            "BLEOIdPartner2": {
                "bsonType": ["string", "null"],
                "description": "BLEO ID of second partner (optional)"
            },
            "status": {
                "enum": ["pending", "accepted", "rejected", "blocked"],
                "description": "Current status of the connection"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Link creation date"
            },
            "updated_at": {
                "bsonType": "date",
                "description": "Link last update date"
            }
        }
    }
}

MESSAGE_INFOS_SCHEMA = {
    "bsonType": "object",
    "required": ["id", "title", "text", "type"],
    "properties": {
        "id": {
            "bsonType": "int",
            "description": "Unique integer ID for the message"
        },
        "title": {
            "bsonType": "string",
            "description": "Message title"
        },
        "text": {
            "bsonType": "string",
            "description": "Message content"
        },
        "type": {
            "enum": ["Joking", "Thoughts", "Love_message", "Souvenir"],
            "description": "Type of message"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Message creation timestamp"
        }
    }
}

MESSAGE_DAY_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["BLEOId", "date"],
        "properties": {
            "BLEOId": {
                "bsonType": "string",
                "description": "User BLEO identifier"
            },
            "date": {
                "bsonType": "date",
                "description": "Date of the message collection"
            },
            "messages": {
                "bsonType": "array",
                "items": MESSAGE_INFOS_SCHEMA
            },
            "mood": {
                "bsonType": ["string", "null"],
                "description": "Mood for the day"
            },
            "energy_level": {
                "bsonType": ["string", "null"],
                "description": "Energy level for the day (high/low)"
            },
            "pleasantness": {
                "bsonType": ["string", "null"],
                "description": "Pleasantness level for the day (pleasant/unpleasant)"
            }
        }
    }
}

# New schemas for authentication features

PASSWORD_RESET_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["email", "token", "expires"],
        "properties": {
            "email": {
                "bsonType": "string",
                "description": "User email for password reset"
            },
            "token": {
                "bsonType": "string",
                "description": "Unique token for password reset verification"
            },
            "expires": {
                "bsonType": "date",
                "description": "Token expiration timestamp"
            }
        }
    }
}

TOKEN_BLACKLIST_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["token", "created_at", "expires_at"],
        "properties": {
            "token": {
                "bsonType": "string",
                "description": "JWT refresh token that has been invalidated"
            },
            "created_at": {
                "bsonType": "date",
                "description": "When the token was added to blacklist"
            },
            "expires_at": {
                "bsonType": "date",
                "description": "When the token will expire (for cleanup)"
            }
        }
    }
}