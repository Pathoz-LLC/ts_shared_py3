import os
from datetime import date

PROJ_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "tsapi-stage2")
BASE_URL_SUFFIX = os.environ.get("BASE_URL_SUFFIX", "tsapi-stage2.appspot.com/")
FIR_CREDS_FILENAME = os.environ.get(
    "FIREBASE_ADMIN_CREDENTIAL",
    "auth/stage/ts-firebase-adminsdk.json",
)

# END DATE for latest Interval/Phase that has not ended
DISTANT_FUTURE_DATE = date(4000, 12, 31)
# impossible date before app was available
EARLY_DEFAULT_DATE = date(2015, 1, 1)

IS_RUNNING_LOCAL = False

if os.getenv("GAE_ENV", "").startswith("standard"):
    # Production in the standard environment
    IS_RUNNING_LOCAL = False
else:
    # Local execution.
    IS_RUNNING_LOCAL = True


# usage:
# from common.scoring import constants as sc
DAYS_IN_RESCORE_WINDOW = 4
FEELING_CD_PREFIX = "feeling"

# MAX_BUCKET_WIDTH_IN_DAYS = 30
# MAX_SCORE_BUCKETS_FOR_CLIENT = 30

# SCORE_ROLLUP_WINDOW_DAYS_STORAGE = (
#     1  # store each days score in a "month" object for persistence
# )
# SCORE_ROLLUP_WINDOW_DAYS_DISPLAY = (
#     7  # default but will be calculated based on prospect-tracking-width
# )

# 3 positions
BEH_MIN_SLIDER_POSITION = 1
BEH_MAX_SLIDER_POSITION = 3

# 4 positions
VALUES_MIN_SLIDER_POSITION = 1
VALUES_MAX_SLIDER_POSITION = 4

# 8 should be highest in PG's spreadsheet; headroom for slider bump
APP_IMPACT_WEIGHT_MAX = 9
IMPACT_WEIGHT_DECIMALS = 4
FINAL_SCORE_DECIMALS = 3  # row scores

COMMIT_CHNG_CODE_CONST = "commitLevelChange"

# FW == FinalWindow
# prospect scores derived from FW plus events from INCLUDE_DAYS_PRIOR_START_FW
DAYS_BACK_4_FINAL_WTAVG_SCORE = 45  # latest_entry - 45 days

# INCLUDE_DAYS_PRIOR_START_FW = 12
# significant events are those 2b included in INCLUDE_DAYS_PRIOR_START_FW
# they are selected by impact weight; at present, this is ALL events
SIG_EVENT_MIN_IMPACT_WEIGHT = 0.0
# NO PERSIST is a filler day (no user entries)
NO_PERSIST_REC_ID = -1

DERIVE_FINAL_FROM_GROUP = False

ISO_8601_DATE_FORMAT = "%Y-%m-%d"  # 2022-08-12
ISO_8601_DATETIME_FORMAT = "%Y-%m-%dT%H:%M"  # 2022-08-12T09:15     "%Y-%m-%dT%H:%M:%z"
ISO_8601_TIME_FORMAT = "%H:%M"

# FIREBASE_CREDS_PATH = "ts_shared_py3/auth/{0}".format(FIR_CREDS_FILENAME)
# # User Score section;  must add to 1
# USER_PCT_WEIGHT_DAILY_FEELINGS = 0.5
# USER_PCT_WEIGHT_TRUST_TELLS = 0.20
# USER_PCT_WEIGHT_BEHAVIORS = 0.30
#
# # Touchstone Score section;  must add to 1
# TSTO_PCT_WEIGHT_COMMUNITY = 0.25
# TSTO_PCT_WEIGHT_USER_SCORE = 0.75
#
#
# # Community Score section
# COMM_BLA = 0
# usage:
# from common.scoring import constants as sc
