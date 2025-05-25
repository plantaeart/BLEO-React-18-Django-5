# MongoDB schema validators

# In USER_SCHEMA, add userName to properties
USER_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["BLEOId", "mail", "password"],
        "properties": {
            "BLEOId": {
                "bsonType": "int",
                "description": "Auto-generated unique BLEO identifier (integer)"
            },
            "mail": {
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
            }
        }
    }
}

LINK_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["BLEOIdPartner1"],
        "properties": {
            "BLEOIdPartner1": {
                "bsonType": "int",
                "description": "BLEO ID of first partner"
            },
            "BLEOIdPartner2": {
                "bsonType": ["int", "null"], 
                "description": "BLEO ID of second partner (optional)"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Link creation date"
            }
        }
    }
}

MESSAGE_INFOS_SCHEMA = {
    "bsonType": "object",
    "required": ["title", "text", "type"],
    "properties": {
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
                "bsonType": "int",
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
                "bsonType": "string",
                "description": "Mood for the day"
            }
        }
    }
}