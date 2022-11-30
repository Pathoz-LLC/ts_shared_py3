import json
from dataclass_wizard import JSONWizard

from datetime import date
from dataclasses import dataclass, field, fields, make_dataclass

from .base import BaseApiData
from ts_shared_py3.common.messages.tracking import TrackingPayloadMessage
import constants

# usage:


@dataclass
class BehaviorKeysMessage(BaseApiData):
    surveyId: int = field(default=2)
    personId: int = field(default=0, required=True)
    priorMonthsToLoad: int = field(default=0)


@dataclass
class BehaviorStatsFilterMessage(BaseApiData):
    behaviorCode: str = field(required=True)
    state: str = field(default="")
    zipCode: str = field(default="")
    lat: float = field(default=0.0)
    lon: float = field(default=0.0)


BehaviorStatsRequestMessage = make_dataclass(
    "BehaviorStatsRequestMessage",
    fields(BehaviorKeysMessage) + fields(BehaviorStatsFilterMessage),
)

# BehaviorRowMsg = model_message(Entry, exclude=('addDateTime', 'modifyDateTime') )
@dataclass
class BehaviorRowMsg(BaseApiData):
    behaviorCode: str = field(required=True)
    feelingStrength: int = field(default=0)  # 0-4
    significanceStrength: int = field(default=0)  # NIU
    comments: str = field(default="")
    lat: float = field(default=0.0)
    lon: float = field(default=0.0)
    shareDetails: str = field(default="")
    surveyId: int = field(default=2)
    personId: int = field(default=0, required=True)
    # Occur SHOULD allow time component
    occurDateTime: float = field(default=0.0)
    behaviorId: int = field(default=-1)  # used to find same rec upon update/replace
    positive: bool = field(default=False)
    categoryCode: str = field(default="general")
    # origOccurDateTime: int = field(default=0)11)  # used to find same rec upon update/replace


# what swift is sending is below:
# note that personId, feelingStrength & significanceStrength are the WRONG data types
# {
#   "comments" : "my notes about leftovers",
#   "lon" : 7.7999999999999998,
#   "behaviorCode" : "ateMyLeftovers",
#   "behaviorId" : "-1",
#   "personId" : "22334",
#   "feelingStrength" : "3",
#   "positive" : true,
#   "lat" : 5.5999999999999996,
#   "significanceStrength" : "2",
#   "occurDateTime" : "1963-11-08T06:00:00.000Z",
#   "categoryCode" : "FIXME",
#   "shareDetails" : "F:fb12345;T:tw876543;",
#   "surveyId" : ""
# }


@dataclass
class BehaviorHistoryMessage(BaseApiData):
    beganDatingDate: date = field()
    endedDatingDate: date = field()
    items = list[BehaviorRowMsg] = []
    firstLogDtTm: float = field(default=0.0)  # as epoch
    lastLogDtTm: float = field(default=0.0)


# new behavior entries summary logic below
# 11/20/17
@dataclass
class StatsAndMetricsMsg(BaseApiData):
    influenceSummary: str = field(default="")
    communicationScore: float = field(default=0.0)
    trustScore: float = field(default=0.0)
    respectScore: float = field(default=0.0)
    lifestyleScore: float = field(default=0.0)
    overallScore: float = field(default=0.0)
    feelingsScore: float = field(default=0.0)
    maleReportCount: int = field(default=0)
    femaleReportCount: int = field(default=0)


@dataclass
class BehEntryWrapperMessage(BaseApiData):
    """also used to include phases/intervals in the list of beh-entries"""

    behaviorCode: str = field(default="", required=True)
    feelingStrength: int = field(default=0, required=True)
    longitude: float = field(default=0.0)
    comments: str = field(default="")
    shareDetails: str = field(default="", required=True)
    occurDateTime: float = field(default=0.0)  # as Epoch
    addDateTime: float = field(default=0.0)
    modifyDateTime: float = field(default=0.0)
    behaviorText: str = field(default="")
    isPositive: bool = field(default=False)(10, default=True)
    keywords: str = field(default="")
    oppBehaviorCode: str = field(default="")
    oppBehaviorText: str = field(default="")
    parentCat: str = field(default="")
    rootCat: str = field(default="")
    parentCatLabel: str = field(default="")
    rootCatLabel: str = field(default="")
    personName: str = field(default="", required=True)
    latitude: float = field(default=0.0)
    commRiskScore: float = field(default=0.0)
    # dont really need rowType currently because rootCat == commitLevel in "cl" case
    rowType: str = field(default="beh")  # or cl (commitLevel)
    # when rowType == cl, then only fields in use are: behaviorCode, shareDetails, occurDateTime
    # stats = BaseApiDataField(StatsAndMetricsMsg, 21)


@dataclass
class BehaviorLogSummaryMessage(BaseApiData):
    beganDatingDt: date = field(required=True)
    endedDatingDt: date = field()
    persId: int = field(default=0, required=True)
    persName: str = field(default="", required=True)
    persCurRelStatus: str = field(default="CASUAL")  # enums.DisplayCommitLvl
    firstEntryDttm: float = field(default=0.0, required=True)  # as epoch
    lastEntryDttm: float = field(default=0.0, required=True)
    count: int = field(default=0, required=True)
    entries: list[BehEntryWrapperMessage] = []
    phaseHistory: list[TrackingPayloadMessage] = []


@dataclass
class BehaviorSearchTermMsg(BaseApiData):
    userId: str = field(default="", required=True)
    searchPhrase: str = field(default="", required=True)
    failed: bool = field(default=False)


# full behavior list
@dataclass
class BehOrCatMsg(BaseApiData):
    # embedded in FullBehaviorListMsg
    code: str = field(default="", required=True)
    parentCode: str = field(default="", required=True)
    catCode: str = field(default="", required=True)
    oppositeCode: str = field(default="")
    text: str = field(default="", required=True)
    catDescription: str = field(default="", required=True)
    isCategory: bool = field(default=False, required=True)
    isPositive: bool = field(default=False, required=True)
    sort: int = field(default=100, required=True)
    keywords: str = field(default="", required=True)


@dataclass
class NodeListMsg(BaseApiData):
    # embedded in FullBehaviorListMsg
    code: str = field(default="", required=True)
    children: str = field(default="", repeated=True)


@dataclass
class FullBehaviorListMsg(BaseApiData):
    # top level msg returned to client
    masterList: list[BehOrCatMsg] = []
    topCategoryCodes: str = field(default="", repeated=True)
    graph: list[NodeListMsg] = []


# return list of NEGATIVE top level category codes
@dataclass
class CatCodeTextMsg(BaseApiData):
    # embedded in FullBehaviorListMsg
    code: str = field(default="", required=True)
    name: str = field(default="", required=True)
    # how many ??'s left unanswered
    answerCount: int = field(default=0, required=True)
    availCount: int = field(default=10, required=True)
    # perhaps we should reset availCount each time they add a prospect??
    iconName: str = field(default="", required=True)
    pos: bool = field(default=False)(6, required=True, default=False)


@dataclass
class TopCategoriesMsg(BaseApiData):
    # list for client
    items: list[CatCodeTextMsg] = []


# global stats about behavior
@dataclass
class BehStatMsg(BaseApiData):
    # embedded in VoteTypeMsg
    totCount: int = field(default=0, required=True)
    slotCounts: int = field(default=0, repeated=True)


@dataclass
class BehStatMsgAdapter:
    @staticmethod
    def toDict(behStatMsg):
        return {"totCount": behStatMsg.totCount, "slotCounts": behStatMsg.slotCounts}

    @staticmethod
    def fromDict(dct):
        # print("BehStatMsg: %s" % dct)
        tc = dct.get("totCount", 0)
        sc = dct.get("slotCounts", [0, 0, 0, 0])
        return BehStatMsg(totCount=tc, slotCounts=sc)


@dataclass
class VoteTypeMsg(BaseApiData):
    # embedded in BehVoteStatsMsg
    feeling: list[BehStatMsg] = []
    concern: list[BehStatMsg] = []
    frequency: list[BehStatMsg] = []


@dataclass
class VoteTypeMsgAdapter:
    @staticmethod
    def toDict(voteTypeMsg):
        return {
            "feeling": BehStatMsgAdapter.toDict(voteTypeMsg.feeling),
            "concern": BehStatMsgAdapter.toDict(voteTypeMsg.concern),
            "frequency": BehStatMsgAdapter.toDict(voteTypeMsg.frequency),
        }

    @staticmethod
    def fromDict(dct):
        feel = dct.get("feeling", {})
        if not isinstance(feel, BehStatMsg):
            feel = BehStatMsgAdapter.fromDict(feel)
        con = dct.get("concern", {})
        if not isinstance(con, BehStatMsg):
            con = BehStatMsgAdapter.fromDict(con)
        freq = dct.get("frequency", {})
        if not isinstance(freq, BehStatMsg):
            freq = BehStatMsgAdapter.fromDict(freq)
        return VoteTypeMsg(feeling=feel, concern=con, frequency=freq)


@dataclass
class BehVoteStatsMsg(BaseApiData):
    behaviorCode: str = field(default="", required=True)
    female: list[VoteTypeMsg] = []
    male: list[VoteTypeMsg] = []
    unknown: list[VoteTypeMsg] = []
    categoryName: str = field(default="", required=True)


@dataclass
class BehVoteStatAdapter:
    @staticmethod
    def toDict(behVoteStatsMsg):
        return {
            "behaviorCode": behVoteStatsMsg.behaviorCode,
            "female": VoteTypeMsgAdapter.toDict(behVoteStatsMsg.female),
            "male": VoteTypeMsgAdapter.toDict(behVoteStatsMsg.male),
            "unknown": VoteTypeMsgAdapter.toDict(behVoteStatsMsg.unknown),
            "categoryName": behVoteStatsMsg.categoryName,
        }

    @staticmethod
    def fromDict(dct):
        bc = dct.get("behaviorCode", "unknown")
        f = dct.get("female", {})
        if not isinstance(f, VoteTypeMsg):
            f = VoteTypeMsgAdapter.fromDict(f)
        m = dct.get("male", {})
        if not isinstance(m, VoteTypeMsg):
            m = VoteTypeMsgAdapter.fromDict(m)
        u = dct.get("unknown", {})
        if not isinstance(u, VoteTypeMsg):
            u = VoteTypeMsgAdapter.fromDict(u)
        cn = dct.get("categoryName", "unknown")
        return BehVoteStatsMsg(
            behaviorCode=bc, female=f, male=m, unknown=u, categoryName=cn
        )


@dataclass
class BehSrchLogMsg(BaseApiData):
    searchStr: str = field(default="", required=True)
    foundCount: int = field(default=0, required=True)
    # behCode ultimately Selected is for future
    behCodeSelected: str = field(default="")
