from __future__ import annotations
from datetime import date, datetime
import google.cloud.ndb as ndb
from typing import Optional, Iterable  # List

#
from common.models.entry_adapter import InputEntryAdapter
from common.models.baseNdb_model import BaseNdbModel
from common.enums.scoreRuleType import ScoreRuleType
from common.enums.scoreScope import ScoreScope
from common.utils.arg_types import ArgTypes
from common.utils.date_conv import lastDayOfMonth as convertToLastDayOfMonth
from .interval_model import Interval

# EMPTY_DEFAULT_USER: ScopedRawScore = None
# EMPTY_DEFAULT_APP: ScopedRawScore = None

TEST_COUNT: int = 0


class ScopedRawScore(ndb.Model):
    # app, user, flock, community or communication
    impactType = ndb.IntegerProperty(
        default=ScoreScope.APP_AND_USER,
        choices=[ic.value for ic in ScoreScope],
        indexed=False,
    )
    # stored in 0 <-> 1 format
    yVal = ndb.FloatProperty(default=0.0, indexed=False)

    # @staticmethod
    # def fromDst(yVal: float, impCom: ScoreScope = ImpactCommunity.APP_AND_USER):
    #     # yVal = dst.userScore if impCom == ScoreScope.APP_AND_USER else dst.appScore
    #     return ScopedRawScore(impactType=impCom, yVal=yVal)

    @staticmethod
    def emptyDefault(typ: ScoreScope) -> ScopedRawScore:
        # sending 91 recs but this is only being called 78 times;  I'm confused??
        # global TEST_COUNT
        # TEST_COUNT += 1
        # print(
        #     "{0} ScopedScore missing for {1}  (should total 91)".format(
        #         TEST_COUNT, typ.name
        #     )
        # )
        return ScopedRawScore(impactType=typ.value, yVal=0.50)


class RawDayScores(ndb.Model):
    """
    collection of score-types (user or app) for each day
    stored under ScoresPersist.perDayScores
    all REAL-ENTRY based Scores for a month
    no interpolation or copies stored here
    """

    day = ndb.DateProperty(indexed=False)  # exact day of month for this prospect
    scores = ndb.LocalStructuredProperty(ScopedRawScore, repeated=True, indexed=False)
    # rippleEffect = ndb.FloatProperty(default=0.0)
    # itemsBitCode represents the types of records that created this day
    itemsBitCode = ndb.IntegerProperty(default=0, indexed=False)

    def _typedIterable(
        self: RawDayScores, impactType: ScoreScope
    ) -> Iterable(ScopedRawScore):
        return (ss for ss in self.scores if ss.impactType == impactType)

    @property
    def toAdapterRec(self: RawDayScores) -> InputEntryAdapter:
        return InputEntryAdapter(
            ruleType=ScoreRuleType.PRE_SCORED,
            occurDt=self.day,
            args=[self.communityHybrid, self.userApp, self.itemsBitCode],
            scored=True,
            saveDtTm=self.day,
            debugRecId="storedNonUnique",
        )

    @property
    def userApp(self: RawDayScores) -> float:
        # scores is a list with 1 rec of each type
        # find the one you seek or use empty default
        ss = next(
            self._typedIterable(ScoreScope.APP_AND_USER),
            ScopedRawScore.emptyDefault(ScoreScope.APP_AND_USER),
        )
        return ss.yVal

    @property
    def communityHybrid(self: RawDayScores) -> float:
        ss = next(
            self._typedIterable(ScoreScope.COMMUNITY_HYBRID),
            ScopedRawScore.emptyDefault(ScoreScope.COMMUNITY_HYBRID),
        )
        return ss.yVal

    @property
    def yearMonthKeyStr(self: RawDayScores) -> str:
        # ignore DAY component of date (it's always 1st)
        # identify which ScorePerist (ie month) window this score should live in for persist
        return PersonMonthScoresRaw.keyStrFromDate(self.day)

    @staticmethod
    def fromDtCalcRes(
        dst: ArgTypes.DatedCalcResult,
    ) -> RawDayScores:  # -> RawDayScores:
        return RawDayScores(
            day=dst.pointDt,
            itemsBitCode=dst.itemsBitCode,
            scores=[
                ScopedRawScore(
                    impactType=ScoreScope.APP_AND_USER, yVal=dst.userAppScore
                ),
                ScopedRawScore(
                    impactType=ScoreScope.COMMUNITY_HYBRID, yVal=dst.communityScore
                ),
            ],
        )


ListConsolidatedRawDayScores = list[RawDayScores]


class PersonMonthScoresRaw(BaseNdbModel):
    """month of previously calculated user/prospect scores
        Key:  UserID->ProspectID->YYMM01

    also includes any ripple objects that occurred in this month
    LocalStructuredProperty are compressed & not indexed

    in future, we'll change query to only go back x months using monthStartDt
    or build some structure that rolls prior years into a summary obj
    """

    monthStartDt = ndb.DateProperty(indexed=True)
    # LocalStructuredProperty is not indexed
    # perDayScores only holds days of REAL user entries/input
    perDayScores = ndb.LocalStructuredProperty(RawDayScores, repeated=True)
    # rippleEffects = ndb.LocalStructuredProperty(RippleEffect, repeated=True)
    intervals = ndb.StructuredProperty(Interval, repeated=True)

    # metadata
    # lastCalcDtTm should be set whenever saved
    lastCalcDtTm = ndb.DateTimeProperty(auto_now=True, indexed=False)
    addDtTm = ndb.DateTimeProperty(auto_now_add=True, indexed=False)

    @classmethod
    def loadOrCreate(
        cls, userId: str, persId: int, dateInMonth: date
    ) -> PersonMonthScoresRaw:
        userPersonKey = BaseNdbModel.makeAncestor(userId, persId)
        yearMonthKeyStr = BaseNdbModel.keyStrFromDate(dateInMonth)
        sspRecKey = ndb.Key(cls.__name__, yearMonthKeyStr, parent=userPersonKey)
        sspRec = sspRecKey.get()
        if sspRec is not None:
            return sspRec

        print("creating new PersonMonthScoresRaw for month {0}".format(dateInMonth))
        sspRec = PersonMonthScoresRaw(
            monthStartDt=dateInMonth.replace(day=1), perDayScores=[], intervals=[]
        )
        sspRec.key = sspRecKey
        return sspRec

    # @staticmethod
    # def newForMonth(
    #     userID: str,
    #     personID: int,
    #     monthStartDt: date,
    #     perDayScores: list[RawDayScores] = [],
    # ):
    #     assert isinstance(monthStartDt, date), "invalid arg"
    #     assert perDayScores is None or isinstance(perDayScores, list), "invalid arg"
    #     # assert rippleEffects is None or isinstance(rippleEffects, list), "invalid arg"
    #     sp = PersonMonthScoresRaw()
    #     sp.monthStartDt = monthStartDt.replace(day=1)
    #     sp.perDayScores = perDayScores
    #     sp.intervals = []
    #     # create key so rec can be saved
    #     sp.key = PersonMonthScoresRaw.makeKey(userID, personID, sp.monthStartDt)
    #     # assert sp.key == key, "Error:  check this??"
    #     return sp

    # @staticmethod
    # def storeScoredDays(userId: str, persId: int, dayRecs: list):
    #     """group all recs by occurDt month"""
    #     monthListMap = {}
    #     for rec in dayRecs:
    #         lst = monthListMap.setdefault(rec.yearMonthKeyStr, [])
    #         lst.append(rec)

    #     for monthKey, recList in monthListMap.items:
    #         # recKey = ndb.Key('User', userId, 'Person', persId, '', monthKey)
    #         recKey = ScoresPersist.makeKey(userId, persId, monthKey)

    @staticmethod
    def loadMonthsInRange(
        userId: str, persId: int, minDt: date, maxDt: date
    ) -> list[PersonMonthScoresRaw]:
        # return map with key being month str
        # ancestorKey = ndb.Key("User", userId, "Person", persId)
        ancestorKey = BaseNdbModel.makeAncestor(userId, persId)
        q = PersonMonthScoresRaw.query(ancestor=ancestorKey).filter(
            PersonMonthScoresRaw.monthStartDt >= minDt,
            PersonMonthScoresRaw.monthStartDt <= maxDt,
        )
        return q.fetch()

    def _idxIfExists(self: PersonMonthScoresRaw, dt: date) -> Optional[int]:
        return next((i for i, x in enumerate(self.perDayScores) if x.day == dt), None)

    def appendManyDayScores(self: PersonMonthScoresRaw, dsRecs) -> None:
        # curRecCnt = len(self.perDayScores)
        if (
            len(self.perDayScores) < 1 or len(dsRecs) > 29
        ):  # a new month rec so no need to loop/replace
            self.perDayScores = dsRecs
        else:
            for r in dsRecs:
                self.appendOneDayScore(r)

    def appendOneDayScore(self: PersonMonthScoresRaw, dsRec: RawDayScores) -> None:
        # don't add duplicates; replace or add if not found
        assert isinstance(dsRec, RawDayScores), "oops"
        assert (
            dsRec.day.month == self.monthStartDt.month
            and dsRec.day.year == self.monthStartDt.year
        )
        idx = self._idxIfExists(dsRec.day)
        if idx is None:
            self.perDayScores.append(dsRec)
        else:
            self.perDayScores[idx] = dsRec

        # g = (i for i, ds in enumerate(self.perDayScores) if ds.day == dsRec.day)
        # try:
        #     # find matching rec to replace/update;  otherwise, add new
        #     idx = next(
        #         (i for i, ds in enumerate(self.perDayScores) if ds.day == dsRec.day)
        #     )  # replace if succeeds
        #     self.perDayScores[idx] = dsRec
        # except StopIteration:  # insert if fails
        #     self.perDayScores.append(dsRec)

    # def appendRippleEffect(self, rEffect):
    #     # allow one or more
    #     if isinstance(rEffect, RippleEffect):
    #         self.rippleEffects.append(rEffect)
    #     elif isinstance(rEffect, list) and len(rEffect) > 0:
    #         assert isinstance(rEffect[0], RippleEffect), "???"
    #         self.rippleEffects.extend(rEffect)

    def save(self: PersonMonthScoresRaw) -> None:
        """store latest score data for this month"""
        assert self.key is not None and isinstance(
            self.key, ndb.Key
        ), "instance created without key"
        self.lastCalcDtTm = datetime.now()
        self.put()

    def __eq__(self: PersonMonthScoresRaw, other) -> bool:
        # equality check between instances
        if self.key and other.key:
            return self.key == other.key
        return self.yearMonthKeyStr == other.yearMonthKeyStr

    @property
    def yearMonthKeyStr(self: PersonMonthScoresRaw) -> str:
        return BaseNdbModel.keyStrFromDate(self.monthStartDt)

    @property
    def lastRealEntryDt(self: PersonMonthScoresRaw) -> date:
        return max(self.datesOfRealEntries)

    @property
    def datesOfRealEntries(self: PersonMonthScoresRaw) -> list[date]:
        # return only recs based on real user entries, not copy/extrapolations
        # return self.perDayScores
        return [ds.day for ds in self.perDayScores]
        # print("{0} contains {1} ds recs of which {2} are original".format(self.monthStartDt, len(self.perDayScores), len(l)))
        # return l

    @property
    def realScoredDaysCount(self: PersonMonthScoresRaw) -> int:
        return len(self.perDayScores)

    @property
    def lastDateOfMonth(self: PersonMonthScoresRaw) -> date:
        return convertToLastDayOfMonth(self.monthStartDt)

    @property
    def isCurrentMonth(self: PersonMonthScoresRaw) -> bool:
        today = date.today()
        return (
            self.monthStartDt.year == today.year
            and self.monthStartDt.month == today.month
        )

    # def _mostRecentPriorDay(self, missedDay, existingDays):
    #     lowerDays = [d.day for d in existingDays if d.day < missedDay]
    #     lowerDays.append(0)
    #     return max(lowerDays)


def clone_ndb_entity(e, **extra_args):
    klass = e.__class__
    props = dict(
        (v._code_name, v.__get__(e, klass))
        for v in klass._properties.itervalues()
        if type(v) is not ndb.ComputedProperty
    )
    props.update(extra_args)
    return klass(**props)


MapMonthKeyToPersonMonthRawScores = dict[str, PersonMonthScoresRaw]


# from google.cloud.datastore import Client, Entity, Key


# class TsBaseKind(Entity):
#     """ """

#     def __init__(self, key, exclude_from_indexes):
#         super().__init__(key=key, exclude_from_indexes=exclude_from_indexes)

#     def save(self, client: Client):
#         client.put(self)

#     @staticmethod
#     def _makeKey(client: Client, id: str) -> Key:
#         return client.key(__class__.__name__, id)

#     @staticmethod
#     def createNew(client: Client, id: str):
#         ky = TsBaseKind._makeKey(client, id)
#         return __class__.__init__(ky)

#     @staticmethod
#     def loadExisting(client: Client, id: str):
#         ky = TsBaseKind._makeKey(client, id)
#         return client.get(ky)
