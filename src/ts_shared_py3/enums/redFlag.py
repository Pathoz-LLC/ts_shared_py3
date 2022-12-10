from enum import IntEnum, unique
from google.cloud.ndb import model


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
