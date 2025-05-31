from enum import Enum
from .MoodQuadrantType import MoodQuadrantType

class MoodType(str, Enum):
    # Red Quadrant (High energy, unpleasant)
    ANGRY = "Angry"
    ANXIOUS = "Anxious"
    FRUSTRATED = "Frustrated"
    MIXED = "Mixed"

    # Yellow Quadrant (High energy, pleasant)
    EXCITED = "Excited"
    JOYFUL = "Joyful"
    HAPPY = "Happy"
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
    def quadrant(self) -> MoodQuadrantType:
        red_moods = [self.ANGRY, self.ANXIOUS, self.FRUSTRATED, self.MIXED]
        yellow_moods = [self.EXCITED, self.JOYFUL, self.ENTHUSIASTIC, self.JOKING, self.HAPPY]
        blue_moods = [self.SAD, self.DISAPPOINTED, self.TIRED]
        
        if self in red_moods:
            return MoodQuadrantType.RED
        elif self in yellow_moods:
            return MoodQuadrantType.YELLOW
        elif self in blue_moods:
            return MoodQuadrantType.BLUE
        else:
            return MoodQuadrantType.GREEN