from enum import Enum
from .EnergyPleasantnessType import MoodQuadrant

class MoodType(str, Enum):
    # Red Quadrant (High energy, unpleasant)
    ANGRY = "Angry"
    ANXIOUS = "Anxious"
    FRUSTRATED = "Frustrated"
    
    # Yellow Quadrant (High energy, pleasant)
    EXCITED = "Excited"
    JOYFUL = "Joyful"
    ENTHUSIASTIC = "Enthusiastic"
    JOKING = "Joking"
    
    # Blue Quadrant (Low energy, unpleasant)
    SAD = "Sad"
    DISAPPOINTED = "Disappointed" 
    TIRED = "Tired"
    
    # Green Quadrant (Low energy, pleasant)
    CALM = "Calm"
    RELAXED = "Relaxed"
    CONTENT = "Content"
    LOVE_MESSAGE = "Love message"
    SOUVENIR = "Souvenir"
    THOUGHTS = "Thoughts"
    
    @property
    def quadrant(self) -> MoodQuadrant:
        red_moods = [self.ANGRY, self.ANXIOUS, self.FRUSTRATED]
        yellow_moods = [self.EXCITED, self.JOYFUL, self.ENTHUSIASTIC, self.JOKING]
        blue_moods = [self.SAD, self.DISAPPOINTED, self.TIRED]
        
        if self in red_moods:
            return MoodQuadrant.RED
        elif self in yellow_moods:
            return MoodQuadrant.YELLOW
        elif self in blue_moods:
            return MoodQuadrant.BLUE
        else:
            return MoodQuadrant.GREEN