"""
constants to determine how the behavior scoring works

from common.behavior.constants import DECEPTION_STATS_NODE, GENERATE_TEST_BEH_STATS,
STATS_RELOAD_INTERVAL_HOURS, MIN_BEHAVE_ENTRIES_TO_CALC_STATS
"""

from datetime import datetime, date, time, timedelta

# names of the Firebase DB nodes follow:
BEHAVIOR_STATS_NODE = "behaviorStats"
FIRDB_TRUST_STATS_NODE = "trustStats"
REDFLAGS_STATS_NODE = "redFlagStats"

STATS_RELOAD_INTERVAL_HOURS = 4  # Global stats into memcache
MIN_BEHAVE_ENTRIES_TO_CALC_STATS = 8  # to be valid to return results

MAX_SCORE_PER_BEH = 1  # our ONE constant
MAX_FEELING = 4  # max slider value
MAX_FREQUENCY = 4  # max slider value
FEELING_NUDGE = 0.35  # pct of FlexGap to allocate to feeling bump
FREQUENCY_NUDGE = 0.65  # pct of FlexGap to allocate to frequency bump
FREQUENCY_DEGRADE_DEFAULT = (
    0.65  # NIU:  future to reduce FREQUENCY_NUDGE in event of low FEELING scores....
)

# below currently NIU
FREQUENCY_AMPLIFIER = 1
FEELINGS_AMPLIFIER = 1

QUERY_START_DEFAULT = date(2016, 6, 1)

GENERATE_TEST_BEH_STATS = False

SHOWALL_CAT_LABEL = "Search All"
SHOWALL_CODE_PREFIX = "ShowAll_"

# behavior code used in client when no actual behavior is selected
FEELING_CD_PREFIX = "feelingReport"
FEELING_ONLY_CODE_POS = "feelingReportPos"
FEELING_ONLY_CODE_NEG = "feelingReportNeg"

# below moved to test
# sample relationship data for scoring tests
# GETTING_BETTER_FILENAME = "gettingBetter.csv"
# VOLATILE_FILENAME = "volatile.csv"
# GETTING_WORSE_FILENAME = "gettingWorse.csv"
