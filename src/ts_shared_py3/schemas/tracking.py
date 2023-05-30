from __future__ import annotations
from marshmallow import fields

#
from .base import DataClassBaseSchema


""" this file is NIU for scoring server
    usage:
    from common.schemas.tracking import *

    tracking & intervals
    keep only schema defs in here;  no logic
    converters live on model objects

    chatbot sends list of IntervalMessage at end of dialog
    client sends back: TrackingPayloadMessage with exact same structure
"""


class CommitLvlApiMsgSchema(DataClassBaseSchema):
    # full descrip of a commitment level payload
    displayCode = fields.String()  # UI
    logicCode = fields.String()  # abstract code
    iconName = fields.String()
    displayValue = fields.String()


class CommitLvlUpdateMsgSchema(DataClassBaseSchema):
    """used to update CommitLvl for in-active users"""

    persId = fields.Integer(required=True)
    userId = fields.Integer(required=True)
    commitLvlDisplayCd = fields.String(required=True)
    startDate = fields.Date()
    # notificationId serves for authentication b4 changing data
    notificationId = fields.String(required=True, default="38248")


class IntervalMessageSchema(DataClassBaseSchema):
    """used for add update delete
    oldStartDate is key for update/delete
    """

    persId = fields.Integer(required=True)
    # oldStartDate is key to find which row edited or deleted; ignored for Add
    oldStartDate = fields.Date()
    startDate = fields.Date()
    endDate = fields.Date()
    commitLvl = fields.Nested(CommitLvlApiMsgSchema)


# class IntervalMessageCollection(ApiBaseSchema):
#     pass


# class TrackingPayloadMessageSchema(DataClassBaseSchema):
#     # the std msg to update a tracking record
#     persId = fields.Integer()
#     enabled = fields.Boolean(default=True)
#     # repeating intervals:
#     phases = fields.Nested(IntervalMessage(many=True))


class IncidentRowMessageSchema(DataClassBaseSchema):
    """ """

    incidentId = fields.Integer(required=True)
    userTruthOpinion = fields.Integer()
    evidenceStatus = fields.Integer()

    # details: reportingUser is the OTHER user
    reportingUserId = fields.String()
    earliestOverlapDate = fields.Date()

    overlapDays = fields.Integer()
    userIntervalRowNum = fields.Integer()
    userInterval = fields.Nested(IntervalMessageSchema, repeated=False)
    reportingUserInterval = fields.Nested(IntervalMessageSchema, repeated=False)

    # housekeeping
    # if reporting user changes their dates, store old vals here
    repUserIntervalReviseHistory = fields.String()
    addDateTime = fields.Date()
    modDateTime = fields.Date()
    reportingUserIntervalRowNum = fields.Integer(required=False)
    reportingUserSex = fields.Integer(default=0)
    # a sequential user ID starting from 1 to keep privacy
    reportingUserDisplayID = fields.Integer(default=1)
    # how many distinct incidents has this user had with prospect
    reportingUserIncdSeqNum = fields.Integer(default=1)


class IncidentDetailsMessageSchema(DataClassBaseSchema):
    persId = fields.Integer()
    asOfDate = fields.Date()
    items = fields.Nested(IncidentRowMessageSchema(many=True))
    userOverlapCount = fields.Integer(default=1)


class IncidentTruthMessage(DataClassBaseSchema):
    incidentId = fields.Integer()
    incidentTruthVote = fields.Integer(default=0)  # 0 means not seen; 1-4 = true->false


class DevotionLevelListMessage(DataClassBaseSchema):
    items = fields.Nested(CommitLvlApiMsgSchema(many=True))


# class RelationshipStateOverviewMessage(fields.Message):
#     # Relationship Overview Message
#     persId = fields.Integer( default=0)
#     # scores
#     userConfidenceScore = fields.Integer( default=50)
#     # innerCircleRelationshipScore = fields.Integer( default=50)
#     # anonAdviceRelationshipScore = fields.Integer( default=50)
#     # communityAdviceRelationshipScore = fields.Integer(5, default=50)
#     tsRelationshipScore = fields.Integer(6, default=50)
#     # score descriptions for UI
#     userRelationshipScoreDescrip = fields.String(7, default='Derived from your entries')
#     # innerCircleRelationshipScoreDescrip = fields.String(8, default='')
#     # anonAdviceRelationshipScoreDescrip = fields.String(9, default='')
#     # communityAdviceRelationshipScoreDescrip = fields.String(10, default='Derived from community votes')
#     tsRelationshipScoreDescrip = fields.String(11, default='Derived from the TS Algorithm')
#     haveCommunicationStats = fields.Boolean(12, default=False)
#
#     # counts
#     behaviorEntryCountPos = fields.Integer(13, default=0)
#     behaviorEntryCountNeg = fields.Integer(14, default=0)
#     feelingEntryCountPos = fields.Integer(15, default=0)
#     feelingEntryCountNeg = fields.Integer(16, default=0)
#     quizResponseCount = fields.Integer(17, default=0)
#     incidentCount = fields.Integer(18, default=0)
#     redFlagBits = fields.Integer(19, default=0)


# class SurveyOverviewMessage(fields.Message):
#     persId = fields.Integer( default=0)
#     totalQuestions = fields.Integer( default=0)
#     totalAnswers = fields.Integer( default=0)
#     prospectSpecificAnswers = fields.Integer( default=0)
