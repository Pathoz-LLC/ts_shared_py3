from __future__ import annotations
from enum import IntEnum, unique

# ACTUAL nodes from DB
# _commNewsInternal
# behaviorStats
# clStats
# commNews-activePaths
# dailyStatsNeg
# dailyStatsPos


@unique
class FirDbPath(IntEnum):
    DAILY_STATS_NEG = 0
    DAILY_STATS_POS = 1
    COMMUNITY_NEWS_PRIVATE = 2
    COMMUNITY_NEWS = 3
    COMMIT_LVL_STATS = 4
    BEHAVIOR_STATS = 5

    @property
    def urlPathTmpl(self: FirDbPath) -> str:
        if self == FirDbPath.DAILY_STATS_NEG:
            return "dailyStatsNeg"
        elif self == FirDbPath.DAILY_STATS_POS:
            return "dailyStatsPos"
        elif self == FirDbPath.COMMUNITY_NEWS_PRIVATE:
            return "_commNewsInternal"
        elif self == FirDbPath.COMMUNITY_NEWS:
            return "commNews-activePaths"
        elif self == FirDbPath.COMMIT_LVL_STATS:
            return "clStats"
        elif self == FirDbPath.BEHAVIOR_STATS:
            return "behaviorStats"
