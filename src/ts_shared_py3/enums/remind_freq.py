from __future__ import annotations
from enum import IntEnum, unique
import random

from google.cloud.ndb import model

_DISPL_VALS = [
    "Never",
    "Monthly",
    "Weekly",
    "Bi-weekly",
    "Daily",
    "Twice Daily",
    "Hourly",
]


@unique
class RemindFreq(IntEnum):
    """"""

    NEVER = 0
    MONTHLY = 1
    WEEKLY = 2
    TWICE_WEEKLY = 3
    DAILY = 4
    TWICE_DAILY = 5
    HOURLY = 6

    @property
    def toDisplayVal(self) -> str:
        return _DISPL_VALS[self.value]

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
        # convert RemindFreq to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return RemindFreq(value)


from marshmallow import fields, ValidationError


class ReminderFreqSerialized(fields.Field):
    """"""

    def _serialize(
        self: ReminderFreqSerialized, value: RemindFreq, attr, obj, **kwargs
    ) -> str:
        if value is None:
            return ""
        return value.name

    def _deserialize(
        self: ReminderFreqSerialized, value: str, attr, data, **kwargs
    ) -> RemindFreq:
        try:
            return RemindFreq[value]
        except ValueError as error:
            raise ValidationError("") from error

    @property
    def dump_default(self: ReminderFreqSerialized) -> RemindFreq:
        return RemindFreq.DAILY
