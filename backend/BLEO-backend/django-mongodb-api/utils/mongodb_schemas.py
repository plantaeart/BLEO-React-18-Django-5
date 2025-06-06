# MongoDB schema validators

from utils.validation_patterns import ValidationPatterns, ValidationRules

USER_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["bleoid", "email", "password", "userName", "created_at"],
        "properties": {
            "bleoid": {
                "bsonType": "string",
                "pattern": ValidationPatterns.BLEOID_PATTERN,
                "description": ValidationPatterns.BLEOID_DESCRIPTION
            },
            "email": {
                "bsonType": "string",
                "pattern": ValidationPatterns.EMAIL_BASIC_PATTERN,
                "maxLength": ValidationRules.MAX_LENGTHS['email'],
                "description": "User's email address"
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
            "email_verified_at": {
                "bsonType": ["date", "null"],
                "description": "When the email was verified"
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
        "required": ["bleoidPartner1", "bleoidPartner2", "status", "created_at", "updated_at"],
        "properties": {
            "bleoidPartner1": {
                "bsonType": "string",
                "pattern": "^[A-Z0-9]{6}$",
                "description": "BLEO ID of first partner"
            },
            "bleoidPartner2": {
                "bsonType": "string",
                "pattern": "^[A-Z0-9]{6}$",
                "description": "BLEO ID of second partner"
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
        "required": ["from_bleoid", "to_bleoid", "date"],
        "properties": {
            "from_bleoid": {
                "bsonType": "string",
                "pattern": "^[A-Z0-9]{6}$",
                "description": "User BLEO identifier (sender)"
            },
            "to_bleoid": {
                "bsonType": "string", 
                "pattern": "^[A-Z0-9]{6}$",
                "description": "Partner BLEO identifier (recipient)"
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
                "enum": ["High", "Low", None],
                "description": "Energy level for the day (High/Low)"
            },
            "pleasantness": {
                "bsonType": ["string", "null"],
                "enum": ["pleasant", "unpleasant", None],
                "description": "Pleasantness level for the day (pleasant/unpleasant)"
            }
        }
    }
}

PASSWORD_RESET_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["bleoid", "email", "token", "created_at", "expires_at", "used", "attempts"],
        "properties": {
            "bleoid": {
                "bsonType": "string",
                "pattern": ValidationPatterns.BLEOID_PATTERN,
                "description": ValidationPatterns.BLEOID_DESCRIPTION
            },
            "email": {
                "bsonType": "string",
                "pattern": ValidationPatterns.EMAIL_BASIC_PATTERN,
                "maxLength": ValidationRules.MAX_LENGTHS['email'],
                "description": "User's email address for password reset"
            },
            "token": {
                "bsonType": "string",
                "description": "JWT reset token"
            },
            "created_at": {
                "bsonType": "date",
                "description": "When the reset token was created"
            },
            "expires_at": {
                "bsonType": "date",
                "description": "When the reset token expires"
            },
            "used": {
                "bsonType": "bool",
                "description": "Whether the reset token has been used"
            },
            "attempts": {
                "bsonType": "int",
                "description": "Number of reset attempts",
                "minimum": 0
            },
            "used_at": {
                "bsonType": ["date", "null"],
                "description": "When the reset token was used (if applicable)"
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

DEBUG_LOGS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["id", "date", "message", "type", "code", "user_type"],
        "properties": {
            "id": {
                "bsonType": "int",
                "description": "Auto-incremented unique log entry identifier"
            },
            "date": {
                "bsonType": "date",
                "description": "Log date and time"
            },
            "bleoid": {
                "bsonType": ["string", "null"],
                "description": "User BLEO identifier (if applicable)"
            },
            "user_type": {
                "enum": ["user", "system"],
                "description": "Type of user (user or system)"
            },
            "message": {
                "bsonType": "string",
                "description": "Log message content"
            },
            "type": {
                "bsonType": "string",
                "description": "Log type category"
            },
            "code": {
                "bsonType": "int",
                "description": "Error or success code"
            },
            "error_source": {
                "bsonType": ["string", "null"],
                "enum": ["server", "application", None],
                "description": "Source of the error (server or application)"
            }
        }
    }
}

APP_PARAMETERS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["id", "param_name", "param_value"],
        "properties": {
            "id": {
                "bsonType": "int",
                "description": "Unique integer identifier for the parameter"
            },
            "param_name": {
                "bsonType": "string", 
                "description": "Parameter name/key"
            },
            "param_value": {
                "description": "Parameter value (can be any type)"
            }
        }
    }
}

EMAIL_VERIFICATION_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["bleoid", "email", "token", "created_at", "expires_at", "verified"],
        "properties": {
            "bleoid": {
                "bsonType": "string",
                "pattern": "^[A-Z0-9]{6}$",
                "description": "User's BLEO ID"
            },
            "email": {
                "bsonType": "string",
                "pattern": "^[^@]+@[^@]+\\.[^@]+$",
                "maxLength": 254,
                "description": "User's email address for verification"
            },
            "token": {
                "bsonType": "string",
                "description": "JWT verification token"
            },
            "created_at": {
                "bsonType": "date",
                "description": "When the verification token was created"
            },
            "expires_at": {
                "bsonType": "date",
                "description": "When the verification token expires"
            },
            "verified": {
                "bsonType": "bool",
                "description": "Whether the email has been verified"
            },
            "attempts": {
                "bsonType": "int",
                "description": "Number of verification attempts",
                "minimum": 0
            },
            "verified_at": {
                "bsonType": ["date", "null"],
                "description": "When the email verification was completed"
            }
        }
    }
}