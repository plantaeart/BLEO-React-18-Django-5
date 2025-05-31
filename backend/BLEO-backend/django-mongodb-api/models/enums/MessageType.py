from enum import Enum

class MessageType(str, Enum):
    JOKING = "Joking"
    THOUGHTS = "Thoughts"
    LOVE_MESSAGE = "Love_message"
    SOUVENIR = "Souvenir"
    NOTES = "Notes"
