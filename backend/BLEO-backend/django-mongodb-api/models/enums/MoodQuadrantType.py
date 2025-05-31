from enum import Enum, auto
from .PleasantnessType import PleasantnessType
from .EnergyLevelType import EnergyLevelType

class MoodQuadrantType(str, Enum):
    RED = "red"      # High energy, unpleasant
    YELLOW = "yellow"  # High energy, pleasant
    BLUE = "blue"    # Low energy, unpleasant
    GREEN = "green"  # Low energy, pleasant
    
    @classmethod
    def from_dimensions(cls, energy: EnergyLevelType, pleasantness: PleasantnessType):
        if energy == EnergyLevelType.HIGH.value and pleasantness == PleasantnessType.UNPLEASANT:
            return cls.RED
        elif energy == EnergyLevelType.HIGH.value and pleasantness == PleasantnessType.PLEASANT.value:
            return cls.YELLOW
        elif energy == EnergyLevelType.LOW.value and pleasantness == PleasantnessType.UNPLEASANT:
            return cls.BLUE
        else:  # Low energy, pleasant
            return cls.GREEN