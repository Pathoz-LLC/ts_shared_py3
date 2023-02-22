from __future__ import annotations

from datetime import date, datetime
from typing import ClassVar, Type, Optional
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from .tracking import TrackingPayloadMsgDc

""" Important Note:
    it is vital that you set the Schema.__model__
    equal to the Classname
    this will allow creation & return of actual Model instances
    inside our endpoints
"""

# example of validation
@dataclass()
class BehaviorKeysMessage(BaseApiData):
    surveyId: int = field(default=2)
    personId: int = field(default=0, metadata=dict(required=True))
    priorMonthsToLoad: int = field(
        default=3,
        metadata=dict(
            required=False,
            validate=validate.Range(min=1, max=12),
        ),
    )
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class BehaviorStatsFilterMessage(BaseApiData):
    behaviorCode: str = field(metadata=dict(required=True))
    state: str = field(default="")
    zipCode: str = field(default="")
    lat: float = field(default=0.0)
    lon: float = field(default=0.0)
    #
    Schema: ClassVar[Type[Schema]] = Schema


BehaviorStatsRequestMessage = make_dataclass(
    "BehaviorStatsRequestMessage",
    fields=[
        ("BehaviorKeysMessage", BehaviorKeysMessage),
        ("BehaviorStatsFilterMessage", BehaviorStatsFilterMessage),
    ],
)

# BehaviorRowMsg = model_message(Entry, exclude=('addDateTime', 'modifyDateTime') )
@dataclass()
class BehaviorRowMsg(BaseApiData):
    behaviorCode: str = field(metadata=dict(required=True))
    # used to find same rec upon update/replace
    secsToOrigDtTm: Optional[int] = field(default=0, metadata=dict(required=False))
    # origOccurDateTime: datetime = field()  # used to find same rec upon update/replace

    feelingStrength: int = field(default=2)  # 0-4
    # significanceStrength: int = field(default=0)  # NIU
    comments: str = field(default="")
    lat: float = field(default=0.0)
    lon: float = field(default=0.0)
    shareDetails: str = field(default="")
    surveyId: int = field(default=2)
    personId: int = field(default=0, metadata=dict(required=True))
    # Occur SHOULD allow time component
    occurDateTime: datetime = field(default_factory=lambda: datetime.now())
    positive: bool = field(default=False)
    categoryCode: str = field(default="general")
    #
    Schema: ClassVar[Type[Schema]] = Schema


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


@dataclass()
class BehaviorHistoryMessage(BaseApiData):
    beganDatingDate: date = field()
    endedDatingDate: date = field()
    firstLogDtTm: datetime = field(metadata=dict(required=False))  # as epoch
    lastLogDtTm: datetime = field(metadata=dict(required=False))
    items: list[BehaviorRowMsg] = field(default_factory=lambda: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema


# new behavior entries summary logic below
# 11/20/17
@dataclass()
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
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class BehEntryWrapperMessage(BaseApiData):
    """also used to include phases/intervals in the list of beh-entries"""

    behaviorCode: str = field(default="", metadata=dict(required=True))
    feelingStrength: int = field(default=0, metadata=dict(required=True))
    longitude: float = field(default=0.0)
    latitude: float = field(default=0.0)
    comments: str = field(default="")
    shareDetails: str = field(default="", metadata=dict(required=True))
    occurDateTime: float = field(default=0.0)  # as Epoch
    addDateTime: float = field(default=0.0)
    modifyDateTime: float = field(default=0.0)
    behaviorText: str = field(default="")
    isPositive: bool = field(default=False)
    keywords: str = field(default="")
    oppBehaviorCode: str = field(default="")
    oppBehaviorText: str = field(default="")
    parentCat: str = field(default="")
    rootCat: str = field(default="")
    parentCatLabel: str = field(default="")
    rootCatLabel: str = field(default="")
    personName: str = field(default="", metadata=dict(required=True))
    commRiskScore: float = field(default=0.0)
    # dont really need rowType currently because rootCat == commitLevel in "cl" case
    rowType: str = field(default="beh")  # or cl (commitLevel)
    # when rowType == cl, then only fields in use are: behaviorCode, shareDetails, occurDateTime
    # stats = BaseApiDataField(StatsAndMetricsMsg, 21)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class BehaviorLogSummaryMessage(BaseApiData):
    endedDatingDt: date = field()
    beganDatingDt: date = field(
        default_factory=lambda: date.today(), metadata=dict(required=True)
    )

    persId: int = field(default=0, metadata=dict(required=True))
    persName: str = field(default="", metadata=dict(required=True))
    persCurRelStatus: str = field(default="CASUAL")  # enums.DisplayCommitLvl
    firstEntryDttm: date = field(
        default_factory=lambda: date.today(), metadata=dict(required=True)
    )  # as epoch
    lastEntryDttm: date = field(
        default_factory=lambda: date.today(), metadata=dict(required=True)
    )
    count: int = field(default=0, metadata=dict(required=True))
    entries: list[BehEntryWrapperMessage] = field(default_factory=lambda: [])
    phaseHistory: list[TrackingPayloadMsgDc] = field(default_factory=lambda: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class BehaviorSearchTermMsg(BaseApiData):
    userId: str = field(default="", metadata=dict(required=True))
    searchPhrase: str = field(default="", metadata=dict(required=True))
    failed: bool = field(default=False)
    #
    Schema: ClassVar[Type[Schema]] = Schema


# full behavior list
@dataclass()
class BehOrCatMsg(BaseApiData):
    # embedded in FullBehaviorListMsg
    code: str = field(default="", metadata=dict(required=True))
    parentCode: str = field(default="", metadata=dict(required=True))
    catCode: str = field(default="", metadata=dict(required=True))
    oppositeCode: str = field(default="")
    text: str = field(default="", metadata=dict(required=True))
    catDescription: str = field(default="", metadata=dict(required=True))
    isCategory: bool = field(default=False, metadata=dict(required=True))
    isPositive: bool = field(default=False, metadata=dict(required=True))
    sort: int = field(default=100, metadata=dict(required=True))
    keywords: str = field(default="", metadata=dict(required=True))
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class NodeListMsg(BaseApiData):
    # embedded in FullBehaviorListMsg
    code: str = field(default="", metadata=dict(required=True))
    children: list[str] = field(default_factory=lambda: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class FullBehaviorListMsg(BaseApiData):
    # top level msg returned to client
    topCategoryCodes: list[str] = field(default_factory=lambda: [])
    masterList: list[BehOrCatMsg] = field(default_factory=lambda: [])
    graph: list[NodeListMsg] = field(default_factory=lambda: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema


# return list of NEGATIVE top level category codes
@dataclass()
class CatCodeTextMsg(BaseApiData):
    # embedded in FullBehaviorListMsg
    code: str = field(default="", metadata=dict(required=True))
    name: str = field(default="", metadata=dict(required=True))
    # how many ??'s left unanswered
    answerCount: int = field(default=0, metadata=dict(required=True))
    availCount: int = field(default=10, metadata=dict(required=True))
    # perhaps we should reset availCount each time they add a prospect??
    iconName: str = field(default="", metadata=dict(required=True))
    pos: bool = field(default=False, metadata=dict(required=True))
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class TopCategoriesMsg(BaseApiData):
    # list for client
    items: list[CatCodeTextMsg] = field(default_factory=lambda: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema


# global stats about behavior
@dataclass()
class BehStatMsg(BaseApiData):
    # embedded in VoteTypeMsg
    totCount: int = field(default=0, metadata=dict(required=True))
    slotCounts: list[int] = field(default_factory=lambda: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema


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


@dataclass()
class VoteTypeMsg(BaseApiData):
    # embedded in BehVoteStatsMsg
    feeling: list[BehStatMsg] = field(default_factory=lambda: [])
    concern: list[BehStatMsg] = field(default_factory=lambda: [])
    frequency: list[BehStatMsg] = field(default_factory=lambda: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema

    @staticmethod
    def defaultEmpty() -> VoteTypeMsg:
        return VoteTypeMsg(feelings=[], concern=[], frequency=[])


class VoteTypeMsgAdapter:
    @staticmethod
    def toDict(voteTypeMsg):
        return {
            "feeling": BehStatMsgAdapter.toDict(voteTypeMsg.feeling),
            "concern": BehStatMsgAdapter.toDict(voteTypeMsg.concern),
            "frequency": BehStatMsgAdapter.toDict(voteTypeMsg.frequency),
        }

    @staticmethod
    def fromDict(dct: dict):
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


@dataclass()
class BehVoteStatsMsg(BaseApiData):
    behaviorCode: str = field(default="", metadata=dict(required=True))
    categoryName: str = field(default="", metadata=dict(required=True))
    female: VoteTypeMsg = field(default_factory=lambda: VoteTypeMsg.defaultEmpty())
    male: VoteTypeMsg = field(default_factory=lambda: VoteTypeMsg.defaultEmpty())
    unknown: VoteTypeMsg = field(default_factory=lambda: VoteTypeMsg.defaultEmpty())
    #
    Schema: ClassVar[Type[Schema]] = Schema


class BehVoteStatAdapter:

    #

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


@dataclass()
class BehSrchLogMsg(BaseApiData):
    searchStr: str = field(default="", metadata=dict(required=True))
    foundCount: int = field(default=0, metadata=dict(required=True))
    # behCode ultimately Selected is for future
    behCodeSelected: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


# update all schemas to refer to the enclosing model
# add the model so creation can work in reverse!
BehaviorKeysMessage.Schema.__model__ = BehaviorKeysMessage
BehaviorRowMsg.Schema.__model__ = BehaviorRowMsg
BehaviorHistoryMessage.Schema.__model__ = BehaviorHistoryMessage
StatsAndMetricsMsg.Schema.__model__ = StatsAndMetricsMsg
BehEntryWrapperMessage.Schema.__model__ = BehEntryWrapperMessage
BehaviorLogSummaryMessage.Schema.__model__ = BehaviorLogSummaryMessage

BehaviorSearchTermMsg.Schema.__model__ = BehaviorSearchTermMsg
BehOrCatMsg.Schema.__model__ = BehOrCatMsg
NodeListMsg.Schema.__model__ = NodeListMsg
FullBehaviorListMsg.Schema.__model__ = FullBehaviorListMsg
CatCodeTextMsg.Schema.__model__ = CatCodeTextMsg

TopCategoriesMsg.Schema.__model__ = TopCategoriesMsg
BehStatMsg.Schema.__model__ = BehStatMsg
# BehStatMsgAdapter.Schema.__model__ = BehStatMsgAdapter
VoteTypeMsg.Schema.__model__ = VoteTypeMsg

# VoteTypeMsgAdapter.Schema.__model__ = VoteTypeMsgAdapter
BehVoteStatsMsg.Schema.__model__ = BehVoteStatsMsg
# BehVoteStatAdapter.Schema.__model__ = BehVoteStatAdapter
BehSrchLogMsg.Schema.__model__ = BehSrchLogMsg
