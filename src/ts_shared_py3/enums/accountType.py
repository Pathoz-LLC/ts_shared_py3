from __future__ import annotations
from enum import IntEnum, unique
import random
from marshmallow import fields, ValidationError
from marshmallow_dataclass import NewType
from google.cloud.ndb import model


@unique
class AccountType(IntEnum):
    """sex of user prospect or inner circle member"""

    FREE = 0
    PRO = 1  # Gold
    PREMIUM = 2  # Diamond
    MODERATOR = 3
    ADMIN = 4
    GOD = 5

    def __equ__(self, other):
        return self.value == other.value or self.value == other

    @staticmethod
    def fromProdID(id):
        if id == "com.pathoz.touchstone.sub.gold":
            return AccountType.PRO

        elif id == "com.pathoz.touchstone.sub.premium":
            return AccountType.PREMIUM

        else:
            return AccountType.FREE

    @property
    def shouldPushNotifyIncidents(self):
        return self == AccountType.PREMIUM

    @staticmethod
    def fromString(val):
        # expect val to be int as str
        return AccountType(int(val))
        # val = val.lower()
        # if val == "free":
        #     return AccountType.FREE
        # elif val == "pro":
        #     return AccountType.PRO
        # elif val == "premium":
        #     return AccountType.PREMIUM
        # elif val == "moderator":
        #     return AccountType.MODERATOR
        # elif val == "admin":
        #     return AccountType.ADMIN
        # else:
        #     return AccountType.FREE

    @property
    def toDisplayVal(self):
        if self == 0:
            return "Free"
        elif self == 1:
            return "Gold"
        elif self == 2:
            return "Diamond"
        elif self == 3:
            return "Moderator"
        elif self == 4:
            return "Admin"
        else:
            return "Free"

    # for testing
    @staticmethod
    def random():
        return AccountType(random.randint(0, 2))


# from google.cloud.ndb import model
class NdbAcctTypeProp(model.IntegerProperty):
    def _validate(self, value: int):
        if isinstance(value, (int)):
            return AccountType(value)
        elif isinstance(value, (bytes, str)):
            return AccountType(int(value))
        elif not isinstance(value, AccountType):
            raise TypeError(
                "expected CommitLevel_Display, int, str or unicd, got %s" % repr(value)
            )

    def _to_base_type(self, sx: AccountType):
        # convert AccountType to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return AccountType(value)


class AcctTypeSerialized(fields.Enum):
    """serialization"""

    def _serialize(
        self: AcctTypeSerialized, value: AccountType, attr, obj, **kwargs
    ) -> str:
        if value is None:
            return ""
        return value.name

    def _deserialize(
        self: AcctTypeSerialized, value: str, attr, data, **kwargs
    ) -> AccountType:
        try:
            return AccountType[value]
        except ValueError as error:
            raise ValidationError("") from error

    # def dump_default(self: AcctTypeSerialized) -> AccountType:
    #     return AccountType.FREE


# AcctTypeSerializedMsg = NewType(
#     "AcctTypeSerialized", AcctTypeSerialized, field=fields.Enum(AccountType)
# )
