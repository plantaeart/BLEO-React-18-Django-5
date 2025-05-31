from enum import Enum, auto

class PleasantnessType(str, Enum):
    PLEASANT = "pleasant"
    UNPLEASANT = "unpleasant"

    @property
    def is_pleasant(self) -> bool:
        return self == PleasantnessType.PLEASANT.value

    @property
    def is_unpleasant(self) -> bool:
        return self == PleasantnessType.UNPLEASANT