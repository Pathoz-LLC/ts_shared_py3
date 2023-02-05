from random import randint
from typing import Union, TypeVar

import google.cloud.ndb as ndb
from ..enums.commitLevel import CommitLevel_Display, NdbCommitLvlProp
import logging

# usage
# from common.models.commitStats import CommitStats

GLOBAL_REGION = "global"  # group stats by state when we have more data
STATS_SHARD_COUNT = 20  # dont reduce this # or counts will be missed

ALL_COMMITLVL_DFLTS = None


class CommitRollup(ndb.Model):
    """
    count of people in a particular relationship state at present
    """

    # FIXME
    commitLevel = NdbCommitLvlProp(required=True)
    count = ndb.IntegerProperty(default=0)

    def __str__(self):
        dcl = CommitLevel_Display(self.commitLevel)
        return "{0}:{1}".format(dcl.name, self.count)

    @staticmethod
    def allSeed():
        global ALL_COMMITLVL_DFLTS
        # its vital that this list order never changes
        # we're counting on index position in CommitStats.counts
        if ALL_COMMITLVL_DFLTS == None:
            ALL_COMMITLVL_DFLTS = [
                CommitRollup(commitLevel=dcl, count=0)
                for dcl in CommitLevel_Display.masterList()
            ]

        return ALL_COMMITLVL_DFLTS


class CommitStats(ndb.Model):
    """keeps counts of commitment levels
    eventually grouped by region
    """

    region = ndb.TextProperty(indexed=False, required=True, default=GLOBAL_REGION)
    updateDtTm = ndb.DateTimeProperty(indexed=False, required=True, auto_now=True)
    # per CL counts
    # its vital that this list order never changes
    # we're counting on index position in CommitStats.counts
    counts = ndb.LocalStructuredProperty(CommitRollup, repeated=True)

    def __str__(self):
        x = "\n".join([str(cr) for cr in self.counts])
        return "\n{0}".format(x)

    def _update(self, curCommitLvl, priorCommitLvl):
        """ """
        for cr in self.counts:
            if cr.commitLevel == priorCommitLvl and cr.count > 0:
                cr.count -= 1
            elif cr.commitLevel == curCommitLvl:
                cr.count += 1
        # assert updtCount == targetCount, "value not updated {0}-{1}".format(updtCount, targetCount)

    def _mergeCountsToSelf(self, rec):
        # copy vals from another shard onto this rec
        for idx, cr in enumerate(rec.counts[0:5]):
            self.counts[idx].count += cr.count
            assert idx < 5, "enumerate yielding %s from %s" % (idx, len(rec.counts))

    def _convertCountToPctOfTotal(self):
        total = self.sumOfCount
        total = float(total)  # avoid floor division
        # dm = "ConvertCountToPctOfTotal:  counts:{0}  total:{1}".format(self.counts, total)
        # print(dm)
        for cr in self.counts:
            cr.count = int((cr.count / total) * 100)

    def _save(self):
        # store to ndb
        # I was somehow getting double len counts lists????
        # assert len(self.counts) == DisplayCommitLvl.typeCount(), "Err: Corrupt rec w {0} rows".format(len(self.counts))
        if len(self.counts) == CommitLevel_Display.typeCount():
            self.put()
        else:
            m = "Err: CommitStats rec {0} had {1} rows".format(
                self.key.id(), len(self.counts)
            )
            logging.error(m)
            print(m)

    @property
    def sumOfCount(self):
        # never return zero to avoid divide error
        return max(1, sum([cr.count for cr in self.counts]))

    @property
    def asDict(self):
        # return self as nested dictionary
        d = dict()
        for cr in self.counts:
            d[cr.commitLevel.name] = cr.count
        return {GLOBAL_REGION: d}

    @staticmethod
    @ndb.transactional(retries=1)
    def updateCounts(curCommitLvl, priorCommitLvl=None):
        """public api to store updated stats"""
        rec = CommitStats._loadOrCreateRec()
        rec._update(curCommitLvl, priorCommitLvl)
        rec._save()

    @staticmethod
    def _loadOrCreateRec():
        """pick one shard rec to distribute concurrent write load
        either load or create it
        """
        shardID = randint(1, STATS_SHARD_COUNT)
        key = _makeCommitStatsShardKey(GLOBAL_REGION, shardID)
        rec = key.get()
        if rec is None:
            rec = CommitStats._newRec()
            rec.key = key
        return rec

    @staticmethod
    def _newRec():
        """create new empty rec; only for internal use"""
        cs = CommitStats()
        cs.counts = CommitRollup.allSeed()
        return cs

    @staticmethod
    def loadAggregateStats():
        """
        roll up stats (across all shards
        """
        allRecs = CommitStats._loadAllStatShards()

        firstRec = CommitStats._newRec()
        if len(allRecs) > 0:
            firstRec = allRecs[0]

        tmpl = "\n77$$: {0} {1}"
        print(tmpl.format("1.1", firstRec))
        for rec in allRecs[1:]:
            print(tmpl.format(" .x", rec))
            firstRec._mergeCountsToSelf(rec)

        print(tmpl.format("1.2", firstRec))
        firstRec._convertCountToPctOfTotal()
        print(tmpl.format("1.3", firstRec))
        firstRec.key = None  # keep this rec from being confused with stored recs

        return firstRec

    @staticmethod
    def _loadAllStatShards():
        allStatRecKeys = CommitStats._all_keys(GLOBAL_REGION)
        allRecs = ndb.get_multi(allStatRecKeys)
        # remove empty slots from list
        return [r for r in allRecs if r is not None]

    @staticmethod
    def _all_keys(region):
        """Returns all possible keys for the counter name given the config.
        Returns:
            The full list of ndb.Key values corresponding to all the possible
                counter shards that could exist.
        """
        return [
            _makeCommitStatsShardKey(region, idx + 1)
            for idx in range(STATS_SHARD_COUNT)
        ]

    @staticmethod
    def zeroCountsForTesting():
        """erase counts created by prior tests"""
        allRecs = CommitStats._loadAllStatShards()
        for rec in allRecs:
            for cr in rec.counts:
                cr.count = 0
            rec._save()


def _makeCommitStatsShardKey(region, instanceID):
    assert instanceID > 0, "invalid ID"
    return ndb.Key("Region", region, CommitStats, instanceID)


# def _updateFirebase(self):
#     # extract relevant data for firebase
#     clStats = self.asDict()
#     # push data to this path at Firebase
#     # in future, global can be replaced with user state or hometown
#     StatsTasks.pushCommitStatsTask()
#
# @staticmethod
# def pushStatsToFirebase():
#     """ public api to store updated stats
#     """
#     totRec = CommitStats._loadAggregateStats()
#     totRec._updateFirebase()
