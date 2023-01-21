from __future__ import annotations
from enum import IntEnum, unique
import random
from marshmallow import fields, ValidationError

from google.cloud.ndb import model


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


#
class NdbSexProp(model.IntegerProperty):
    def _validate(self, value: int):
        if isinstance(value, (int)):
            return Sex(value)
        elif isinstance(value, (bytes, str)):
            return Sex(int(value))
        elif not isinstance(value, Sex):
            raise TypeError("expected Sex, int, str or unicd, got %s" % repr(value))

    def _to_base_type(self, sx: Sex):
        # convert Sex to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return Sex(value)


# from marshmallow import fields, ValidationError
class SexSerialized(fields.Field):
    """Field that serializes to a string of sex name"""

    def _serialize(self: SexSerialized, value: Sex, attr, obj, **kwargs):
        if value is None:
            return ""
        return value.name

    def _deserialize(self: SexSerialized, value: str, attr, data, **kwargs):
        try:
            return Sex[value]
        except ValueError as error:
            raise ValidationError("Pin codes must contain only digits.") from error

    @property
    def dump_default(self: SexSerialized) -> Sex:
        return Sex.UNKNOWN
