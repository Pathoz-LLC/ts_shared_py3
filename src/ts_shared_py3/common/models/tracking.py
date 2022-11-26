from __future__ import annotations
import logging
from datetime import date
import google.cloud.ndb as ndb
from typing import Optional, Iterable  # List

#
from common.models.baseNdb_model import BaseNdbModel
from scoring.commBehImpactConsenus import CommImpactConsensus
from common.enums.commitLevel import DisplayCommitLvl, LogicCommitLvl
from common.models.interval_model import Interval
from common.utils.date_conv import calcOverlappingDays, dateTime_to_epoch
from constants import DISTANT_FUTURE_DATE

log = logging.getLogger("tracking")
communityRiskStats = CommImpactConsensus()

# from common.models.person_model import Person   # , PersonLocal, MonitorStatus, CreateReason
# from common.models.user_model import User
# from common.models.tracking_model import Tracking


class Tracking(BaseNdbModel):
    """see class IntervalMgmtV2 for changes to intervals array
    starting interval (when began dating) is at end of list
    most recent interval is at TOP ie [0]
    """

    userKey = ndb.KeyProperty("User")  # user
    personKey = ndb.KeyProperty("Person")  # guy

    # if enabled is turned off, getIncidents will return empty list....
    enabled = ndb.BooleanProperty(default=True)  # true if active
    # list of all intervals currently being tracked
    # most recent at top & oldest at bottom of this list
    intervals = ndb.StructuredProperty(Interval, repeated=True)

    # metadata
    lastCheckDateTime = ndb.DateTimeProperty(
        indexed=False
    )  # when last did we check for overlap incidents
    addDateTime = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    modDateTime = ndb.DateTimeProperty(indexed=False)

    _canSave = True  # set False by roCloneWithActivePhases() method
    # normally we update personLocal rec when self.intervals is overwritten
    # saving track rec should fire check for incidents UNLESS
    # it is the incident check that is saving/putting this Tracking rec
    _shouldCheckForIncidentsOnPut = True

    @property
    def userId(self: Tracking) -> str:
        return self.userKey.string_id()

    @property
    def personId(self: Tracking) -> int:
        return self.personKey.integer_id()

    @property
    def intervalCount(self: Tracking) -> int:
        """how many intervals on this tracking rec"""
        return len(self.intervals)

    @property
    def startDate(self: Tracking) -> date:
        """date when tracking started (when they started dating)
        must return date and NOT datetime
        """
        if self.intervalCount < 1:
            return DISTANT_FUTURE_DATE
        earliestDate = self.intervals[-1].startDate
        assert isinstance(earliestDate, date), "must be date"
        return earliestDate

    @property
    def endDate(self: Tracking) -> date:
        """date when tracking of prospect ended (ie before recent breakup)
        should be endDate of most RECENT "together" phase

        must return date and NOT datetime
        """
        if self.intervalCount < 1:
            return date.today()
        recentInterval = self.latestInterval
        if recentInterval.isTogetherPhase:
            latestDate = date.today()
        else:
            # endDate of most RECENT "together" phase
            latestDate = recentInterval.endDate  # default for safety
            for i in range(1, self.intervalCount):
                if self.intervals[i].isTogetherPhase:
                    latestDate = self.intervals[i].endDate
                    break

        return latestDate

    @property
    def relationshipLengthDays(self: Tracking) -> int:
        """excludes broken up periods"""
        daysBrokenUp = self.daysBrokenUp
        return (self.endDate - self.startDate).days - daysBrokenUp

    @property
    def daysBrokenUp(self: Tracking) -> int:
        brokeIntervals = [
            i for i in self.intervals if i.commitLevel == DisplayCommitLvl.BROKENUP
        ]
        if len(brokeIntervals) < 1:
            return 0
        return sum([i.dayCount for i in brokeIntervals])

    @property
    def currentLogicCommitLvl(self: Tracking) -> LogicCommitLvl:
        """return CURRENT (based on most recent phase)
        logic/abstract commitment level
        """
        if self.intervalCount < 1:
            return DisplayCommitLvl.logicClSeparated()
        return self.intervals[0].commitLevel.logic

    @property
    def currentDisplayCommitLvl(self: Tracking) -> DisplayCommitLvl:
        """return CURRENT (based on most recent phase)"""
        if self.intervalCount < 1:
            return DisplayCommitLvl.default()
        return self.intervals[0].commitLevel

    @property
    def currentDisplayCommitLvlCode(self: Tracking) -> str:
        """return latest cl code"""
        return self.currentDisplayCommitLvl.code

    @property
    def latestInterval(self: Tracking) -> Optional[Interval]:
        # most recent at top of list
        if self.intervalCount > 0:
            return self.intervals[0]
        else:
            return

    def overlapDayCount(self: Tracking, trackRec: Tracking) -> int:
        """returns # of days (via intervals) on this rec that have some overlap
        with related dates on trackRec
        """
        assert isinstance(trackRec, Tracking), "invalid arg"
        # print("Tracking overlapDayCount (rough est)")
        # print("otherTrack->invlCnt:{0} start:{1} end:{2}".format(len(self.intervals), self.startDate, self.endDate))
        # print("myTrackRec->invlCnt:{0} start:{1} end:{2}".format(len(trackRec.intervals), trackRec.startDate, trackRec.endDate))
        overlapDays = calcOverlappingDays(
            self.startDate, self.endDate, trackRec.startDate, trackRec.endDate
        )
        # print("overlapDays: {0}".format(overlapDays))
        return overlapDays

    @staticmethod
    def loadByKeys(userKey: ndb.Key, personKey: ndb.Key) -> Tracking:
        query = Tracking.query(
            Tracking.userKey == userKey, Tracking.personKey == personKey
        )
        return query.get()

    @staticmethod
    def loadByIds(userId: str, personId: int) -> Tracking:
        userKey = ndb.Key("User", userId)
        personKey = ndb.Key("Person", personId)
        return Tracking.loadByKeys(userKey, personKey)

    def _pre_put_hook(self: Tracking):
        assert (
            self._canSave
        ), "This Tracking record is a read-only clone;  cannot save it"
        assert len(self.intervals) > 0, "must be at least 1 interval in tracking record"

    def _post_put_hook(self: Tracking, resultFuture):
        # Incident resolver updates tracking rec lastCheckDateTime & saves/puts rec
        # so it must set this to prevent an infinite loop
        if not self._shouldCheckForIncidentsOnPut:
            return

        # check again anytime this track rec changes
        # print("track after_put for Pers %s has %d" % (self.personKey.integer_id(), len(self.intervals)))
        log.info(
            "track after_put for Pers %s has %d (%s)",
            self.personKey.integer_id(),
            len(self.intervals),
            self.key,
        )
        # print(self.key)
        # TrackingTasks.checkForIncidents(self.key)
        # self._shouldCheckForIncidentsOnPut = False
