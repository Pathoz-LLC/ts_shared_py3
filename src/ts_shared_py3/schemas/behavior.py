from __future__ import annotations

#
from marshmallow_dataclass import add_schema

# #
# from .base import NdbBaseSchema
# from .tracking import TrackingPayloadMessage
from ..api_data_classes.behavior import *

"""
    from common.schemas.behavior import *


"""

BehaviorKeysMessageSchema = BehaviorKeysMessage.Schema()

# class BehaviorKeysMessage(NdbBaseSchema):
#     surveyId = fields.Integer(default=2)
#     personId = fields.Integer(default=0, required=True)
#     priorMonthsToLoad = fields.Integer(default=0)

BehaviorStatsFilterMessageSchema = BehaviorStatsFilterMessage.Schema()

# class BehaviorStatsFilterMessage(NdbBaseSchema):
#     behaviorCode = fields.String(required=True)
#     state = fields.String(default="")
#     zipCode = fields.String(default="")
#     lat = fields.Float(default=0.0)
#     lon = fields.Float(default=0.0)


# BehaviorStatsRequestMessage = BehaviorStatsRequestMessage.Schema()

# BehaviorRowMsg = model_message(Entry, exclude=('addDateTime', 'modifyDateTime') )

BehaviorRowMsgSchema = BehaviorRowMsg.Schema()

# class BehaviorRowMsg(NdbBaseSchema):
#     behaviorCode = fields.String(required=True)
#     feelingStrength = fields.Integer(default=0)  # 0-4
#     significanceStrength = fields.Integer(default=0)  # NIU
#     comments = fields.String(default="")
#     lat = fields.Float(default=0.0)
#     lon = fields.Float(default=0.0)
#     shareDetails = fields.String(default="")
#     surveyId = fields.Integer(default=2)
#     personId = fields.Integer(default=0, required=True)
#     # Occur SHOULD allow time component
#     occurDateTime = fields.Float()
#     behaviorId = fields.Integer(default=-1)
#     # used to find same rec upon update/replace
#     positive = fields.Boolean(default=False)
#     categoryCode = fields.String(default="general")
#     # origOccurDateTime = fields.Integer(11)  # used to find same rec upon update/replace


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

BehaviorHistoryMessageSchema = BehaviorHistoryMessage.Schema()

# class BehaviorHistoryMessage(NdbBaseSchema):
#     items = fields.List(BehaviorRowMsg)
#     firstLogDtTm = fields.Float()  # as epoch
#     lastLogDtTm = fields.Float()
#     beganDatingDate = fields.Date(required=True)
#     endedDatingDate = fields.Date(required=True)


# new behavior entries summary logic below
# 11/20/17
StatsAndMetricsMsgSchema = StatsAndMetricsMsg.Schema()
# class StatsAndMetricsMsg(NdbBaseSchema):
#     influenceSummary = fields.String(default="")
#     communicationScore = fields.Float(default=0.0)
#     trustScore = fields.Float(default=0.0)
#     respectScore = fields.Float(default=0.0)
#     lifestyleScore = fields.Float(default=0.0)
#     overallScore = fields.Float(default=0.0)
#     feelingsScore = fields.Float(default=0.0)
#     maleReportCount = fields.Integer(default=0)
#     femaleReportCount = fields.Integer(default=0)


BehEntryWrapperMessageSchema = BehEntryWrapperMessage.Schema()

# class BehEntryWrapperMessage(NdbBaseSchema):
#     """also used to include phases/intervals in the list of beh-entries"""

#     behaviorCode = fields.String(default="", required=True)
#     feelingStrength = fields.Integer(default=0, required=True)
#     longitude = fields.Float(default=0.0)
#     comments = fields.String(default="")
#     shareDetails = fields.String(default="", required=True)
#     occurDateTime = fields.Float()  # as Epoch
#     addDateTime = fields.Float()
#     modifyDateTime = fields.Float()
#     behaviorText = fields.String(default="")
#     isPositive = fields.Boolean(default=True)
#     keywords = fields.String(default="")
#     oppBehaviorCode = fields.String(default="")
#     oppBehaviorText = fields.String(default="")
#     parentCat = fields.String(default="")
#     rootCat = fields.String(default="")
#     parentCatLabel = fields.String(default="")
#     rootCatLabel = fields.String(default="")
#     personName = fields.String(default="", required=True)
#     latitude = fields.Float(default=0.0)
#     commRiskScore = fields.Float(default=0.0)
#     # dont really need rowType currently because rootCat == commitLevel in "cl" case
#     rowType = fields.String(default="beh")  # or cl (commitLevel)
#     # when rowType == cl, then only fields in use are: behaviorCode, shareDetails, occurDateTime
#     # stats = fields.MessageField(StatsAndMetricsMsg, 21)

BehaviorLogSummaryMessageSchema = BehaviorLogSummaryMessage.Schema()
# class BehaviorLogSummaryMessage(NdbBaseSchema):
#     persId = fields.Integer(default=0, required=True)
#     persName = fields.String(default="", required=True)
#     persCurRelStatus = fields.String(default="CASUAL")  # enums.DisplayCommitLvl
#     firstEntryDttm = fields.Float(required=True)  # as epoch
#     lastEntryDttm = fields.Float(required=True)
#     beganDatingDt = fields.Date(required=True)
#     endedDatingDt = fields.Date(required=True)
#     count = fields.Integer(default=0, required=True)
#     entries = fields.List(BehEntryWrapperMessage)
#     phaseHistory = fields.List(TrackingPayloadMessage)


BehaviorSearchTermMsgSchema = BehaviorSearchTermMsg.Schema()
# class BehaviorSearchTermMsg(NdbBaseSchema):
#     userId = fields.String(required=True)
#     searchPhrase = fields.String(required=True)
#     failed = fields.Boolean(default=False)


# full behavior list
BehOrCatMsgSchema = BehOrCatMsg.Schema()
# class BehOrCatMsg(NdbBaseSchema):
#     # embedded in FullBehaviorListMsg
#     code = fields.String(required=True, default="")
#     parentCode = fields.String(required=True, default="")
#     catCode = fields.String(required=True, default="")
#     oppositeCode = fields.String(default="")
#     text = fields.String(required=True, default="")
#     catDescription = fields.String(required=True, default="")

#     isCategory = fields.Boolean(required=True, default=False)
#     isPositive = fields.Boolean(required=True, default=False)
#     sort = fields.Integer(required=True, default=100)
#     keywords = fields.String(required=True, default="")


NodeListMsgSchema = NodeListMsg.Schema()
# class NodeListMsg(NdbBaseSchema):
#     # embedded in FullBehaviorListMsg
#     code = fields.String(required=True, default="")
#     children = fields.String(repeated=True)

FullBehaviorListMsgSchema = FullBehaviorListMsg.Schema()
# class FullBehaviorListMsg(NdbBaseSchema):
#     # top level msg returned to client
#     masterList = fields.List(BehOrCatMsg)
#     topCategoryCodes = fields.List(fields.Str)
#     graph = fields.List(NodeListMsg)


# return list of NEGATIVE top level category codes
CatCodeTextMsgSchema = CatCodeTextMsg.Schema()
# class CatCodeTextMsg(NdbBaseSchema):
#     # embedded in FullBehaviorListMsg
#     code = fields.String(required=True, default="")
#     name = fields.String(required=True, default="")
#     # how many ??'s left unanswered
#     answerCount = fields.Integer(required=True, default=0)
#     availCount = fields.Integer(required=True, default=10)
#     # perhaps we should reset availCount each time they add a prospect??
#     iconName = fields.String(required=True, default="")
#     pos = fields.Boolean(required=True, default=False)

TopCategoriesMsgSchema = TopCategoriesMsg.Schema()
# class TopCategoriesMsg(NdbBaseSchema):
#     # list for client
#     items = fields.List(CatCodeTextMsg)


# global stats about behavior

BehStatMsgSchema = BehStatMsg.Schema()
# class BehStatMsg(NdbBaseSchema):
#     # embedded in VoteTypeMsg
#     totCount = fields.Integer(required=True, default=0)
#     slotCounts = fields.Integer(repeated=True)


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


VoteTypeMsgSchema = VoteTypeMsg.Schema()
# class VoteTypeMsg(NdbBaseSchema):
#     # embedded in BehVoteStatsMsg
#     feeling = fields.Nested(BehStatMsg, required=True)
#     concern = fields.Nested(BehStatMsg, required=True)
#     frequency = fields.Nested(BehStatMsg, required=True)


# VoteTypeMsgAdapterSchema = VoteTypeMsgAdapter.Schema()
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


BehVoteStatsMsgSchema = BehVoteStatsMsg.Schema()
# class BehVoteStatsMsg(NdbBaseSchema):
#     behaviorCode = fields.String(required=True)
#     female = fields.Nested(VoteTypeMsg, required=True)
#     male = fields.Nested(VoteTypeMsg, required=True)
#     unknown = fields.Nested(VoteTypeMsg, required=True)
#     categoryName = fields.String(required=True, default="")


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


BehSrchLogMsgSchema = BehSrchLogMsg.Schema()
# class BehSrchLogMsg(NdbBaseSchema):
#     searchStr = fields.String(default="", required=True)
#     foundCount = fields.Integer(default=0, required=True)
#     # behCode ultimately Selected is for future
#     behCodeSelected = fields.String(default="")
