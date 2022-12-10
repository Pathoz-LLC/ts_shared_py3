from enum import IntEnum, unique
import google.cloud.ndb as ndb


@unique
class KeyTypeEnum(IntEnum):
    MBPHONE = 1  # mobile phone
    HMPHONE = 2  # home ph
    WKPHONE = 3
    SKYPE = 4
    # EMAIL/CHAT
    HMEMAIL = 10
    WKEMAIL = 11
    JABBER = 12
    # SOCIAL
    FACEBOOK = 20
    TWITTER = 21
    SNAPCHAT = 22
    PINTEREST = 23
    # SOMENEWSITE = 24


#
class NdbKeyTypeProp(ndb.IntegerProperty):
    def _validate(self, value: int):
        if isinstance(value, (int)):
            return KeyTypeEnum(value)
        elif isinstance(value, (bytes, str)):
            return KeyTypeEnum(int(value))
        elif not isinstance(value, KeyTypeEnum):
            raise TypeError(
                "expected KeyTypeEnum, int, str or unicd, got %s" % repr(value)
            )

    def _to_base_type(self, sx: KeyTypeEnum):
        # convert AccountType to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return KeyTypeEnum(value)
