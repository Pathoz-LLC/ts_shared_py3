from __future__ import annotations
from enum import IntEnum, unique
import random

# import google.cloud.ndb


@unique
class Sex(IntEnum):
    """sex of user prospect or inner circle member"""

    NEVERSET = 0
    UNKNOWN = 1
    FEMALE = 2
    MALE = 3

    def __eq__(self, other) -> bool:
        """handle both int and object cases

        should not be necessary since equality is built into Enum class
            but some tests are sending values that fail equality tests
            so enabled this code to handle more flexibility
            TODO:  disable this method and then fix any failing tests
        """
        if isinstance(other, Sex):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    @property
    def toDisplayVal(self) -> str:
        if self == 0:
            return "Won't say"
        elif self == 1:
            return "Won't say"
        elif self == 2:
            return "Female"
        elif self == 3:
            return "Male"
        else:
            return "Won't say"

    @staticmethod
    def random() -> Sex:
        # only returns MALE or FEMALE for testing
        return Sex(random.randint(2, 3))
