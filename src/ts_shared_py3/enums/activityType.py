from enum import IntEnum, unique
from random import randint
from google.cloud.ndb import model


@unique
class ActivityType(IntEnum):
    """event type for community news feed
    must mirror type xxx on the client
    """

    # prospect
    # deepening connection
    PROSPECT_ADDED = 0
    PROSPECT_STATUS_INCREASE = 1
    # distancing connection
    PROSPECT_STATUS_DECREASE = 2
    # PROSPECT_DOGHOUSE = 3
    PROSPECT_STATUS_BREAKUP = 4
    PROSPECT_DELETED = 5

    # pertains to Phases
    PROSPECT_DTCHANGE_LATEST = 10
    PROSPECT_DTCHANGE_PRIOR = 11
    PROSPECT_PHASE_REMOVED = 12

    # behavior
    BEHAVIOR_REPORTED = 20
    # BEHAVIOR_SHARED = 21

    FEELING_RECORDED = 30

    # value assements
    VALUE_ASSESSED = 40
    VALUE_SHARED = 41

    INCIDENT_OCCURED = 50

    # community
    # FRIEND_ADDED = 60

    @staticmethod
    def allIds():
        # for random data generator
        # only want certain rec types
        return [1, 2, 4, 20, 30, 50]
        # return [0, 1, 2, 4, 5, 10, 11, 12, 20, 30, 40, 41, 50]

    @staticmethod
    def random():
        randInt = randint(0, len(ActivityType.allIds()) - 1)
        typInt = ActivityType.allIds()[randInt]
        return ActivityType(typInt)

    @property
    def isPublic(self):
        return self in [ActivityType.BEHAVIOR_SHARED, ActivityType.VALUE_SHARED]

    @property
    def hasBehCode(self):
        # these two types should always be paired with behCode
        return self.appliesToBehavior or self.appliesToValues

    @property
    def hasCommitLevel(self):
        # should always be paired with commitment level
        return self.appliesToProspect

    @property
    def appliesToProspect(self):
        return self.value < 20

    @property
    def appliesToBehavior(self):
        # or self == ActivityType.FEELING_RECORDED
        return self.value > 19 and self.value < 39

    @property
    def appliesToValues(self):
        return self.value > 39 and self.value < 50


class NdbActivityTypeProp(model.IntegerProperty):
    def _validate(self, value: int):
        if isinstance(value, (int)):
            return ActivityType(value)
        elif isinstance(value, (bytes, str)):
            return ActivityType(int(value))
        elif not isinstance(value, ActivityType):
            raise TypeError(
                "expected DisplayCommitLvl, int, str or unicd, got %s" % repr(value)
            )

    def _to_base_type(self, sx: ActivityType):
        # convert ActivityType to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return ActivityType(value)
