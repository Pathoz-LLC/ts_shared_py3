from __future__ import annotations
from typing import List, Tuple
from enum import IntEnum, unique
from datetime import datetime, timedelta
import google.cloud.ndb as ndb


from .baseNdb_model import BaseNdbModel

# usage:
# from common.models.person_activity import PersonActivity


@unique
class ActivityLogType(IntEnum):
    """what was logged about this person/prospect"""

    POS_FEEL = 0
    NEG_FEEL = 1
    POS_BEH = 2
    NEG_BEH = 3
    POS_CLCHG = 4
    NEG_CLCHG = 5
    VAL_ASSESS = 6  # always negative

    def __equ__(self, other):
        return self.value == other.value or self.value == other


class PersonActivity(BaseNdbModel):  # ndb.model.Expando
    """
    keeps count & date of each logged interaction
    used for finding old data to auto-breakup
    """

    lastChngDtTm = ndb.DateTimeProperty(auto_now=True, indexed=True)
    editCounts = ndb.IntegerProperty(repeated=True, indexed=False)

    @property
    def userId(self: PersonActivity):
        # return user ID as str
        return self.key.parent().string_id()

    @property
    def personId(self: PersonActivity):
        # return person/prospect ID as int
        return self.key.integer_id()

    @staticmethod
    def bumpFeeling(userIdStr: str, personIdInt: int, isPos=True):
        typ = ActivityLogType.POS_FEEL if isPos else ActivityLogType.NEG_FEEL
        PersonActivity.update(userIdStr, personIdInt, typ)

    @staticmethod
    def bumpBehavior(userIdStr: str, personIdInt: int, isPos: bool = True):
        typ = ActivityLogType.POS_BEH if isPos else ActivityLogType.NEG_BEH
        PersonActivity.update(userIdStr, personIdInt, typ)

    @staticmethod
    def bumpValues(userIdStr: str, listPersonIdsInt: list[int], isPos: bool = False):
        # receives multiple prospect IDs
        typ = ActivityLogType.VAL_ASSESS
        for pid in listPersonIdsInt:
            PersonActivity.update(userIdStr, pid, typ)

    @staticmethod
    def bumpCommitLevel(userIdStr: str, personIdInt: int, isPos: bool = True):
        typ = ActivityLogType.POS_CLCHG if isPos else ActivityLogType.NEG_CLCHG
        PersonActivity.update(userIdStr, personIdInt, typ)

    @staticmethod
    def update(userIdStr: str, personIdInt: int, logType: ActivityLogType):
        # assert isinstance(logType, ActivityLogType), 'wrong arg type'

        key = PersonActivity._makeKey(userIdStr, personIdInt)
        rec = key.get()
        if rec is None:
            rec = PersonActivity(editCounts=[0, 0, 0, 0, 0, 0, 0, 0])
            rec.key = key
        rec.lastChngDtTm = datetime.now()
        rec.editCounts[logType.value] += 1
        rec.put()

    @staticmethod
    def _makeKey(userIdStr: str, personIdInt: int):
        return ndb.Key("User", userIdStr, PersonActivity, personIdInt)

    @staticmethod
    def loadAllUntouchedFor(days: int = 30) -> List[Tuple]:
        # return list of tuple of (userId, prospectId)
        lastTouchDay = datetime.now() - timedelta(days=days)
        tdStart = lastTouchDay.replace(hour=0, minute=0, second=0)
        tdEnd = lastTouchDay.replace(hour=23, minute=59, second=59)
        qry = PersonActivity.query()
        qry = qry.filter(
            PersonActivity.lastChngDtTm >= tdStart, PersonActivity.lastChngDtTm <= tdEnd
        )
        results = qry.fetch(12000, keys_only=True, offset=0)
        # tup[0] is user id;  tup[1] is prospect id
        return [(key.parent().string_id(), key.integer_id()) for key in results]

    # def _pre_put_hook(self, future):
    #     pass
