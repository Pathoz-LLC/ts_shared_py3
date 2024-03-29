from __future__ import annotations
from enum import IntEnum, unique
from marshmallow_dataclass import NewType
from google.cloud.ndb import model
from marshmallow import fields, ValidationError


@unique
class RedFlagType(IntEnum):
    """ """

    NEVERSET = 0
    REVENGE_PORN = 1
    DEEP_FAKE = 2
    PHYSICAL_ABUSE = 4
    DATE_RAPE = 8

    @property
    def convictionVoteCount(self):
        # number votes req to get the red-flag badge
        return 5

    def countExceedsThreshold(self, count):
        return count >= self.convictionVoteCount


class NdbRedFlagProp(model.IntegerProperty):
    def _validate(self, value: RedFlagType):
        if isinstance(value, int):
            return RedFlagType(value)
        elif isinstance(value, str):
            return RedFlagType(int(value))
        elif not isinstance(value, RedFlagType):
            raise TypeError(
                "expected RedFlagType, int, str or unicd, got %s" % repr(value)
            )

    def _to_base_type(self, sx: RedFlagType):
        # convert to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return RedFlagType(value)  # return RedFlagType


class RedFlagTypeSerializedMa(fields.Enum):
    """"""

    def _serialize(
        self: RedFlagTypeSerializedMa, value: RedFlagType, attr, obj, **kwargs
    ) -> str:
        if value is None:
            return ""
        return value.name

    def _deserialize(
        self: RedFlagTypeSerializedMa, value: str, attr, data, **kwargs
    ) -> RedFlagType:
        try:
            return RedFlagType[value]
        except ValueError as error:
            raise ValidationError("") from error


# RedFlagTypeSerializedMsg = NewType("RedFlagTypeSerialized", str, _RedFlagTypeSerialized)
