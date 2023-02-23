from __future__ import annotations
import sys
import random
import json
from typing import Union, TypeVar
from datetime import date, datetime, timedelta
import copy
from collections import namedtuple

import google.cloud.ndb as ndb

# FIXME
# from ..async_tasks.stats import StatsTasks

from ..enums.sex import Sex, NdbSexProp
from ..enums.voteType import VoteType, NdbVoteTypeProp
from ..schemas.behavior import BehVoteStatsMsg, VoteTypeMsg, BehStatMsg
from ..schemas.behavior import (
    BehVoteStatAdapter,
    VoteTypeMsgAdapter,
    BehStatMsgAdapter,
)
from ..config.behavior.load_yaml import BehaviorSourceSingleton


behaviorDataShared = BehaviorSourceSingleton()  # read only singleton

PerSexVoteTotals = namedtuple("PerSexVoteTotals", ["female", "male", "unknown"])

"""
purpose of this module is to accumulated global stats
for all behavior record entries (both experience & values-assesment)

    class VoteInfo: used to pass args into BehaviorRollup
    class BehaviorRollup:  the stats container/table for a given behCode
        it consists of 3 sex entries  (each behCode can have UP TO PER_BEHAVIOR_SHARDS recs)
        each which contains 3 VoteTypeRollup (by Vote Type)
    class VoteTypeRollup:  used to track groups of stats by user sex
    class CountTotals:  proto-rpc types cannot have methods so this is a wrapper for BehVoteStatsMsg
    class BehVoteStatsMsg:  what is returned to the client
"""


PER_BEHAVIOR_SHARDS = 20  # dont reduce this # or counts will be missed

GLOBAL_PERCENT_INCREASE = 0.5  # when firebase updates are required


class VoteInfo:
    """
    the object used to summarize specifc end-user votes
        (1 per behavior report;  1 + n(prospects) (frequ) for each values assessment)
    such that they can be passed into BehaviorRollup.updateStats
    for accumulated global stats
    """

    def __init__(
        self, sex, voteType, slot, behCode, categoryCode, subCatCode, isPositive
    ):
        # all info needed to support writing recs to BehaviorRollup
        assert 1 <= slot <= 4, "vote {0} is out of range 1-4".format(slot)
        if isinstance(sex, Sex):
            self.sex = sex.value  # sex of user doing the reporting
            self._sexObj = sex
        elif isinstance(sex, int):
            self.sex = sex
            self._sexObj = Sex(sex)
        elif isinstance(sex, (str, unicode)):
            self._sexObj = Sex(int(sex))
            self.sex = self._sexObj.value
        else:
            assert False, "invalid construction"

        self.voteType = int(voteType.value)  # feeling, concern or frequency
        self._voteTypeObj = voteType
        self.voteSlot = slot  # represents a slider position from 1-4
        self.behCode = behCode
        self.categoryCode = categoryCode
        self.subCatCode = subCatCode
        self.positive = isPositive

    def __str__(self):
        sex = "Fem" if self.sex < 3 else "Male"
        voteType = VoteType(self.voteType)
        return "{3} {6} Vote of {4} by {5} on {0}-{1}".format(
            self.behCode,
            self.subCatCode,
            self.categoryCode,
            "Pos" if self.positive else "Neg",
            self.voteSlot,
            sex,
            voteType.name,
        )


class CountTotals:
    """simply a class wrapper around BehVoteStatsMsg
    used to rollup sum vote count vals from BehaviorRollup
        for return to UI
        returns a BehVoteStatsMsg msg
    """

    def __init__(self: CountTotals, bru: BehaviorRollup):
        """construct obj with one bru
        then use self.append() to add stats from other bru shards
        """
        # assert isinstance(bru, BehaviorRollup), "oops?"
        female = bru.msgFor(Sex.FEMALE)
        male = bru.msgFor(Sex.MALE)
        unknown = bru.msgFor(Sex.UNKNOWN)
        self.msg = BehVoteStatsMsg(
            behaviorCode=bru.code, female=female, male=male, unknown=unknown
        )
        self.msg.categoryName = bru.categoryName

    def __eq__(self: CountTotals, other: CountTotals):
        if isinstance(other, CountTotals):
            if other.msg == self.msg:
                return True
            return False
        return False

    def __ne__(self: CountTotals, other: CountTotals):
        return not self.__eq__(other)

    def append(self: CountTotals, bru: BehaviorRollup):
        # add to dict
        d = bru.msgFor(Sex.FEMALE)
        self.msg.female = CountTotals.merge(self.msg.female, d)
        d = bru.msgFor(Sex.MALE)
        self.msg.male = CountTotals.merge(self.msg.male, d)
        d = bru.msgFor(Sex.UNKNOWN)
        self.msg.unknown = CountTotals.merge(self.msg.unknown, d)

    def _slotsToPct(self: CountTotals, voteRecForSex):
        # min of 1 to avoid divide by zero
        totCount = float(max(voteRecForSex.totCount, 1))
        if totCount == 1.0:
            assert sum(voteRecForSex.slotCounts) < 2, "bad data!! should be 0 or 1"
        else:
            assert sum(voteRecForSex.slotCounts) == int(
                totCount
            ), "bad data {0} != {1}".format(
                sum(voteRecForSex.slotCounts), int(totCount)
            )
        return [int(float(vote) / totCount * 100) for vote in voteRecForSex.slotCounts]

    def convertToPctByType(self: CountTotals, voteType=VoteType.CONCERN):
        voteTypeName = voteType.name.lower()

        femVoteRec = getattr(self.msg.female, voteTypeName)
        malVoteRec = getattr(self.msg.male, voteTypeName)
        unkVoteRec = getattr(self.msg.unknown, voteTypeName)

        # based on type of vote, for each sex
        # convert all vote-counts to percentages
        # of the total votes by users under sex
        femVoteRec.slotCounts = self._slotsToPct(femVoteRec)
        malVoteRec.slotCounts = self._slotsToPct(malVoteRec)
        unkVoteRec.slotCounts = self._slotsToPct(unkVoteRec)

    def convertAllCountsToPct(self):
        # self contains a rec for each sex, and each of those contains
        # a rec for each vote type
        self.convertToPctByType(VoteType.FEELING)
        self.convertToPctByType(VoteType.CONCERN)
        self.convertToPctByType(VoteType.FREQUENCY)

    @staticmethod
    def merge(mainMsg: VoteTypeMsg, newMsg: VoteTypeMsg):
        """
        main func for combining partitioned global stats recs into
        one rec with all counts rolled together
        might be a heavy operation so cache in memcache
        append tots from newMsg onto mainMsg
        """

        newFeel = newMsg.feeling
        newConcern = newMsg.concern
        newFrequ = newMsg.frequency

        # BDM TODO -- see if you can find a more efficient approach to this function
        #             try using python maps to improve these loops
        mainMsg.feeling.totCount += newFeel.totCount
        for i in range(0, len(mainMsg.feeling.slotCounts)):
            mainMsg.feeling.slotCounts[i] += newFeel.slotCounts[i]

        mainMsg.concern.totCount += newConcern.totCount
        for i in range(0, len(mainMsg.concern.slotCounts)):
            mainMsg.concern.slotCounts[i] += newConcern.slotCounts[i]

        mainMsg.frequency.totCount += newFrequ.totCount
        for i in range(0, len(mainMsg.frequency.slotCounts)):
            mainMsg.frequency.slotCounts[i] += newFrequ.slotCounts[i]

        return mainMsg

    # @property
    # def totalConcernVotes(self):
    #     # TODO
    #     compositeCountList = [0]
    #     return sum(compositeCountList)

    @property
    def toDict(self):
        return BehVoteStatAdapter.toDict(self.msg)

    @staticmethod
    def fromDict(dct):
        return BehVoteStatAdapter.fromDict(dct)

    @property
    def toJson(self):
        return json.dumps(self, cls=CountTotalsEncoder)

    @staticmethod
    def fromJson(json_str):
        return json.loads(json_str, cls=CountTotalsDecoder)

    @staticmethod
    def default(behCode):
        # returns an empty totals count rec
        cat, subCat = behaviorDataShared.catAndSubForCode(behCode)
        vi = VoteInfo(
            sex=Sex.FEMALE,
            voteType=VoteType.FEELING,
            slot=1,
            behCode=behCode,
            categoryCode=cat,
            subCatCode=subCat,
            isPositive=False,
        )
        bru = BehaviorRollup._newBehaviorRollup(vi)
        return CountTotals(bru)

    def toMsg(self) -> BehVoteStatsMsg:
        # BehVoteStatsMsg for returning to client
        return self.msg


class CountTotalsEncoder(json.JSONEncoder):
    def default(self, obj: Union[CountTotals, object]):
        if isinstance(obj, CountTotals):
            return obj.toDict
        else:
            super(CountTotals, self).default(obj)


class CountTotalsDecoder(json.JSONDecoder):
    """convert Json str into CountTotalsEvent & return"""

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        # object is a nested BehStatMsg
        if "totCount" in dct:
            return BehStatMsgAdapter.fromDict(dct)
        # object is a nested VoteTypeMsg
        if "feeling" in dct:
            return VoteTypeMsgAdapter.fromDict(dct)
        # error - object is not the embedded BehVoteStat
        if "behaviorCode" not in dct:
            return dct

        # convert BehVotStat from dictionary
        ct = CountTotals.default(dct.get("behaviorCode"))
        ct.msg = BehVoteStatAdapter.fromDict(dct)
        return ct


class VoteTypeRollup(ndb.Model):
    """
    keeps votes for (3 or 4) slider positions
    behaviors only vote 0-2 (1,2,3)
    value assmts vote 0-3 (1,2,3,4)
    voteBreakout == slider position 0-3
    """

    voterSex = NdbSexProp(required=True)
    voteType = NdbVoteTypeProp(required=True)
    count = ndb.IntegerProperty(default=0)
    # list of integers for each slider slot
    s1 = ndb.IntegerProperty(default=0)
    s2 = ndb.IntegerProperty(default=0)
    s3 = ndb.IntegerProperty(default=0)
    s4 = ndb.IntegerProperty(default=0)

    @property
    def derivedCount(self):
        return self.s1 + self.s2 + self.s3 + self.s4

    @property
    def consensusWeight(self):
        """looking for consensus, not avg or mean
        voteType.statsPositionCount holds either 3 or 4
        representing # of positions on respective UI slider
        """
        cWts = self.voteType.consensusWeights
        consensus = (
            (self.s1 * cWts[0])
            + (self.s2 * cWts[1])
            + (self.s3 * cWts[2])
            + (self.s4 * cWts[3])
        )
        return float(consensus) / self.derivedCount

    @property
    def slotsAsList(self):
        return [self.s1, self.s2, self.s3, self.s4]

    def toDict(self):
        """TODO:  check this dict missing sex & type?"""
        return dict(count=self.count, votes=self.slotsAsList)

    @staticmethod
    def newEmpty(sex: Sex, voteType: VoteType):
        """new type rollup"""
        vtr = VoteTypeRollup(
            voterSex=sex, voteType=voteType, count=0, s1=0, s2=0, s3=0, s4=0
        )
        return vtr

    @staticmethod
    def vtrListAllTypes(sex: Sex):
        # used for init empty recs when first encountered
        # returns list but would be safer to convert to named-tuple
        feel = VoteTypeRollup.newEmpty(sex, VoteType.FEELING)
        # hope = VoteTypeRollup.newTR(sex, VoteType.HOPE)
        concern = VoteTypeRollup.newEmpty(sex, VoteType.CONCERN)
        freq = VoteTypeRollup.newEmpty(sex, VoteType.FREQUENCY)
        # order in this array matters
        return [feel, concern, freq]

    def __str__(self):
        return "VTR: {0}-{1} has Tot:{2}  [{3},{4},{5},{6}]".format(
            self.voterSex, self.voteType, self.count, self.s1, self.s2, self.s3, self.s4
        )

    def update(self, slot: int):
        """add to count"""
        # slot = max(1, min(4, slot))
        assert 1 <= slot <= 4, "oops? slot: {0}".format(slot)
        # print("pre-update: slot{0}".format(slot))
        # print(self)
        self.count += 1
        self.s1 = self.s1 + 1 if slot == 1 else self.s1
        self.s2 = self.s2 + 1 if slot == 2 else self.s2
        self.s3 = self.s3 + 1 if slot == 3 else self.s3
        self.s4 = self.s4 + 1 if slot == 4 else self.s4
        # print("post-update")
        # print(self)

    def append(self, otherVtr):
        self.count += otherVtr.count
        self.s1 += otherVtr.s1
        self.s2 += otherVtr.s2
        self.s3 += otherVtr.s3
        self.s4 += otherVtr.s4

    def matchesVoteType(self, voteType: VoteType):
        if isinstance(voteType, VoteType):
            voteType = voteType.value
        assert isinstance(voteType, int), "invalid type"
        return self.voteType.value == voteType  # or self.voteType == voteType.value


class BehaviorRollup(ndb.Model):
    """main shard/partition entity for tracking stats per behavior-code
    key == _makeBehStatsShardKey
    also make composite key on:  category:subCategory
    multiple recs for each behavior to handle sharding write thruput

    stored fields are codes (not name/text)
    """

    category = ndb.StringProperty(indexed=True, required=True)
    subCategory = ndb.StringProperty(indexed=True, required=True)
    code = ndb.StringProperty(indexed=True, required=True)
    positive = ndb.BooleanProperty(indexed=False, default=False)

    # each sex contains a list of 3 VoteTypeRollup recs (one for each VoteType)
    # note JsonProperty encoded differently between Python 2 & 3
    femaleCounts = ndb.LocalStructuredProperty(VoteTypeRollup, repeated=True)
    maleCounts = ndb.LocalStructuredProperty(VoteTypeRollup, repeated=True)
    unknownCounts = ndb.LocalStructuredProperty(VoteTypeRollup, repeated=True)

    def _update(self: BehaviorRollup, voteInfo: VoteInfo):
        """
        take latest vote info & apply it to the right user-sex & stat-type
        """
        vtrListForThisSex: list[VoteTypeRollup] = self._statsListBySex(voteInfo.sex)
        # print("vtrListForThisSex: {0}".format(len(vtrListForThisSex)))
        # print(vtrListForThisSex)

        foundVtr = False

        for vtr in vtrListForThisSex:  # loop x recs considering both VoteType & INT
            if vtr.matchesVoteType(voteInfo.voteType):
                vtr.update(voteInfo.voteSlot)
                # TODO: BDM update stats (by category & hour) in memcache
                # lets discuss ... is this still needed??
                # add cron to flush to Firebase every 5 minutes
                # add cron to rest window counts on each hour
                # key looks like: catCode-hour
                # value is int (use increment in memcache)
                foundVtr = True
                break
        if not foundVtr:
            # print("$$$$ could not find {0}-{1} to set {2}".format(voteInfo.sex, vtr.voteType, voteInfo.voteSlot))
            assert False, "bryan--your types are wrong in your tests"
            return

        # to verify real-rec (not a copy) was updated
        # print("2)", self.femaleCounts[1])
        # print("3)", self.maleCounts[2])

        # print("3)", perSexList[1])
        #
        # python copies lists on return so confirm correct memory address is updated
        # if voteInfo.sex == Sex.FEMALE:
        #     self.femaleCounts = perSexList
        # elif voteInfo.sex == Sex.MALE:
        #     self.maleCounts = perSexList
        # else:
        #     self.unknownCounts = perSexList

    def save(self: BehaviorRollup):
        # store to ndb
        self.put()

    def _statsListBySex(self: BehaviorRollup, sex: Sex) -> list[VoteTypeRollup]:
        # handles receiving Sex obj or int
        # returns copy of list but objects inside list should have only 1 identity
        if isinstance(sex, int):
            sex = Sex(sex)
        assert isinstance(sex, Sex), "{0} is unexpected arg type".format(type(sex))
        if sex == Sex.NEVERSET:
            sex = Sex.UNKNOWN

        sexName = sex.name.lower() + "Counts"
        return getattr(self, sexName, None)  #  default= []

    @staticmethod
    def loadAllStats(voteType: VoteType, pos: bool = False):
        """
        roll up all stats (across all behaviors) by vote type
        combine all totals (across many shards) into one VoteTypeRollup (ignoring its sex)
        and store in dict keyed by behCode
        return:
            aggregateCounts is a {negBehCode: VoteTypeRollup}
        """
        if voteType == VoteType.CONCERN and pos:
            # only negative behaviors have "concern" votes
            return dict()

        allBehCodes = behaviorDataShared.allBehaviorCodes(pos)
        allStatRecKeys = []
        for behCode in allBehCodes:
            allStatRecKeys.extend(BehaviorRollup.all_keys(behCode))

        # if there are 200 negative behaviors; and 10 shards for each, this list could be 2000 long
        allRecsPlusNoneIfRecNotExists = ndb.get_multi(allStatRecKeys)
        # get_multi returns None at keyIndex for recs that dont exist
        allRecs = [r for r in allRecsPlusNoneIfRecNotExists if r is not None]

        aggregateCounts = dict()  # ref obj updated inside of _unifyStats
        for bru in allRecs:
            bru._unifyStats(voteType, aggregateCounts)
        return aggregateCounts

    @staticmethod
    def updateStats(listVoteInfo: list[VoteInfo]):
        """public api to store updated stats
        several votes can come from one endpoint so arg is a list
        but all most pertain to same behCode for sharding purposes
        """
        assert len(listVoteInfo) > 0, "invalid args"
        firstVoteInfo = listVoteInfo[0]
        assert len(listVoteInfo) == 1 or (
            firstVoteInfo.behCode == listVoteInfo[1].behCode
        ), "all must be for same behCode"
        rec = BehaviorRollup._loadOrCreateRec(firstVoteInfo)
        for vi in listVoteInfo:
            rec._update(vi)

        # call to increment rolling stats window memcache count here
        # for total in Firebase
        RollingStatWindowManager.updateRollingStatCount(firstVoteInfo)

        # save
        # print(rec.maleCounts, rec.femaleCounts)
        rec.save()

    @staticmethod
    def _loadOrCreateRec(voteInfo: VoteInfo):
        """pick one shard rec to distribute concurrent write load
        either load or create it
        do not update stats here
        that is done by caller in the _update method
        """
        shardID = random.randint(0, PER_BEHAVIOR_SHARDS - 1)
        key = _makeBehStatsShardKey(voteInfo.behCode, shardID)
        rec = key.get()
        if rec is None:
            rec = BehaviorRollup._newBehaviorRollup(voteInfo)
            rec.key = key
        return rec

    @staticmethod
    def _newBehaviorRollup(voteInfo: VoteInfo):
        """create new empty rec; only for internal use"""
        new = BehaviorRollup()
        new.category = voteInfo.categoryCode
        new.subCategory = voteInfo.subCatCode
        new.code = voteInfo.behCode
        new.positive = voteInfo.positive
        # list of stat voteType (s) for each sex
        new.femaleCounts = VoteTypeRollup.vtrListAllTypes(Sex.FEMALE)
        new.maleCounts = VoteTypeRollup.vtrListAllTypes(Sex.MALE)
        new.unknownCounts = VoteTypeRollup.vtrListAllTypes(Sex.UNKNOWN)
        return new

    def _unifyStats(self: BehaviorRollup, voteType: VoteType, aggDict):
        """roll stats into one VoteTypeRollup rec
        sex is irrelevant in this case

        aggDict is ref obj which keeps getting updated
        across many shards
        """
        totalsVtr = aggDict.setdefault(
            self.code, VoteTypeRollup.newEmpty(Sex.UNKNOWN, voteType)
        )
        # combine all 3 lists of VTR recs from self
        allStoredVtr = self.femaleCounts + self.maleCounts + self.unknownCounts
        for vtr in allStoredVtr:
            if vtr.voteType == voteType:
                totalsVtr.append(vtr)

    def msgFor(self: BehaviorRollup, sex: Sex):
        """return a VoteTypeMsg"""
        if Sex.FEMALE == sex:
            theLst = self.femaleCounts
        elif Sex.MALE == sex:
            theLst = self.maleCounts
        elif Sex.UNKNOWN == sex:
            theLst = self.unknownCounts
        else:
            sys.exit("invalid sex")

        # FIXME: hard coding position of vote-type in this list is very risky
        # but asserts below confirm it's not failing here for now
        vtrFeel = theLst[0]
        # assert vtrFeel.matchesVoteType(VoteType.FEELING), "Feel-lost list order somewhere: {0}".format(vtrFeel.voteType)
        vtrConcern = theLst[1]
        vtrFrequ = theLst[2]
        # assert vtrFrequ.matchesVoteType(VoteType.FREQUENCY), "Freq-lost list order somewhere: {0}".format(vtrFrequ.voteType)

        feeling = BehStatMsg(totCount=vtrFeel.count, slotCounts=vtrFeel.slotsAsList)
        concern = BehStatMsg(
            totCount=vtrConcern.count, slotCounts=vtrConcern.slotsAsList
        )
        frequency = BehStatMsg(totCount=vtrFrequ.count, slotCounts=vtrFrequ.slotsAsList)
        return VoteTypeMsg(feeling=feeling, concern=concern, frequency=frequency)

    @staticmethod
    def getStatsForBehavior(behCode: str) -> BehVoteStatsMsg:
        """API to Retrieve the value for a given sharded counter.
        Args:
            behCode: behavior code name of the counter.
        Returns:
            CountTotals as proto rpc msg
            cached for an hour at time after launch
        """
        jsn = None  # memcache.get(behCode)
        if jsn is not None:
            return CountTotals.fromJson(jsn).toMsg()

        # time to rebuild & cache our stats
        all_keys = BehaviorRollup.all_keys(behCode)
        activeShards = [bru for bru in ndb.get_multi(all_keys) if bru is not None]
        if len(activeShards) < 1:
            print("Err: no global stats data found for behavior " + behCode)
            return CountTotals.default(behCode).toMsg()

        totalRec = CountTotals(activeShards[0])  # init from first
        for bru in activeShards[1:]:
            totalRec.append(bru)

        totalRec.convertAllCountsToPct()
        jsn = totalRec.toJson
        ttl = 3600 if date.today() > date(2020, 3, 2) else 4
        # memcache.add(behCode, jsn, time=ttl)  # ttl
        return totalRec.toMsg()

    @staticmethod
    def all_keys(behCode: str):
        """Returns all possible keys for the counter name given the config.
        Args:
            name: The name of the counter.
        Returns:
            The full list of ndb.Key values corresponding to all the possible
                counter shards that could exist.
        """
        return [
            _makeBehStatsShardKey(behCode, index)
            for index in range(PER_BEHAVIOR_SHARDS)
        ]

    @property
    def categoryName(self: BehaviorRollup):
        catRec = behaviorDataShared.masterDict.get(self.category)
        if catRec is not None:
            return catRec.text
        else:
            return self.category

    # properties added for rollup by percentages
    @property
    def concernCountsBySex(self: BehaviorRollup):
        femCount = sum(
            [vtr.count for vtr in self.femaleCounts if vtr.voteType == VoteType.CONCERN]
        )
        maleCount = sum(
            [vtr.count for vtr in self.maleCounts if vtr.voteType == VoteType.CONCERN]
        )
        unkCount = sum(
            [
                vtr.count
                for vtr in self.unknownCounts
                if vtr.voteType == VoteType.CONCERN
            ]
        )
        # return (femCount, maleCount, unkCount)
        return PerSexVoteTotals(female=femCount, male=maleCount, unknown=unkCount)

    @property
    def frequencyCountsBySex(self: BehaviorRollup):
        femCount = sum(
            [
                vtr.count
                for vtr in self.femaleCounts
                if vtr.voteType == VoteType.FREQUENCY
            ]
        )
        maleCount = sum(
            [vtr.count for vtr in self.maleCounts if vtr.voteType == VoteType.FREQUENCY]
        )
        unkCount = sum(
            [
                vtr.count
                for vtr in self.unknownCounts
                if vtr.voteType == VoteType.FREQUENCY
            ]
        )
        # return (femCount, maleCount, unkCount)
        return PerSexVoteTotals(female=femCount, male=maleCount, unknown=unkCount)

    @property
    def feelingCountsBySex(self: BehaviorRollup):
        femCount = sum(
            [vtr.count for vtr in self.femaleCounts if vtr.voteType == VoteType.FEELING]
        )
        maleCount = sum(
            [vtr.count for vtr in self.maleCounts if vtr.voteType == VoteType.FEELING]
        )
        unkCount = sum(
            [
                vtr.count
                for vtr in self.unknownCounts
                if vtr.voteType == VoteType.FEELING
            ]
        )
        # return (femCount, maleCount, unkCount)
        return PerSexVoteTotals(female=femCount, male=maleCount, unknown=unkCount)


def _makeBehStatsShardKey(code: str, instanceID: int):
    # assert instanceID > 0, "invalid ID"
    strID = "{0}_{1:d}".format(code, instanceID)
    return ndb.Key(BehaviorRollup, strID)


class RollingStatWindow:
    """
    {
        GlobalCount int,
        LastUpdateTime[<windowIndex>] datetime,
        PositiveTotals["<category>"][<windowIndex>] int
        NegativeTotals["<category>"][<windowIndex>] int
    }

    __init__():         initializes blank stat window data
    loadFromMemcache(): loads rolling stat window data from memcache
    saveToMemcache():   saves rolling stat window data to memcache
    updateFirebase():   convert to firebase format and sync with firebase

    # TODO: move the following to the json encoder pattern, but for now...
    toJson():
    fromJson():
    """

    def __init__(
        self: RollingStatWindow,
        globalCount: int = 0,
        lastUpdateTime=[],
        positiveTotals={},
        negativeTotals={},
    ):
        # initialize basic structure
        self.GlobalCount = globalCount
        self.LastUpdateTime = lastUpdateTime
        self.PositiveTotals = positiveTotals
        self.NegativeTotals = negativeTotals

        if self.LastUpdateTime == []:
            # print("INIT TIMES")
            for _ in range(24):
                self.LastUpdateTime.append(datetime.min)

        # get POSITIVE codes
        if self.PositiveTotals == {}:
            # set zero counts for all categories
            for cat in behaviorDataShared.categoryCodesWithNames(False):
                self.PositiveTotals[cat[0]] = {
                    "catName": cat[1],
                    "iconName": cat[2],
                    "isPositive": cat[3],
                    "subTot": [],
                }
                for _ in range(24):
                    self.PositiveTotals[cat[0]]["subTot"].append(0)

        # get NEGATIVE codes
        if self.NegativeTotals == {}:
            # set zero counts for all categories
            for cat in behaviorDataShared.categoryCodesWithNames():
                self.NegativeTotals[cat[0]] = {
                    "catName": cat[1],
                    "iconName": cat[2],
                    "isPositive": cat[3],
                    "subTot": [],
                }
                for _ in range(24):
                    self.NegativeTotals[cat[0]]["subTot"].append(0)

    def copy(self: RollingStatWindow):
        return RollingStatWindow(
            self.GlobalCount,
            copy.deepcopy(self.LastUpdateTime),
            copy.deepcopy(self.PositiveTotals),
            copy.deepcopy(self.NegativeTotals),
        )

    # calculate the total sum of a list of category window
    # return a list of dicts containing catName, iconName, isPositive,
    # and the actual summed count
    def _sumWindowedTotals(self: RollingStatWindow, isPositive: bool):
        summedStatsList = []

        # BDM TODO: factor out - this is used in multiple places
        # determine ignored categories based on pos/neg list
        if isPositive:
            totalsList = self.PositiveTotals
            ignoreCat = "ShowAll_Pos"
        else:
            totalsList = self.NegativeTotals
            ignoreCat = "ShowAll_Neg"

        for cat in totalsList:
            total = 0

            # ignore specified categories
            if cat == ignoreCat:
                continue

            # sum each window subtotal into actual vote count
            for subTot in totalsList[cat]["subTot"]:
                total = total + subTot

            summedStatsList.append(
                {
                    "catName": totalsList[cat]["catName"],
                    "iconName": totalsList[cat]["iconName"],
                    "isPos": totalsList[cat]["isPositive"],
                    "actCount": total,
                }
            )

        return summedStatsList

    def loadFromMemcache(self: RollingStatWindow):
        # read memcache! (stored as json)
        data = None  # memcache.get(key="RollingStatsWindow")

        # set internal window to memcache window
        if data is not None:
            # DEBUGGING
            # print("rolling stats window - memcache hit!")
            # print(data)

            stats = RollingStatWindow.fromJson(data)
            self.GlobalCount = stats.GlobalCount
            self.LastUpdateTime = stats.LastUpdateTime
            self.PositiveTotals = stats.PositiveTotals
            self.NegativeTotals = stats.NegativeTotals
            return

        # DEBUGGING
        # print("rolling stats window - memcache miss!")

    def saveToMemcache(self: RollingStatWindow):
        data = RollingStatWindow.toJson(self)
        # print("saving %s to memecache!" % data)

        # calculate memcache expiration
        expiration = datetime.utcnow() + timedelta(days=1)
        epoch = datetime.utcfromtimestamp(0)
        expiration_secs = (expiration - epoch).total_seconds()

        # store in memcache
        # memcache.set(key="RollingStatsWindow", value=data, time=expiration_secs)
        return

    def percentIncreased(self: RollingStatWindow, rate: float, oldStats):
        # DEBUGGING
        # print("rate = %d oldStats = %s" %(rate, oldStats))

        # avoid divide by zero
        if oldStats.GlobalCount == 0:
            # if global count is zero and this function is called,
            # it means the count is increasing to at least 1,
            # infinite/undefined increase is worth updating firebase :)
            return True

        # calculate percentage increase
        percentageIncreased = (self.GlobalCount - oldStats.GlobalCount) / float(
            oldStats.GlobalCount
        )

        # DEBUGGING
        # print("rate = %f" % percentageIncreased)

        # return true if greater than threshold rate of increase!
        if percentageIncreased > rate:
            return True

        return False

    def isReordered(self: RollingStatWindow, oldStats):
        # get summed total lists
        PosList_prev = oldStats._sumWindowedTotals(True)
        PosList = self._sumWindowedTotals(True)
        NegList_prev = oldStats._sumWindowedTotals(False)
        NegList = self._sumWindowedTotals(False)

        # sort the lists
        PosList_prev.sort(reverse=True, key=lambda cat: cat["actCount"])
        PosList.sort(reverse=True, key=lambda cat: cat["actCount"])
        NegList_prev.sort(reverse=True, key=lambda cat: cat["actCount"])
        NegList.sort(reverse=True, key=lambda cat: cat["actCount"])

        if len(PosList_prev) != len(PosList):
            print("POS - NUM CATEGORIES CHANGED! UPDATE")
            return True

        # for i in range(len(PosList)):
        #     print("CURR: %s = %d" % (PosList[i]["catName"], PosList[i]["actCount"]))
        #     print("PREV: %s = %d" % (PosList_prev[i]["catName"], PosList_prev[i]["actCount"]))

        for i in range(len(PosList)):
            if PosList_prev[i]["catName"] != PosList[i]["catName"]:
                if PosList_prev[i]["actCount"] != PosList[i]["actCount"]:
                    # print("POS LIST REORDER!")
                    # print("CURR: %s = %d" % (PosList[i]["catName"], PosList[i]["actCount"]))
                    # print("PREV: %s = %d" % (PosList_prev[i]["catName"], PosList_prev[i]["actCount"]))
                    return True

        if len(NegList_prev) != len(NegList):
            # print("NEG LIST - NUM CATEGORIES CHANGED! UPDATE")
            return True

        for i in range(len(NegList_prev)):
            if NegList_prev[i]["catName"] != NegList[i]["catName"]:
                if NegList_prev[i]["actCount"] != NegList[i]["actCount"]:
                    # print("NEG LIST REORDER!")
                    # print("CURR: %s = %d" % (NegList[i]["catName"], NegList[i]["actCount"]))
                    # print("PREV: %s = %d" % (NegList_prev[i]["catName"], NegList_prev[i]["actCount"]))
                    return True

        return False

    def updateFirebase(self: RollingStatWindow):
        # extract relevant data for firebase
        dailyStatsPos = {}
        dailyStatsNeg = {}

        # BDM TODO! refactor to use the _summedWindowTotals function!
        for cat in self.PositiveTotals:
            if cat == "ShowAll_Pos":
                continue
            total = 0
            for subTot in self.PositiveTotals[cat]["subTot"]:
                # print(subTot)
                total = total + subTot
            dailyStatsPos[cat] = {
                "catName": self.PositiveTotals[cat]["catName"],
                "iconName": self.PositiveTotals[cat]["iconName"],
                "isPos": self.PositiveTotals[cat]["isPositive"],
                "actCount": total,
            }

        for cat in self.NegativeTotals:
            if cat == "ShowAll_Neg":
                continue
            total = 0
            for subTot in self.NegativeTotals[cat]["subTot"]:
                # print(subTot)
                total = total + subTot
            dailyStatsNeg[cat] = {
                "catName": self.NegativeTotals[cat]["catName"],
                "iconName": self.NegativeTotals[cat]["iconName"],
                "isPos": self.NegativeTotals[cat]["isPositive"],
                "actCount": total,
            }

    # FIXME:
    # place firebase tasks on queue
    # StatsTasks.updateDailyStatsTask("/dailyStatsPos/", dailyStatsPos)
    # StatsTasks.updateDailyStatsTask("/dailyStatsNeg/", dailyStatsNeg)

    # BDM TODO: refactor these methods to use the proper encoder/decoder
    #           for json & classes.

    @staticmethod
    def toJson(rst):
        data = rst.__dict__.copy()
        data["LastUpdateTime"] = []

        # convert times to iso string format
        for t in rst.LastUpdateTime:
            data["LastUpdateTime"].append(t.isoformat())

        # DEBUGGING
        # print(data)
        # print("dumping data...")

        return json.dumps(data)

    @staticmethod
    def fromJson(data):
        stats = json.loads(data)
        rsw = RollingStatWindow()
        rsw.GlobalCount = stats["GlobalCount"]

        # convert times from iso string format
        rsw.LastUpdateTime = []
        for t in stats["LastUpdateTime"]:
            rsw.LastUpdateTime.append(dateutil.parser.parse(t))

        rsw.PositiveTotals = stats["PositiveTotals"]
        rsw.NegativeTotals = stats["NegativeTotals"]

        return rsw


class RollingStatWindowManager:
    """this is BDM object to manage logic for updating Firebase
    with rolling system stats
    """

    @staticmethod
    def _currentWindow():
        # DEBUGGING
        # print("current window is %d" % datetime.datetime.utcnow().hour)
        return datetime.utcnow().hour

    @staticmethod
    def _outOfDateWindow(t):
        t_now = datetime.utcnow()
        if t.hour <= t_now.hour and t.day != t_now.day:
            return True
        return False

    # given the current DtTm, find out how many rolling
    # windows are now out of date and clear counts.
    # return True if any windows are cleared.
    @staticmethod
    def _clearOldWindows(stats):
        windows_cleared = False
        outdated_windows = []

        # check latest update time for every window
        idx = 0
        for t in stats.LastUpdateTime:
            if RollingStatWindowManager._outOfDateWindow(t):
                # signal windows / values have been cleared / changed.
                # print("DEBUG - WINDOW %d CLEARED AT TIME: %s!" % (idx, t.isoformat()))
                windows_cleared = True

                # set latest update time to NOW
                stats.LastUpdateTime[idx] = datetime.utcnow()

                # get NEGATIVE codes
                # set zero counts for all categories
                for cat in behaviorDataShared.categoryCodesWithNames():
                    # decrement global total
                    stats.GlobalCount = (
                        stats.GlobalCount - stats.NegativeTotals[cat[0]]["subTot"][idx]
                    )

                    # zero out existing total counts for expired data.
                    stats.NegativeTotals[cat[0]]["subTot"][idx] = 0

                # get POSITIVE codes
                # set zero counts for all categories
                for cat in behaviorDataShared.categoryCodesWithNames(False):
                    # decrement global total
                    stats.GlobalCount = (
                        stats.GlobalCount - stats.PositiveTotals[cat[0]]["subTot"][idx]
                    )

                    # zero out existing total counts for expired data.
                    stats.PositiveTotals[cat[0]]["subTot"][idx] = 0

            idx = idx + 1

        # print(stats.LastUpdateTime)

        return windows_cleared

    @staticmethod
    def _incrementVoteCount(stats, vote):
        cat = vote.categoryCode
        w = RollingStatWindowManager._currentWindow()

        # increment global count
        stats.GlobalCount = stats.GlobalCount + 1

        curDict = stats.PositiveTotals if vote.positive else stats.NegativeTotals
        localStatRec = curDict.get(cat)
        if localStatRec is None:
            # TODO: BDM please log error here
            return

        curCount = localStatRec["subTot"][w]
        # update catagory count by category and window
        localStatRec["subTot"][w] = curCount + 1

        # if vote.positive:
        #     stats.PositiveTotals[cat]["subTot"][w] = stats.PositiveTotals[cat]["subTot"][w] + 1
        # else:
        #     stats.NegativeTotals[cat]["subTot"][w] = stats.NegativeTotals[cat]["subTot"][w] + 1

        # set last update time to now
        # print(stats.LastUpdateTime)
        # print("window is %s" % window)
        # print(stats.LastUpdateTime[window])
        stats.LastUpdateTime[w] = datetime.utcnow()

        return stats

    @staticmethod
    def updateRollingStatCount(vote):
        """vote argument is of VoteInfo type"""
        updateFirebase = False
        stats = RollingStatWindow()

        # get memcache
        stats.loadFromMemcache()

        # check if windows are out of date (date rollover)!
        # clears old windows - returns true if anything had to be cleared
        if RollingStatWindowManager._clearOldWindows(stats):
            # print("old windows! update firebase!")
            updateFirebase = True

        # update stats (and data)
        oldStats = stats.copy()
        RollingStatWindowManager._incrementVoteCount(stats, vote)

        # check firebase updates are required
        if stats.percentIncreased(GLOBAL_PERCENT_INCREASE, oldStats):
            # print("global increase! update firebase!!")
            updateFirebase = True
        elif stats.isReordered(oldStats):
            # print("stats need reordering! update firebase!")
            updateFirebase = True

        # update memcache
        stats.saveToMemcache()

        # if needed, update firebase
        if updateFirebase:
            stats.updateFirebase()
