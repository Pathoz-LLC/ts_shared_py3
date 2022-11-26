from __future__ import annotations

# import logging
import google.cloud.ndb as ndb
from datetime import datetime, date, time
from collections import namedtuple

#
from common.models.tracking import Tracking
from common.models.baseNdb_model import BaseNdbModel
from common.models.interval_model import Interval

# from common.utils.date_conv import date_to_message, message_to_date
from common.utils.date_conv import overlappingDates


# creating a flat immutable struc that is easy to pass around in complex logic below
IntervalRow = namedtuple(
    "IntervalRow",
    [
        "userKey",
        "trackKey",
        "intervalRowNum",
        "startDate",
        "endDate",
        "overlapDayCount",
        "interval",
    ],
)


class Incident(BaseNdbModel):
    """each user owns their own incident record
    and one will exist for each overlap found with another user for the same personKey

    for adjacent phases without a breakup, we should only create ONE incident
    and pick the most serious commitment level for it

    if the newest phase in either interval (ie no end date)
    is the one that causes the overlap, then the incident rec is stale
    as soon as it is written.  (we don't know when that phase will end)
    See "incidentToMsg" func where we currently substitute today
    but we should be checking those for current
    """

    # fkeys
    trackingKey = ndb.KeyProperty(Tracking, required=True)
    userKey = ndb.KeyProperty("User", required=True)
    personKey = ndb.KeyProperty("Person", required=True)  # the "playa"

    # # status
    # # userTruthOpinion = ndb.IntegerProperty(indexed=False, default=0)    # 0 means not seen; 1-4 = true->false
    # userTruthOpinion = msgprop.EnumProperty(TruthOpinion, default=TruthOpinion.UNSEEN, indexed=False)
    evidenceStatus = ndb.IntegerProperty(required=True, default=0, indexed=False)

    # details: reportingUser is the OTHER user
    reportingUserId = ndb.StringProperty(indexed=True)
    reportingUserSex = ndb.IntegerProperty(indexed=False, default=0)
    earliestOverlapDate = ndb.DateProperty(indexed=True)  # to select for new recs

    overlapDays = ndb.IntegerProperty(indexed=False, default=0)
    userIntervalRowNum = ndb.IntegerProperty(
        indexed=True, default=0
    )  # used to identify which Interval caused this overlap
    userInterval = ndb.StructuredProperty(Interval, repeated=False)
    reportingUserInterval = ndb.StructuredProperty(Interval, repeated=False)
    reportingUserIntervalRowNum = ndb.IntegerProperty(indexed=False, default=0)

    # housekeeping
    # if reporting user changes their dates, store old vals here
    repUserIntervalReviseHistory = ndb.StringProperty(default="")
    addDateTime = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    modDateTime = ndb.DateTimeProperty(
        auto_now=True, indexed=False
    )  # when user updated with their truth opinion

    @property
    def isInvalid(self) -> bool:  # bool
        return self.overlapStartDate is None or self.evidenceStatus == 3333

    @property
    def overlapPeriod(self) -> tuple[date, date]:  # returns date obj (no time)
        # return start & end of any overlap period; since incident exists, we can assume one does exist
        st, en = overlappingDates(
            self.userInterval.startDate,
            self.userInterval.endDate,
            self.reportingUserInterval.startDate,
            self.reportingUserInterval.endDate,
        )
        return st, en

    @property
    def overlapStartDate(self) -> date:  # returns date obj (no time)
        st, en = self.overlapPeriod
        return st

    @property
    def overlapEndDate(self) -> date:  # returns date obj (no time)
        st, en = self.overlapPeriod
        return en

    @property
    def involvesAnUnboundedInterval(self) -> date:  #
        st, en = self.overlapPeriod
        return st

    @staticmethod
    def createNew(
        personKey: ndb.Key,
        userIntervalTuple: IntervalRow,
        reportingUserIntervalTuple: IntervalRow,
    ) -> Incident:
        """create new Interval based on args above

          , , personKey,
        reportingUserIntervalTuple.userKey, ,
                                                                 , curIntervalRowNum
        """
        newIncident = Incident()
        newIncident.trackingKey = userIntervalTuple.trackKey
        newIncident.userKey = userIntervalTuple.userKey
        newIncident.personKey = personKey
        # point to the OTHER user as the one reporting
        newIncident.reportingUserId = reportingUserIntervalTuple.userKey.id()
        newIncident.reportingUserSex = 0

        newIncident.userInterval = userIntervalTuple.interval
        newIncident.userIntervalRowNum = userIntervalTuple.intervalRowNum
        #
        newIncident.reportingUserInterval = reportingUserIntervalTuple.interval
        newIncident.reportingUserIntervalRowNum = (
            reportingUserIntervalTuple.intervalRowNum
        )
        newIncident.addDateTime = datetime.now()
        newIncident.modDateTime = datetime.now()

        # the newIncident.put() operation will set  overlapDays & earliestOverlapDate
        return newIncident

    @staticmethod
    def loadByTrackId(
        trackingKey: ndb.Key, afterDate: datetime = datetime(2000, 1, 1)
    ) -> list[Incident]:
        """
        get all incidents related to this tracking Rec (represents a user & person)
            remove the ones that have been invalidated by the overlap comparison job
            also create fake User ID's (start at 1)
            and sequence the overlaps per user so each is numbered
        Args:
            trackingKey:
            afterDate:

        Returns:  array of Incident

        """
        foundIncidents = (
            Incident.query(
                Incident.trackingKey == trackingKey,
                Incident.earliestOverlapDate > afterDate,
            )
            .order(-Incident.earliestOverlapDate)
            .fetch()
        )

        perPersonOverlapCount = dict()
        seenUserIDs = []
        shortUserID = 1
        res: list[Incident] = []
        for incd in foundIncidents:
            if incd.evidenceStatus != 3333:
                if incd.reportingUserId not in seenUserIDs:
                    seenUserIDs.append(incd.reportingUserId)

                shortUserID = seenUserIDs.index(incd.reportingUserId) + 1

                incdSeqNum = perPersonOverlapCount.setdefault(incd.reportingUserId, 1)
                perPersonOverlapCount[incd.reportingUserId] = incdSeqNum + 1

                incd.reportingUserDisplayID = shortUserID
                incd.reportingUserIncdSeqNum = incdSeqNum
                res.append(incd)
        return res

    @staticmethod
    def loadByUserId(userId: str, persId: int = 0) -> list[Incident]:
        """person ID is optional
        return list of found incidents
        """
        userKey = ndb.Key("User", userId)
        if persId > 0:
            personKey = ndb.Key("Person", persId)
            query = Incident.query(
                Incident.userKey == userKey, Incident.personKey == personKey
            )
        else:
            query = Incident.query(Incident.userKey == userKey)
        return query.fetch()

    @staticmethod
    def deleteExisting(trackKey) -> None:
        allExist = Incident.loadByTrackId(trackKey)
        for ivl in allExist:
            ivl.key.delete()

    def _pre_put_hook(self) -> None:
        """runs at each put operation
        set overlapDays & earliestOverlapDate
        """
        self.overlapDays = self.userInterval.overlapDayCount(self.reportingUserInterval)
        self.earliestOverlapDate = self.overlapStartDate
