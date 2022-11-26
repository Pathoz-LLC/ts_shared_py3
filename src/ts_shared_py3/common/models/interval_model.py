from __future__ import annotations
from datetime import date, timedelta
import random
import google.cloud.ndb as ndb
from common.models.baseNdb_model import BaseNdbModel

from common.schemas.tracking import IntervalMessage
from common.enums.commitLevel import DisplayCommitLvl
from common.utils.date_conv import (
    calcOverlappingDays,
    overlappingDates,
)

# from common.utils.date_conv import DateMessage, date_to_message

from constants import DISTANT_FUTURE_DATE

# class AccuracyRating(messages.Enum):
#     # Governs data validation
#     REPORTED = 1
#     CONTESTED = 2
#     VALIDATED = 3
#     DISCARDED = 4
#     THIRDPARTY = 5  # snooping for a friend


# this class IS stored as a repeating subtype of Tracking
# and also a NON-repeating subtype of Incident  (userInterval, reportingUserInterval)
# not sure it helps to index any of it when userId is not part of these fields?
class Interval(BaseNdbModel):
    """a relationship phase (together or broken up)
    latest/last/most-recent phase will always have endDate == DISTANT_FUTURE_DATE
    because you don't know when it will end
    """

    startDate = ndb.DateProperty(required=True)
    endDate = ndb.DateProperty(
        required=True, indexed=False, default=DISTANT_FUTURE_DATE
    )

    commitLevel = ndb.IntegerProperty(
        required=True,
        default=DisplayCommitLvl.CASUAL.value,
        indexed=False,
        choices=[cl.value for cl in DisplayCommitLvl],
    )

    def __str__(self):
        return "CL:{0} St:{1} En:{2}".format(
            self.commitLevel.code, self.startDate, self.comparableEndDate
        )

    @property
    def commitLevelEnum(self) -> DisplayCommitLvl:
        return DisplayCommitLvl(self.commitLevel)

    @property
    def comparableEndDate(self):
        # don't check overlaps with DISTANT future
        return date.today() if self.endDate >= DISTANT_FUTURE_DATE else self.endDate

    # TODO: comment out next two funcs and run tests
    # @property
    # def uiCommitment(self):
    #     # old: for backward compatibility
    #     # remove this;  do not use
    #     return self.commitLevel.code
    #
    # @property
    # def commitment(self):
    #     # old: for backward compatibility
    #     # remove this;  do not use
    #     return self.logic.code

    @property
    def logic(self):
        # returns a LogicCommitLvl
        return self.commitLevelEnum.logic

    @property
    def description(self):
        # return date history as a str
        _template = "Relationship Phase from {startDate} to {endDate} with Status of {commitment}"
        vals = dict(
            startDate=self.startDate,
            endDate=self.comparableEndDate,
            commitment=self.commitLevelEnum.code,
        )
        return _template.format(**vals)

    @property
    def dayCount(self):
        # returns # of days between start & end date
        return (self.endDate - self.startDate).days

    def overlapDayCount(self, intervalRec):
        """returns # of days that have some overlap
        with related dates on intervalRec
        """
        selfEndDate = self.comparableEndDate
        otherEndDate = intervalRec.comparableEndDate
        overlapDays = calcOverlappingDays(
            self.startDate, selfEndDate, intervalRec.startDate, otherEndDate
        )
        return overlapDays

    def earliestOverlapDate(self, intervalRec):
        # will return None if no overlap
        st, en = overlappingDates(
            self.startDate, self.endDate, intervalRec.startDate, intervalRec.endDate
        )
        return st

    # def before_put(self):
    #     pass

    @property
    def isTogetherPhase(self):
        # return true if this interval represents anything other than separated/brokenup/predating
        return not self.commitLevelEnum.isSeparated

    @property
    def isExclusivePhase(self):
        # return true if this interval represents anything other than separated/brokenup/predating
        # print("isExclusiveTest on {0} yields {1}".format(self.commitLevel.code, self.commitLevel.isExclusive))
        return self.commitLevelEnum.isExclusive

    def asDict(self):
        # used for testing via uidisplay_handlers
        return dict(
            startDate=self.startDate,
            endDate=self.endDate,
            commitLevel=self.commitLevelEnum.code,
        )

    @staticmethod
    def getSeries(count: int, startDt: date, endDt: date) -> list[Interval]:
        # builds a mock series of intervals for testing
        series = []
        daysRemaining = (endDt - startDt).days
        avgDaysInPhase = int(daysRemaining / count)
        minDaysInPhase = avgDaysInPhase - 90
        maxDaysInPhase = avgDaysInPhase + 90

        # daysConsumed = 0
        enDt = startDt - timedelta(days=1)
        for i in range(count):
            daysToAdd = random.randint(minDaysInPhase, maxDaysInPhase)
            daysToAdd = min(daysToAdd, daysRemaining)
            daysRemaining = daysRemaining - daysToAdd
            stDt = enDt + timedelta(days=1)
            enDt = stDt + timedelta(days=daysToAdd)
            # avoid adjacent phases
            curTopCL = (
                DisplayCommitLvl.BROKENUP if len(series) < 1 else series[0].commitLevel
            )
            uic = DisplayCommitLvl.random(butNot=curTopCL)
            # last row created is newest & should go at top
            itvl = Interval(startDate=stDt, endDate=enDt, commitLevel=uic)
            series.insert(0, itvl)

        series[0].endDate = DISTANT_FUTURE_DATE
        return series

    # def toMsg(self, persId=0):
    #     """
    #     Args:
    #         interval:

    #     Returns:
    #         IntervalMessage
    #     """
    #     im = IntervalMessage()
    #     im.persId = persId
    #     im.startDate = date_to_message(self.startDate)
    #     im.endDate = date_to_message(self.endDate)
    #     im.oldStartDate = im.startDate  # date_to_message(datetime.now())
    #     im.commitLvl = self.commitLevel.asApiMsg
    #     return im

    # @staticmethod
    # def newFromMsg(im):
    #     """
    #     Args:
    #         im(IntervalMessage):

    #     Returns:
    #         Interval
    #     """
    #     # print(im.commitLvl)
    #     # print("cmtLvl: {0}".format(im.commitLvl.displayCode))
    #     interval = Interval()
    #     interval.commitLevel = DisplayCommitLvl.fromStr(im.commitLvl.displayCode)
    #     interval.startDate = message_to_date(im.startDate)
    #     interval.endDate = message_to_date(im.endDate)
    #     return interval
