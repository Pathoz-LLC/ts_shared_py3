from enum import Enum, unique


@unique
class RedFlagType(Enum):
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


# class NdbRedFlagProp(ndb.IntegerProperty):
#     def _validate(self, value):
#         if isinstance(value, (int, long)):
#             return RedFlagType(value)
#         elif isinstance(value, (str, unicode)):
#             return RedFlagType(int(value))
#         elif not isinstance(value, RedFlagType):
#             raise TypeError('expected RedFlagType, int, str or unicd, got %s' % repr(value))

#     def _to_base_type(self, sx):
#         # convert to int
#         if isinstance(sx, int):
#             return sx
#         return int(sx.value)

#     def _from_base_type(self, value):
#         return RedFlagType(value)  # return RedFlagType
