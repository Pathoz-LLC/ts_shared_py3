from datetime import date, datetime, timedelta, time

import google.cloud.ndb as ndb

#
from common.config.behavior.beh_constants import (
    FEELING_ONLY_CODE_NEG,
    FEELING_ONLY_CODE_POS,
)
from baseNdb_model import BaseNdbModel
from common.config.behavior.load_yaml import BehaviorSourceSingleton

from random import randint  # for mock data

behaviorDataShared = BehaviorSourceSingleton()  # read only singleton


def randIntInRange(st: int, en: int):
    return randint(st, en)


class Entry(BaseNdbModel):  # ndb.model.Expando
    """
    each behavior log entry looks like this
        stored as a sub-property of PersonBehavior table
        on per-month based on self.occurDateTime
    """

    rowNum = ndb.IntegerProperty(indexed=False, default=1)
    behaviorCode = ndb.StringProperty(indexed=True, required=True)
    positive = ndb.BooleanProperty(indexed=False, default=False)
    feelingStrength = ndb.IntegerProperty(
        indexed=False, default=1
    )  # feeling strength re beh (1-3) 3vals

    # GeoField(name='place', value=GeoPoint(latitude=-33.84, longitude=151.26))
    coords = ndb.GeoPtProperty()

    comments = ndb.TextProperty(indexed=False, default="")  # any notes or comments
    shareDetails = ndb.TextProperty(
        indexed=False, default=""
    )  # as str: "F:kadkdfj;T:388844" share IDs from both FB & Twitter
    occurDateTime = ndb.DateTimeProperty(indexed=True)
    addDateTime = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    modifyDateTime = ndb.DateTimeProperty(indexed=False)
    categoryCode = ndb.StringProperty(
        indexed=True, default="communicationPos"
    )  # top category

    # Scoring adjustments
    # @property
    # def normalizedFeeling(self):
    #     assert sc.BEH_MIN_SLIDER_POSITION <= self.feelingStrength <= sc.BEH_MAX_SLIDER_POSITION, "was: %d" % self.feelingStrength
    #     mult = 1.0 if self.positive else -1.0
    #     return float(self.feelingStrength / sc.BEH_MAX_SLIDER_POSITION * mult)

    # End ScoringOld adjustments

    @property
    def isFeelingOnly(self):
        return self.behaviorCode in (FEELING_ONLY_CODE_NEG, FEELING_ONLY_CODE_POS)

    @property
    def longitude(self):
        if self.coords is not None:
            return self.coords.lon
        else:
            return 0

    @property
    def latitude(self):
        if self.coords is not None:
            self.coords.lat
        else:
            return 0

    # def toMsg(self, personId=0, rowNum=-1):
    #     from common.messages.behavior import BehaviorRowMsg

    #     brm = BehaviorRowMsg(
    #         behaviorCode=self.behaviorCode,
    #         feelingStrength=self.feelingStrength,
    #         comments=self.comments,
    #     )
    #     brm.behaviorId = rowNum
    #     brm.positive = self.positive
    #     brm.shareDetails = self.shareDetails
    #     brm.lon = self.longitude
    #     brm.lat = self.latitude
    #     brm.personId = personId
    #     brm.occurDateTime = (
    #         self.occurDateTime - datetime.datetime(1970, 1, 1)
    #     ).total_seconds()
    #     brm.categoryCode = self.categoryCode
    #     return brm


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
    def unscoredEntries(self):
        return [e for e in self.entries if e.modifyDateTime > self.scoredUpTo]

    @property
    def yearMonthKeyStr(self):
        return PersonBehavior.keyStrFromDate(self.monthStartDt)

    @property
    def earliestEntryDate(self):
        # print("there are {0} behavior entries".format( len(self.entries) ))
        # print("date list is:")
        # print( [ e.occurDateTime for e in self.entries] )
        if len(self.entries) < 1:
            return date.today()
        elif self._earliestEntryDate != None:
            return self._earliestEntryDate

        self._earliestEntryDate = min([e.occurDateTime for e in self.entries]).date()
        return self._earliestEntryDate

    @property
    def latestEntryDate(self):
        if len(self.entries) < 1:
            return date.today()
        elif self._latestEntry == None:
            self._latestEntry = self.entries[0]
        return self._latestEntry.occurDateTime.date()

    @property
    def earliestEntryDtTm(self):
        return datetime.combine(self.earliestEntryDate, time.min) + timedelta(
            milliseconds=1
        )

    @property
    def latestEntryDtTm(self):
        return datetime.combine(self.latestEntryDate, time.min) + timedelta(
            milliseconds=1
        )

    def addNewEntry(self, entry):
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

    def updateEntry(self, rowNum, entry):
        """"""
        # for i, e in enumerate(self.entries):
        #     if e.occurDateTime == origOccurDateTime and e.behaviorCode == entry.behaviorCode:
        #         self.entries[rowNum] = entry
        #         break
        # modifyDateTime is set in _pre_put_hook
        if len(self.entries) < rowNum + 1:
            rowNum = 0
        entry.modifyDateTime = datetime.now()
        self.entries[rowNum] = entry
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
    def loadOrInitByCoreIds(user, personID, occurDate):
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
    def loadAllFromCoreIds(cls, user, personID):
        # return list of PersonBehavior recs for every month since started dating
        ancestorKey = cls.makeAncestor(user.id_, personID)
        # below requires custom datastore index
        qry = cls.query(ancestor=ancestorKey).order(-cls.monthStartDt)
        return qry.fetch()

    # @staticmethod
    # def loadBehaviorsWithDimensions(user, personId):
    #     # returns raw data 4 behaviors/dimensions
    #     from common.scoring.models import BehaviorDimensionScores     # avoid circular import
    #     allBehavior = PersonBehavior.loadOrInitByCoreIds(user, personId)
    #     # print("found %s entries in behavior dict" % (len(allBehavior.entries)) )
    #     bds = BehaviorDimensionScores(user, personId, allBehavior)
    #     bds.calc()
    #     return bds

    # @staticmethod
    # def keyStrFromDate(dt):
    #     return dt.strftime(MONTH_START_FMT_STR)
    #
    # @staticmethod
    # def makeKey(userID, personID, dateObj):
    #     assert isinstance(dateObj, date) and dateObj.day == 1, "Err: %s %s" % (dateObj, dateObj.day)
    #     personKey = PersonBehavior.makeAncestor(userID, personID)
    #     monthStartStr = PersonBehavior.keyStrFromDate(dateObj)
    #     return ndb.Key(PersonBehavior, monthStartStr, parent=personKey)
    #
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
        e.significanceStrength = randIntInRange(0, 4)
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

# class DimensionMatrix(object):
#     """
#         converts existing behavior log entries into weights along 4 core dimensions
#     """
#
#     def __init__(self, existinEntries):
#         """
#         Args:
#             existinEntries:  from the PersonBehavior record
#         """
#         self.existinEntries = existinEntries
#
#         self.communication = 0
#         self.trust = 0
#         self.respect = 0
#         self.lifestyle = 0
#
#         self.overallScore = 0
#
#     def calc(self):
#         """ updates model to hold final stats
#         """
#         g_communication, g_trust, g_respect, g_lifestyle = 0, 0, 0, 0
#         for e in self.existinEntries:
#             (communication, trust, respect, lifestyle) = e.dimmensionFactors()
#             g_communication += communication
#             g_trust += trust
#             g_respect += respect
#             g_lifestyle += lifestyle
#
#         self.communication = g_communication
#         self.trust = g_trust
#         self.respect = g_respect
#         self.lifestyle = g_lifestyle
#
#         self.overallScore = 0
