from __future__ import annotations

from datetime import date, datetime, timedelta, time
from typing import cast, Union, TypeVar

import google.cloud.ndb as ndb

#
from .baseNdb_model import BaseNdbModel

from ..config.behavior.beh_constants import FEELING_ONLY_CODE_NEG, FEELING_ONLY_CODE_POS
from ..config.behavior.load_yaml import BehaviorSourceSingleton
from ..utils.data_gen import randIntInRange
from .beh_entry import Entry
from .user import DbUser

behaviorDataShared = BehaviorSourceSingleton()  # read only singleton


class PersonBehavior(BaseNdbModel):
    """Behavior entries stored by month:
    AncestorKey:  userID -> personID -> monthStartDt
    using Entry occur date
    """

    monthStartDt = ndb.DateProperty(indexed=True)
    personID = ndb.IntegerProperty(required=True, default=0)
    entries = ndb.StructuredProperty(Entry, repeated=True)
    scoredUpTo = ndb.DateTimeProperty(indexed=False)
    _latestEntry = None  # actual entry rec;  not just the date
    _earliestEntryDate = None  # the date

    @property
    def entryList(self) -> list[Entry]:
        return cast(list[Entry], self.entries)

    @property
    def unscoredEntries(self: PersonBehavior):
        return [e for e in self.entryList if e.modifyDateTime > self.scoredUpTo]

    @property
    def yearMonthKeyStr(self: PersonBehavior):
        return PersonBehavior.keyStrFromDate(self.monthStartDt)  # type: ignore

    @property
    def earliestEntryDate(self: PersonBehavior):
        # print("there are {0} behavior entries".format( len(self.entries) ))
        # print("date list is:")
        # print( [ e.occurDateTime for e in self.entries] )
        if len(self.entryList) < 1:
            return date.today()
        elif self._earliestEntryDate != None:
            return self._earliestEntryDate

        self._earliestEntryDate = min([e.occurDateTime for e in self.entryList]).date()  # type: ignore
        return self._earliestEntryDate

    @property
    def latestEntryDate(self: PersonBehavior):
        if len(self.entryList) < 1:
            return date.today()
        elif self._latestEntry == None:
            self._latestEntry = self.entryList[0]
        return self._latestEntry.occurDateTime.date()  # type: ignore

    @property
    def earliestEntryDtTm(self: PersonBehavior):
        return datetime.combine(self.earliestEntryDate, time.min) + timedelta(
            milliseconds=1
        )

    @property
    def latestEntryDtTm(self: PersonBehavior):
        return datetime.combine(self.latestEntryDate, time.min) + timedelta(
            milliseconds=1
        )

    def addNewEntry(self: PersonBehavior, entry: Entry):
        """ """
        # cat, subCat = behaviorDataShared.catAndSubForCode(entry.behaviorCode)
        bcn = behaviorDataShared.masterDict.get(entry.behaviorCode)
        assert bcn is not None, "invalid behCode {0}".format(entry.behaviorCode)
        entry.categoryCode = bcn.topCategoryCode
        entry.oppositeCode = bcn.oppositeCode
        entry.modifyDateTime = datetime.now()
        # print("1) BehCount in {0} is {1}".format(self.monthStartDt, len(self.entries)))
        self.entries.insert(0, entry)
        self._latestEntry = entry
        self.put()
        # print("2) BehCount in {0} is {1}".format(self.monthStartDt, len(self.entries)))
        self.clearCache()

    def updateEntry(self: PersonBehavior, secsFromOrigDtTm: int, entry: Entry):
        """use time delta and beh_code to find rec to replace"""
        originalDtTm: datetime = entry.occurDateTime + timedelta(
            seconds=secsFromOrigDtTm
        )
        originalDtTm = originalDtTm.combine(originalDtTm.date(), time=time(0, 0, 0, 0))

        for rowNum, e in enumerate(self.entries):
            if e.occurDateTime == originalDtTm and e.behaviorCode == entry.behaviorCode:
                self.entries[rowNum] = entry
                break
        # modifyDateTime is set in _pre_put_hook
        # if len(self.entryList) < secsFromOrigDtTm + 1:
        #     secsFromOrigDtTm = 0
        # entry.modifyDateTime = datetime.now()

        self.entries[secsFromOrigDtTm] = entry
        self._latestEntry = entry
        self.put()
        self.clearCache()

    def markJustScored(self):
        self.scoredUpTo = datetime.now()
        self.put_async()

    def clearCache(self):
        # nothing currently cached
        return

    def _pre_put_hook(self):
        if self._latestEntry != None:
            self._latestEntry.modifyDateTime = datetime.now(tz=None)

    @staticmethod
    def loadOrInitByCoreIds(user: DbUser, personID: int, occurDate: date):
        # load one PersonBehavior (user/person/month) combo rec from the DB
        if isinstance(occurDate, datetime):
            occurDate = occurDate.date()

        monthStartDt = occurDate.replace(day=1)
        thisMonthKeyRec = PersonBehavior.makeKey(user.id_, personID, monthStartDt)
        res = thisMonthKeyRec.get()
        if not res:
            res = PersonBehavior(
                monthStartDt=monthStartDt, personID=personID, entries=[]
            )
            res.key = thisMonthKeyRec
            res.scoredUpTo = datetime.combine(monthStartDt, time.min) - timedelta(
                days=1
            )
        return res

    @classmethod
    def loadAllFromCoreIds(cls, user: DbUser, personID: int) -> list[PersonBehavior]:
        # return list of PersonBehavior recs for every month since started dating
        ancestorKey = cls.makeAncestor(user.id_, personID)
        # below requires custom datastore index
        qry = cls.query(ancestor=ancestorKey).order(-cls.monthStartDt)
        return qry.fetch()

    # @staticmethod
    # def loadBehaviorsWithDimensions(user: DbUser, personId: int):
    #     """
    #         niu -- missing BehaviorDimensionScores class below
    #     """
    #     # returns raw data 4 behaviors/dimensions
    #     from .behavior import
    #     (
    #         BehaviorDimensionScores,
    #     )  # avoid circular import

    #     allBehavior = PersonBehavior.loadOrInitByCoreIds(user, personId)
    #     # print("found %s entries in behavior dict" % (len(allBehavior.entries)) )
    #     bds = BehaviorDimensionScores(user, personId, allBehavior)
    #     bds.calc()
    #     return bds

    # @staticmethod
    # def keyStrFromDate(dt):
    #     return dt.strftime(MONTH_START_FMT_STR)
    # #
    # @staticmethod
    # def makeKey(userID, personID, dateObj):
    #     assert isinstance(dateObj, date) and dateObj.day == 1, "Err: %s %s" % (dateObj, dateObj.day)
    #     personKey = PersonBehavior.makeAncestor(userID, personID)
    #     monthStartStr = PersonBehavior.keyStrFromDate(dateObj)
    #     return ndb.Key(PersonBehavior, monthStartStr, parent=personKey)

    # @staticmethod
    # def makeAncestor(userID, personID):
    #     userKey = ndb.Key("User", userID)
    #     return ndb.Key("Person", personID, parent=userKey)

    @staticmethod
    def makeFakeEntry(startDate):
        # mock data for testing
        e = Entry()
        e.behaviorCode = MOCK_BEH_CODES[randIntInRange(0, len(MOCK_BEH_CODES) - 1)]
        e.feelingStrength = randIntInRange(0, 4)
        # e.significanceStrength = randIntInRange(0, 4)
        now = date.today()
        daysBetween = (now - startDate).days
        backupDays = randIntInRange(0, daysBetween)
        newDt = now - timedelta(days=backupDays)
        e.occurDateTime = datetime.combine(newDt, datetime.min.time())
        return e


MOCK_BEH_CODES = [
    "avoidComm",
    "personalboundaryCross",
    "shutoutFeelings",
    "waitedReturnmsg",
    "hintsNotnoticed",
    "brokeupSuddenly",
    "InfoWithheld",
    "exaggerateMistake",
    "pastFocusmistakes",
    "contributionsNotowned",
    "blamedNegsitch",
    "ignoredStress",
    "situationTooserious",
    "disagreethreatenleave",
    "disagreeThreatenhurt",
    "mistakeThreatenhurt",
    "newsBadshock",
    "unclearComm",
    "takingTurnspoorly",
    "empathizedPoorly",
    "suggestionNotuseful",
    "conversationLightneg-",
    "messageMixed",
    "undesiredMsgs",
    "talkedAboutself",
    "newsGoodsurprise",
    "overlookedMistake",
    "presentFocusmistakes",
    "contributionsOwned",
    "workedTogethernegsitch",
    "recognizedStress",
    "situationKeptlight",
    "disagreeWorkthrough",
    "disagreeForgiving",
    "mistakeForgiving",
    "gaveSpace",
    "askedpermissionCross",
    "sharedFeelings",
    "promptReturnmsg",
    "hintsNoticed",
    "infoSharetact",
    "clearComm",
    "takingTurnswell",
    "empathizedWell",
    "suggestionUseful",
    "conversationLightpos",
    "messageConsistent",
    "askedAboutme",
    "desiredMsgs",
    "cleanOrganized",
    "heightRight",
    "weightRight",
    "breathFresh",
    "teethStraight",
    "bodySmellgood",
    "warmConnected",
    "acceptedExlcusiveoffer",
    "initiatedDiscussexclusive",
]
