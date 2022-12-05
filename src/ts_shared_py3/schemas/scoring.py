from __future__ import annotations
import marshmallow as ma

#
from ..api_data_classes import scoring as DataClasses
from .base import DataClassBaseSchema, NdbBaseSchemaWithKey

"""
the whole job of these schema objects is to define the format/structure
of inbound and outbound (open-api) payloads;
when inbound, (after parse & validation) 
the schema will instantiate a DataClasse object
with required (& default) values populated
"""


class RecalcStartSchema(ma.Schema):
    userId = ma.fields.String(required=True)
    persId = ma.fields.Integer(required=True)


class RequRelationshipOverviewSchema(ma.Schema):
    """
    used by client to send API request data
    also used to decode data sent by client, and then cast inbound
    payload into a msg (DataClasses.RequRelationshipOverviewData) with req vals
    sent data-values stored on the returned RequRelationshipOverviewData
    """

    __model__ = DataClasses.RequRelationshipOverviewData  # override base class

    userId = ma.fields.String(required=True)
    persId = ma.fields.Integer(required=True)
    # if dates are empty, will default to prior 3-4 months of data
    queryStartDt = ma.fields.Date()
    queryEndDt = ma.fields.Date()
    persName = ma.fields.String(default="Prospect")
    # prior scores can be used to create a "changed by xxx" sentence
    priorUserScore = ma.fields.Float(default=0.0)
    priorCommunityScore = ma.fields.Float(default=0.0)
    # monthsBackFromNow deprecated (use queryStart and queryEnd below)
    # monthsBackFromNow = ma.fields.Int(default=3)

    @ma.post_load()
    def _getInstance(
        self: RequRelationshipOverviewSchema, dDict: dict[str, str], **kwargs
    ) -> DataClasses.RequRelationshipOverviewData:
        # construct a DataClasses.RequRelationshipOverviewData() & return
        rec = self.__model__()
        assert isinstance(
            rec, self.__model__
        ), "could not create valid RequRelationshipOverviewData from data sent by RequRelationshipOverviewSchema?"
        rec.updateAttsFromDict(dDict)
        return rec


class OneWindowScoreMsg(DataClassBaseSchema):
    """
    A single point on the relationship trends graph
    there is a wrapper for this obj at:
    common/scoring/calc.OneScoreMsgWrapper

    dump_only=True means sent to client
        not received from client
    """

    __model__ = DataClasses.OneWindowScoreData  # override base class

    pointNum = ma.fields.Int(default=0, required=True)  # pointNum = day_num
    centerDtOfWindow = ma.fields.Date(required=True)
    # avg of scores below
    # score = ma.fields.Float(default=0.0, required=True)
    # detailed scores
    userAppScore = ma.fields.Float(required=True)
    # flockScore = ma.fields.Float(5, default=0.0, required=True)
    # communityScore = ma.fields.Float(6, default=0.0, required=True)
    # communicationScore = ma.fields.Float(7, default=0.0, required=True)
    communityScore = ma.fields.Float(required=True)
    # isEmptyPeriod means this day (centerDtOfWindow) is a
    # interpolated copy of a near days scores, because user made no entries
    # it's a filler row to keep the line flat; area won't be NOT tapable on graph UI
    isEmptyPeriod = ma.fields.Bool(default=False, load_only=True)

    # # fields below are NIU
    # hasCommunicationStats = ma.fields.Bool(default=False)
    # # overview totals for this bucket/window
    # behaviorEntryCountPos = ma.fields.Int(default=0)
    # behaviorEntryCountNeg = ma.fields.Int(default=0)
    # feelingEntryCountPos = ma.fields.Int(default=0)
    # feelingEntryCountNeg = ma.fields.Int(default=0)
    # valuesAssessCounts = ma.fields.Int(default=0)


class CurPhaseRelStateMsg(DataClassBaseSchema):
    """includes text descriptions of each score
    to go with CurPhaseRelState Message

    previous phases are just points on graph & dont currently have
    accompanying score descriptions

    dump_only=True means sent to client
        not received from client
    """

    __model__ = DataClasses.CurPhaseRelStateData  # override base class

    scores = ma.fields.Nested(OneWindowScoreMsg, required=True)
    # score descriptions
    userScoreDescrip = ma.fields.String(default="Derived from the TS Algorithm")
    communityScoreDescrip = ma.fields.String(
        default="Derived from TS Community values assessments"
    )
    # flockScoreDescrip = ma.fields.String(3, default='')
    # communityScoreDescrip = ma.fields.String(4, default='Derived from community votes')
    # communicationScoreDescrip = ma.fields.String(6, default='')


class ScoreMetadataSchema(DataClassBaseSchema):
    """carries dates of the scores being returned
    dump_only=True means sent to client
    not received from client
    """

    __model__ = DataClasses.ScoreMetadataData  # override base class

    firstLogDate = ma.fields.Date(dump_only=True)
    lastLogDate = ma.fields.Date(dump_only=True)
    beganDatingDate = ma.fields.Date(dump_only=True)
    endedDatingDate = ma.fields.Date(dump_only=True)
    queryStartDt = ma.fields.Date(dump_only=True)
    queryEndDt = ma.fields.Date(dump_only=True)


class ProspectScoreSchema(DataClassBaseSchema):
    """full score payload for a given
    user / prospect combination
    when requested by client using:
        api_data_classes.RequRelationshipOverviewData
    """

    __model__ = DataClasses.ProspectScoreData  # override base class

    # ProspectScoreMsg; rolls together current score with prior-period scores
    persId = ma.fields.Int(default=0, required=True)
    curPeriodDetails = ma.fields.Nested(CurPhaseRelStateMsg, required=True)
    # priorPeriodScores are the buckets/windows of consolidated scores (ie a point on graph)
    priorPeriodScores = ma.fields.Nested(OneWindowScoreMsg(many=True))
    incidentCount = ma.fields.Int(default=0, required=True)
    redFlagBits = ma.fields.Int(default=0)
    metadata = ma.fields.Nested(ScoreMetadataSchema, required=True)
    # bucketWidthDays = ma.fields.Int(default=0, required=True)
