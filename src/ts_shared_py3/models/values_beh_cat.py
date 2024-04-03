from __future__ import annotations, division
from typing import Optional
from datetime import date, timedelta  # , datetime
import google.cloud.ndb as ndb

#
from ..api_data_classes.values import (
    ValueRateMsg,
    ValuesCollectionMsg,
    ValueOrStatsReqMsg,
)

# from common.utils.date_conv import message_to_date


""" USING PYTHON 3 division!!!!!
Tracks user input from the Assess-Values part of the app!
Goals for this module -- need to be able to determine:
    unanswered global questions
    whether frequency has been set for a particular prospect
    questions allowed per day
    which prospects have not had frequency set for existing global/concern answers
"""

# persisted to disk


class ProspectSummary(ndb.Model):
    """nested rec inside of BehSummary"""

    personID = ndb.IntegerProperty(default=0)
    freqVote = ndb.IntegerProperty(
        default=-1
    )  # slider slot selected by user (1-4) 4 vals
    # date when user changes prospect frequency vote
    changeDt = ndb.DateProperty(
        required=True
    )  # when user last updated it; need to set explicitly for testing; dont auto-set


class BehSummary(ndb.Model):
    """nested rec inside of UserValsByBehCat"""

    behCode = ndb.StringProperty(default="", required=True)
    concernVote = ndb.IntegerProperty(default=-1)  # gen/global answer (1-4) 4 vals
    perProspect = ndb.LocalStructuredProperty(ProspectSummary, repeated=True)
    # date when user changes their concern level
    changeDt = ndb.DateProperty(required=True, auto_now=True)

    def _updateVals(self: BehSummary, valRateMsg: ValueRateMsg):
        """
        Args:
            svap: SaveValueAssessPayload
        """
        assert 1 <= valRateMsg.concernVote <= 4, "concern vote {0} out of range".format(
            valRateMsg.concernVote
        )
        changeDt: date = valRateMsg.changeDt
        if changeDt == None:
            changeDt = date.today()
        if valRateMsg.concernVote != self.concernVote:
            self.changeDt = changeDt
        else:
            self.changeDt = date.today()

        self.concernVote = valRateMsg.concernVote
        for persFreqMsg in valRateMsg.frequencies:
            idx = self._findOrAppendIdxForPerson(persFreqMsg.personID)
            self.perProspect[idx].freqVote = persFreqMsg.frequency
            # setting changeDt EXPLICITLY for testability; do not auto-set
            self.perProspect[idx].changeDt = changeDt

    def _findOrAppendIdxForPerson(self: BehSummary, personID: int) -> int:
        """add ProspectSummary if not found"""
        personID = int(personID)
        for i, ps in enumerate(self.perProspect):
            if ps.personID == personID:
                return i
        # not found so add it
        self.perProspect.append(ProspectSummary(personID=personID, freqVote=-1))
        return len(self.perProspect) - 1

    def _removeProspectEntries(self, persID: int):
        self.perProspect = [pp for pp in self.perProspect if pp.personID != persID]

    @staticmethod
    def _newRecFor(behCode: str) -> BehSummary:
        bs = BehSummary(behCode=behCode, concernVote=-1, perProspect=[])
        return bs


class UserValsByBehCat(ndb.Model):
    """User assessment values by behavior category
    these recs summarize all of a users prior answers in the Values Assessment part of the app
    the BehSummary.perProspect section will grow and change over time as Prospects come & go

    1 rec per user & category of behavior
    ancestor key is userID
    key is category
    """

    category = ndb.StringProperty(indexed=True)
    lastBehCode = ndb.StringProperty(indexed=True, default="")
    allBehaviors = ndb.LocalStructuredProperty(BehSummary, repeated=True)

    @property
    def userID(self: UserValsByBehCat) -> str:
        if self.key is None:
            return ""
        else:
            return self.key.parent().string_id()

    @property
    def userCountStats(self: UserValsByBehCat) -> UserAnswerStats:
        """user global stats/counts values
        keep a copy of UserAnswerStats (persisted separately/globally)
        to govern whether user can get another question or not
        loaded on-demand in each vals-client & cached in dict above
        """
        return UserAnswerStats._loadOrCreate(self.userID)

    @property
    def newestChangeDt(self: UserValsByBehCat) -> date:
        return max(self.changeDates)

    @property
    def changeDates(self: UserValsByBehCat) -> list[date]:
        return [x.changeDt for x in self.allBehaviors]

    def __str__(self: UserValsByBehCat) -> str:
        return "lastCd:{0} ansForCount:{1} userCountSum:{2}".format(
            self.lastBehCode, len(self.allBehaviors), str(self.userCountStats)
        )

    def updateUserAnswer(self: UserValsByBehCat, valRateMsg: ValueRateMsg):
        # valRateMsg is instance of ValuesClient()
        # update nested struc from ValueRateMsg
        if len(valRateMsg.frequencies) > 0:
            assert 1 <= valRateMsg.frequencies[0].frequency <= 4, "vote out of range"
        self._appendOrUpdateVoteVals(valRateMsg)
        # update top level vals
        self.lastBehCode = valRateMsg.behCode
        # store to disk
        self._save()  # will also save (separately) the user-global UserAnswerStats rec

    def questionsAllowedToday(self: UserValsByBehCat, perDayAllowance: int) -> int:
        """
        nxtQuestReqPayload: NextQuestRequestPayload
        return int
        """
        return self.userCountStats.remainingQuestionsAvail(perDayAllowance)

    def maybePriorAnsForBehCode(
        self: UserValsByBehCat, behCode: str
    ) -> Optional[BehSummary]:
        """find prior answer if exists"""
        for bs in self.allBehaviors:
            if bs.behCode == behCode:
                return bs
        return None

    def _appendOrUpdateVoteVals(
        self: UserValsByBehCat, valRateMsg: ValueRateMsg
    ) -> None:
        """update both self & UserAnswerStats from SaveValueAssessPayload
        valRateMsg is instance of ValuesClient()
        """
        isRevisionToExistingAnswer = valRateMsg.origConcernVote > 0  # not == -1
        persIDs = [f.personID for f in valRateMsg.frequencies]
        self.userCountStats._bumpCountAndDateFor(
            valRateMsg.categoryCode,
            valRateMsg.behCode,
            persIDs,
            valRateMsg.decrementQuota,
            isRevisionToExistingAnswer,
        )
        idx = self._findOrAppendIdxForBehCode(valRateMsg.behCode)
        self.allBehaviors[idx]._updateVals(valRateMsg)

    def _findOrAppendIdxForBehCode(self: UserValsByBehCat, behCode: str) -> int:
        """which row contains rec summary for behCode
        FIXME: make this a generator to be faster
        """
        for i, bs in enumerate(self.allBehaviors):
            if bs.behCode == behCode:
                return i
        # not found so add it
        self.allBehaviors.append(BehSummary._newRecFor(behCode))
        return len(self.allBehaviors) - 1

    def _save(self: UserValsByBehCat) -> None:
        self.userCountStats.save()  # separate-table; not persisted on this instance
        self.put()

    @staticmethod
    def loadAllPriorForUser(userID: str) -> list[UserValsByBehCat]:
        """returns list of all UserValsByBehCat (across categories) prior answers
        for provided userID
        """
        key = ndb.Key("DbUser", userID, parent=None)
        qury = UserValsByBehCat.query(ancestor=key)
        mergedlist: list[UserValsByBehCat] = []
        for rec in qury.fetch():
            mergedlist.append(rec)
        return mergedlist

    @staticmethod
    def loadOrCreate(userID: str, category: str) -> UserValsByBehCat:
        # global userCountCache
        key = UserValsByBehCat._makeKey(userID, category)  # UserValsByBehCat
        rec = key.get()
        if rec is None:
            rec = UserValsByBehCat._emptyNewRec(userID, category)
            rec.key = key  # so rec can be saved

        # user stats singleton is loaded on demand (as a property)
        # to track dates/counts
        # & provide logic for whether user can answer more ??'s today
        # this property is NOT SAVED as part of self record; stored in own table
        return rec

    @staticmethod
    def loadAllByUser(userID: str) -> list[UserValsByBehCat]:
        userKey = ndb.Key("DbUser", userID, parent=None)
        q = UserValsByBehCat.query(ancestor=userKey)
        return q.fetch(500)

    @staticmethod
    def deleteAllByUser(userID: str, persID: int = 0) -> None:
        # can delete all prior entries or just by personID
        allRecs = UserValsByBehCat.loadAllByUser(userID)
        if persID == 0:
            # deleting data for all prospects
            kys = [r.key for r in allRecs]
            ndb.delete_multi(kys)
            # UserAnswerStats.deleteAllForUser(persID)
            return

        # clearing counts for one prospect
        for rec in allRecs:
            for pe in rec.allBehaviors:
                pe._removeProspectEntries(persID)
            rec._save()

        UserAnswerStats.zeroAllCatAnswerCounts(userID)

    @staticmethod
    def _emptyNewRec(userID: str, category: str) -> UserValsByBehCat:
        uvbc = UserValsByBehCat(category=category)
        uvbc.key = UserValsByBehCat._makeKey(userID=userID, behCategory=category)
        uvbc.allBehaviors = []
        return uvbc

    @staticmethod
    def _makeKey(userID: str, behCategory: str) -> ndb.Key:
        """nest user answers under userID -> behCategory"""
        userKey = ndb.Key("DbUser", userID, parent=None)
        return ndb.Key(UserValsByBehCat, behCategory, parent=userKey)


# global user stats across all behavior categories


class PerProspectBehCodes(ndb.Model):
    # remember behCodes answered for each prospect
    personID = ndb.IntegerProperty(indexed=False, default=0)
    behCodesAnswered = ndb.TextProperty(indexed=False, repeated=True)


class CategoryCount(ndb.Model):
    """tracks TOTAL per category counts & today answer count
    on a per user basis
    """

    category = ndb.TextProperty(indexed=False, default="communicationNeg")  # code
    answerCount = ndb.IntegerProperty(indexed=False, default=0)
    lastAnswerDt = ndb.DateProperty()  # date of last answer; NOT auto-updated
    perProspectAnsCodes = ndb.LocalStructuredProperty(
        PerProspectBehCodes, repeated=True
    )

    def __str__(self) -> str:
        return "catCd:{0} answCnt:{1:d} lastDt:{2}, personRows:{3}".format(
            self.category,
            self.answerCount,
            self.lastAnswerDt,
            len(self.perProspectAnsCodes),
        )

    def updateFromNewAnswer(
        self, behCode: str, personIDs: list[int], isEditDontBump: bool = False
    ) -> None:
        """remember last day of answers plus
        all behCodes answered for each prospect
        """
        if not isEditDontBump:
            self.answerCount += 1
        self.lastAnswerDt = date.today()

        for persID in personIDs:
            foundPers = False
            for ppbc in self.perProspectAnsCodes:
                if ppbc.personID != persID:
                    continue
                foundPers = True
                lst = (
                    ppbc.behCodesAnswered
                )  # if len(ppbc.behCodesAnswered) > 0 else []  # empty list if None
                # print("abcdefg")
                # print(behCode)
                # print(lst)
                lst.append(behCode)
                # print(lst)
                # print(set(lst.append(behCode)))
                lst = list(set(lst))  # dedup after edits
                ppbc.behCodesAnswered = lst
                break
            if not foundPers:
                ppbc = PerProspectBehCodes(personID=persID, behCodesAnswered=[behCode])
                self.perProspectAnsCodes.append(ppbc)

    @staticmethod
    def newEmpty(category: str) -> CategoryCount:
        return CategoryCount(
            category=category, answerCount=0, lastAnswerDt=date(2019, 1, 1)
        )

    @staticmethod
    def dummyRec() -> CategoryCount:
        return CategoryCount.newEmpty("communication")


class UserAnswerStats(ndb.Model):
    """keeps per category stats by user
    faster & easier than loading all the distinct cat recs above
    allCategoryCounts also keeps specific answered behCodes per prospect
    """

    lastAnswerDt = ndb.DateProperty(
        auto_now=True
    )  # date of last answer; updated on save
    answerCountLastDt = ndb.IntegerProperty(default=0)  # of answers on last date
    # allCategoryCounts also keeps specific behCodes per prospect
    allCategoryCounts = ndb.LocalStructuredProperty(CategoryCount, repeated=True)

    def __str__(self) -> str:
        return "lastDt:{0} numCats:{1:d}".format(
            self.lastAnswerDt, len(self.allCategoryCounts)
        )

    def remainingQuestionsAvail(self, allowedCount: int) -> int:
        # return # of questions still avail today
        if self.lastAnswerDt < date.today():
            return allowedCount
        else:
            return allowedCount - self.answerCountLatest

    def _bumpCountAndDateFor(
        self,
        category: str,
        behCode: str,
        personIDs: list[int],
        decrementQuota: bool = False,
        isEditDontBump: bool = False,
    ) -> None:
        idx = self._findOrAppendIdxFor(category)
        self.allCategoryCounts[idx].updateFromNewAnswer(
            behCode, personIDs, isEditDontBump
        )

        if not decrementQuota:
            # dont limit user edits to OLD answers
            return

        if self.lastAnswerDt < date.today():
            self.answerCountLastDt = 0 if isEditDontBump else 1
            self.lastAnswerDt = date.today()
        elif not isEditDontBump:
            self.answerCountLastDt += 1

    def _findOrAppendIdxFor(self, category: str) -> int:
        for i, cc in enumerate(self.allCategoryCounts):
            if cc.category == category:
                return i
        # not found so add it
        self.allCategoryCounts.append(CategoryCount.newEmpty(category))
        return len(self.allCategoryCounts) - 1

    def save(self) -> None:
        self.put()

    @property
    def answerCountsByCatCode(self) -> map[str, int]:
        # return dict of answered cat codes with # answered
        return {cc.category: cc.answerCount for cc in self.allCategoryCounts}

    @property
    def answerCountLatest(self) -> date:
        return self.answerCountLastDt

    @property
    def mostRecentAnsweredCategory(self) -> CategoryCount:
        # always returns a rec
        if len(self.allCategoryCounts) < 1:
            return CategoryCount.dummyRec()

        latestCatCountRec = max(self.allCategoryCounts, key=lambda cc: cc.lastAnswerDt)
        return latestCatCountRec

    @staticmethod
    def zeroAllCatAnswerCounts(userID: str) -> None:
        # dont want to zero answer counts;  pg 20/10/2
        # except in test mode
        # only run via the debug "replaceAllData" feature
        uas = UserAnswerStats._loadOrCreate(userID)

        uas.answerCountLastDt = 0
        for cc in uas.allCategoryCounts:
            cc.answerCount = 0
        uas.save()
        # TODO: use memcache for cache of stats

    @staticmethod
    def getUserIdsForNoRecentAnswers() -> list[str]:
        # returns user Keys for all users who've not answered values in last x days
        yesterday = date.today() - timedelta(days=6)
        qry = UserAnswerStats.query(UserAnswerStats.lastAnswerDt <= yesterday)
        results: list[ndb.Key] = qry.fetch(12000, keys_only=True, offset=0)
        return [key.string_id() for key in results]

    @staticmethod
    def _loadOrCreate(userID: str) -> UserAnswerStats:
        userKey = UserAnswerStats._makeKeyFrom(userID)
        rec = userKey.get()
        if rec is None:
            rec = UserAnswerStats._emptyNewRec(userID)
        return rec

    @staticmethod
    def _emptyNewRec(userID: str) -> UserAnswerStats:
        uas = UserAnswerStats(
            lastAnswerDt=date.today(), answerCountLastDt=0, allCategoryCounts=[]
        )
        uas.key = UserAnswerStats._makeKeyFrom(userID)
        return uas

    @staticmethod
    def _makeKeyFrom(userID: str) -> ndb.Key:
        return ndb.Key(UserAnswerStats, userID, parent=None)
