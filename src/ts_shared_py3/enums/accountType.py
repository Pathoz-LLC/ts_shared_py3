from enum import IntEnum, unique
import random

# import google.cloud.ndb


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
