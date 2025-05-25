from enum import Enum, auto

class EnergyLevel(str, Enum):
    HIGH = "high"
    LOW = "low"

class Pleasantness(str, Enum):
    PLEASANT = "pleasant"
    UNPLEASANT = "unpleasant"

class MoodQuadrant(str, Enum):
    RED = "red"      # High energy, unpleasant
    YELLOW = "yellow"  # High energy, pleasant
    BLUE = "blue"    # Low energy, unpleasant
    GREEN = "green"  # Low energy, pleasant
    
    @classmethod
    def from_dimensions(cls, energy: EnergyLevel, pleasantness: Pleasantness):
        if energy == EnergyLevel.HIGH and pleasantness == Pleasantness.UNPLEASANT:
            return cls.RED
        elif energy == EnergyLevel.HIGH and pleasantness == Pleasantness.PLEASANT:
            return cls.YELLOW
        elif energy == EnergyLevel.LOW and pleasantness == Pleasantness.UNPLEASANT:
            return cls.BLUE
        else:  # Low energy, pleasant
            return cls.GREEN