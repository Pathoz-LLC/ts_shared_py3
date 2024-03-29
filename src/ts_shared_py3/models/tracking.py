from __future__ import annotations
import logging
from typing import List
from datetime import datetime, date, timedelta
import google.cloud.ndb as ndb
from typing import Optional, Iterable  # List

#
from ..scoring.commBehImpactConsenus import CommImpactConsensus
from ..api_data_classes.behavior import BehEntryWrapperMessage
from ..api_data_classes.scoring import RequRelationshipOverviewData
from .baseNdb_model import BaseNdbModel
from .user import DbUser
from ..enums.commitLevel import CommitLevel_Display, CommitLevel_Logic
from .interval import Interval
from ..utils.date_conv import calcOverlappingDays, dateTime_to_epoch
from ..constants import DISTANT_FUTURE_DATE

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

    # userKey = ndb.KeyProperty("User")  # user
    personId = ndb.IntegerProperty(indexed=True)  # prospect
    # if enabled is turned off, getIncidents will return empty list....
    enabled: bool = ndb.BooleanProperty(default=True)  # true if active
    # list of all intervals currently being tracked
    # most recent at top & oldest at bottom of this list
    intervals: list[Interval] = ndb.StructuredProperty(Interval, repeated=True)

    # metadata
    lastCheckDateTime: datetime = ndb.DateTimeProperty(
        indexed=False
    )  # when last did we check for overlap incidents
    addDateTime: datetime = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    modDateTime: datetime = ndb.DateTimeProperty(auto_now=True, indexed=False)

    _canSave: bool = True  # set False by roCloneWithActivePhases() method
    # normally we update personLocal rec when self.intervals is overwritten
    # saving track rec should fire check for incidents UNLESS
    # it is the incident check that is saving/putting this Tracking rec
    _shouldCheckForIncidentsOnPut: bool = True

    @staticmethod
    def loadOrCreate(
        userId: str,
        persId: int,
        *args,
        startDt: date = None,
        cl: CommitLevel_Display = CommitLevel_Display.CASUAL,
    ) -> Tracking:
        track = Tracking.loadByIds(userId=userId, personId=persId)
        if track is not None:
            return track
        track = Tracking(
            personId=persId,
            enabled=True,
            intervals=[
                Interval(
                    startDate=date.today(),
                    endDate=DISTANT_FUTURE_DATE,
                    commitLevel=cl.value,
                )
            ],
            lastCheckDateTime=datetime.now(),
        )
        track.key = Tracking.makeUserPersKey(userId, persId)
        track.put()
        return track

    @property
    def intervalsAsBehMsgList(self: Tracking) -> list[BehEntryWrapperMessage]:
        return [
            BehEntryWrapperMessage(
                behaviorCode=ivl.commitLevel.name, oppBehaviorCode=""
            )
            for ivl in self.intervals
        ]

    @property
    def userId(self: Tracking) -> str:
        return self.key.parent.string_id()

    @property
    def personId(self: Tracking) -> int:
        return self.key.integer_id()

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
            i for i in self.intervals if i.commitLevel == CommitLevel_Display.BROKENUP
        ]
        if len(brokeIntervals) < 1:
            return 0
        return sum([i.dayCount for i in brokeIntervals])

    @property
    def currentLogicCommitLvl(self: Tracking) -> CommitLevel_Logic:
        """return CURRENT (based on most recent phase)
        logic/abstract commitment level
        """
        if self.intervalCount < 1:
            return CommitLevel_Display.logicClSeparated()
        return self.intervals[0].commitLevel.logic

    @property
    def currentDisplayCommitLvl(self: Tracking) -> CommitLevel_Display:
        """return CURRENT (based on most recent phase)"""
        if self.intervalCount < 1:
            return CommitLevel_Display.default()
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
    def makeUserPersKey(userId: str, personId: int) -> ndb.Key:
        return ndb.Key("Tracking", personId, parent=ndb.Key("User", userId))

    @staticmethod
    def loadByKeys(userKey: ndb.Key, personKey: ndb.Key) -> Tracking:
        # query = Tracking.query(
        #     Tracking.userKey == userKey, Tracking.personKey == personKey
        # )
        key = Tracking.makeUserPersKey(userKey.string_id(), personKey.integer_id())
        return key.get()

    @staticmethod
    def loadByIds(userId: str, personId: int) -> Tracking:
        # userKey = ndb.Key("User", userId)
        # personKey = ndb.Key("Person", personId)
        # return Tracking.loadByKeys(userKey, personKey)
        key = Tracking.makeUserPersKey(userId, personId)
        return key.get()

    @staticmethod
    def createInitialFromDialog(
        userId: str, personId: int, intervalList: List[Interval]
    ):
        # will update or create (& store) the record
        userKey = ndb.Key("User", userId)
        personKey = ndb.Key("Person", personId)
        newTrackRec = Tracking.loadByKeys(userKey, personKey)
        if not newTrackRec:
            newTrackRec = Tracking(
                enabled=True,
                intervals=[],
                lastCheckDateTime=datetime.now(),
            )
            newTrackRec.key = Tracking.makeUserPersKey(userId, personId)

        newTrackRec.intervals = intervalList
        return newTrackRec.put()

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
            "track after_put for Pers %d has %d (%s)",
            self.key.integer_id(),
            len(self.intervals),
            self.key,
        )

    @staticmethod
    def loadOrCreateForDiffUser(
        notThisUserId: str,
        persId: int,
        otherUserId: str,
        *args,
        startDt: date = None,
        cl: CommitLevel_Display = CommitLevel_Display.EXCLUSIVE_MA,
    ) -> Tracking:
        """
        not yet using otherUserId to shortcut searching below
        """
        # to clean up data;  disable after 5/1/24
        Tracking._setAllPersonId()
        #
        allTrackForPers: List[Tracking] = (
            ndb.Query(Tracking).filter(Tracking.personId == persId).fetch()
        )

        startDt = startDt or date.today() - timedelta(days=10 * 365)
        if len(allTrackForPers) < 2:
            # no other user's are dating this person;  create a new one
            curUserTrack = allTrackForPers[0]
            assert (
                curUserTrack.key.parent.string_id() == notThisUserId
            ), "should be this user if only one exists"
            otherUsers = DbUser.query().fetch(3)
            otherUsers = [u for u in otherUsers if u.id != notThisUserId]

            firstNewUser = otherUsers[0]
            newTrack = Tracking.loadOrCreate(
                firstNewUser.id, persId, startDt=startDt, cl=cl
            )
            return newTrack

        # find one for a different user to return
        for tr in allTrackForPers:
            if tr.userId != notThisUserId:
                # logic below is not complete if they have multiple intervals
                # because we are not clearly forcing overlap
                earliestIvl = tr.intervals[-1]
                earliestIvl.startDate = startDt or date.today() - timedelta(
                    days=4 * 365
                )
                earliestIvl.commitLevel = cl
                # latestInterval = tr.intervals[0]
                tr.intervals[0].commitLevel = cl.value
                tr.put()
                return tr
        return None

    @staticmethod
    def _setAllPersonId():
        qAllRecs = ndb.Query(Tracking).fetch()
        for rec in qAllRecs:
            rec.personId = rec.key.integer_id()
            rec.put()

        # print(self.key)
        # TrackingTasks.checkForIncidents(self.key)
        # self._shouldCheckForIncidentsOnPut = False

    # @staticmethod
    # def loadRelStateOverview(user: DbUser, relationshipOverviewMsg: RequRelationshipOverviewData):
    #     """  NIU:  moved to scoring server

    #     called by score/chart/bigPicture screen
    #     Args:
    #         User:
    #         RequRelationshipOverviewMsg: (3 props)

    #     Returns: ProspectScoreMsg
    #     """
    #     userProspScoreCollection = Tracking._rescoreForUser(user, relationshipOverviewMsg.persId, relationshipOverviewMsg.monthsBackFromNow)
    #     sm = userProspScoreCollection.toScoresMsg(relationshipOverviewMsg.priorUserScore,
    #          relationshipOverviewMsg.priorAppScore, relationshipOverviewMsg.persName)
    #     Tracking._updateProspectLocal(user, relationshipOverviewMsg.persId, userProspScoreCollection)
    #     return sm
