from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional
import google.cloud.ndb as ndb

# from itertools import repeat

#
# from common.models.entry_adapter import ScoreAdapter
# from common.models.raw_day_scores_by_month import RawDayScores
from common.models.entry_adapter import InputEntryAdapter
from common.utils.arg_types import ArgTypes
from .baseNdb_model import BaseNdbModel


class ProspectRecentScores(BaseNdbModel):
    """
    --- one record per user/prospect combo
    keeps THE FINAL (user & app) score after
    each time a recalc completes
    also stores a list of final RAW day scores
    that can be passed in to smoothing for contiuuity

    updated every time rescoring happens
    """

    DAY_COUNT_TO_KEEP = 10

    lastAppUserScore = ndb.FloatProperty(default=0.0)
    lastCommunityScore = ndb.FloatProperty(default=0.0)
    # keep 10 most recent adapter recs from prior scoring runs
    unscoredAdaptersFromPriorRuns = ndb.LocalStructuredProperty(
        InputEntryAdapter, repeated=True
    )

    @property
    def unscoredCount(self: ProspectRecentScores) -> int:
        return len(self.unscoredAdaptersFromPriorRuns)

    @classmethod
    def loadOrCreate(cls, userId: str, persId: int) -> ProspectRecentScores:
        recKey = ndb.Key("User", userId, cls.__name__, persId)
        pss = recKey.get()
        if pss is None:
            pss = ProspectRecentScores(
                key=recKey, lastAppUserScore=0.5, lastCommunityScore=0.5
            )
            pss.unscoredAdaptersFromPriorRuns = []
        return pss

    def _clearAndSaveOnlyForTesting(self: ProspectRecentScores):
        # do not use in production code
        self.unscoredAdaptersFromPriorRuns = []
        self.put()

    def _idxIfExists(self: ProspectRecentScores, dt: date) -> Optional[int]:
        return next(
            (
                i
                for i, iea in enumerate(self.unscoredAdaptersFromPriorRuns)
                if iea.occurDt == dt
            ),
            None,
        )

    def appendNewAdapterRecs(
        self: ProspectRecentScores, newUnscoredAdapterRecs: list[InputEntryAdapter]
    ) -> None:
        for scAdpt in newUnscoredAdapterRecs:
            # add or replace existing data
            idx = self._idxIfExists(scAdpt.occurDt)
            if idx is None:
                self.unscoredAdaptersFromPriorRuns.append(scAdpt)
            else:
                self.unscoredAdaptersFromPriorRuns[idx] = scAdpt

    def updateFinalScoresAndSave(
        self: ProspectRecentScores,
        latestAppUserScore: float,
        latestCommunityScore: float,
    ) -> int:
        # returns len(self.unscoredAdaptersFromPriorRuns)

        self.lastAppUserScore = latestAppUserScore
        self.lastCommunityScore = latestCommunityScore

        # sort from newest (most recent) to oldest
        self.unscoredAdaptersFromPriorRuns.sort(key=lambda x: x.occurDt, reverse=True)
        # now truncate the list to keep only newest recs
        self.unscoredAdaptersFromPriorRuns = self.unscoredAdaptersFromPriorRuns[
            0 : self.DAY_COUNT_TO_KEEP - 1
        ]

        self.put()
        return len(self.unscoredAdaptersFromPriorRuns)
