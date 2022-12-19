from __future__ import annotations
from enum import IntEnum, unique
import random

from google.cloud.ndb import model


@unique
class RemindFreq(IntEnum):
    """sex of user prospect or inner circle member"""

    NEVER = 0
    UNKNOWN = 1
    FEMALE = 2
    MALE = 3

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
    def random() -> RemindFreq:
        # only returns MALE or FEMALE for testing
        return RemindFreq(random.randint(2, 3))


#
class NdbRemindProp(model.IntegerProperty):
    def _validate(self, value: int):
        if isinstance(value, (int)):
            return RemindFreq(value)
        elif isinstance(value, (bytes, str)):
            return RemindFreq(int(value))
        elif not isinstance(value, RemindFreq):
            raise TypeError("expected Sex, int, str or unicd, got %s" % repr(value))

    def _to_base_type(self, sx: RemindFreq):
        # convert Sex to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return RemindFreq(value)
