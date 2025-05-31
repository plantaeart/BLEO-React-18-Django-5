from enum import Enum

class EnergyLevelType(str, Enum):
    HIGH = "High"
    LOW = "Low"

    @property
    def is_high(self) -> bool:
        return self == EnergyLevelType.HIGH.value

    @property
    def is_low(self) -> bool:
        return self == EnergyLevelType.LOW.value