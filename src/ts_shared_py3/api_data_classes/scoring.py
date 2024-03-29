from datetime import date
from dataclasses import field
from typing import ClassVar, Type, Optional
from marshmallow import Schema
from marshmallow_dataclass import dataclass

#
from .base import BaseApiData
from ..schemas.base import DataClassBaseSchema


@dataclass(base_schema=DataClassBaseSchema)
class RecalcScoringStart(BaseApiData):
    userId: str = field(default="0")
    persId: int = field(default=0)

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class RequRelationshipOverviewData(BaseApiData):
    """
    used by client to request score data
    request returns a ProspectScoreData
    """

    queryStartDt: date = None
    queryEndDt: date = None

    userId: str = field(default="0")
    persId: int = field(default=0)
    persName: str = field(default="")
    # Deprecated
    # monthsBackFromNow & prior flds are deprecated (use queryStart and queryEnd above)
    monthsBackFromNow: int = field(default=3, metadata=dict(validate=lambda: 123))
    priorUserScore: float = field(default=0.5)
    priorCommunityScore: int = field(default=0.5)

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class OneWindowScoreData(BaseApiData):
    """
    A single point on the relationship trends graph
    there is a wrapper for this obj at:
    common/scoring/calc.OneScoreMsgWrapper
    """

    pointNum: int = field(default=0)  # pointNum = day_num
    centerDtOfWindow: date = None
    # avg of scores below
    # score = field(default=0.0, )
    # detailed scores
    userAppScore: float = field(default=0.0)
    # flockScore = field(5, default=0.0, )
    # communityScore = field(6, default=0.0, )
    # communicationScore = field(7, default=0.0, )
    communityScore: float = field(default=0.0)
    # isEmptyPeriod means this day (centerDtOfWindow) is a
    # copy of a prior days scores because user made no entries
    # it's a filler row to keep the line flat; area is NOT tapable on graph UI
    isEmptyPeriod: bool = field(default=False)

    Schema: ClassVar[Type[Schema]] = Schema

    # # fields below are NIU
    # hasCommunicationStats = field(default=False)
    # # overview totals for this bucket/window
    # behaviorEntryCountPos = field(default=0)
    # behaviorEntryCountNeg = field(default=0)
    # feelingEntryCountPos = field(default=0)
    # feelingEntryCountNeg = field(default=0)
    # valuesAssessCounts = field(default=0)


@dataclass(base_schema=DataClassBaseSchema)
class CurPhaseRelStateData(BaseApiData):
    """includes text descriptions of each score
    to go with CurPhaseRelState Message

    previous phases are just points on graph & dont currently have
    accompanying score descriptions
    """

    scores: OneWindowScoreData = field()
    # score descriptions
    userAppScoreDescrip: str = field(default="Derived from your entries")
    # flockScoreDescrip = ma.fields.String(3, default='')
    # communityScoreDescrip = ma.fields.String(4, default='Derived from community votes')
    communityScoreDescrip: str = field(default="Derived from the TS Algorithm")
    # communicationScoreDescrip = ma.fields.String(6, default='')

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class ScoreMetadataData(BaseApiData):
    """
    carries dates of the scores being returned
    """

    firstLogDate: date = field()
    lastLogDate: date = field()
    beganDatingDate: date = field()
    endedDatingDate: date = field()
    queryStartDt: date = field()
    queryEndDt: date = field()

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class ProspectScoreData(BaseApiData):
    # ProspectScoreMsg; rolls together current score with prior-period scores
    curPeriodDetails: CurPhaseRelStateData = field()
    priorPeriodScores: list[OneWindowScoreData] = field()
    metadata: ScoreMetadataData = field()  # field()

    persId: int = field(default=0)
    # priorPeriodScores are the buckets/windows of consolidated scores (ie a point on graph)
    incidentCount: int = field(default=0)
    redFlagBits: int = field(default=0)

    Schema: ClassVar[Type[Schema]] = Schema

    # bucketWidthDays: int = field(default=0)


RequRelationshipOverviewData.Schema.__model__ = RequRelationshipOverviewData
OneWindowScoreData.Schema.__model__ = OneWindowScoreData
CurPhaseRelStateData.Schema.__model__ = CurPhaseRelStateData
ScoreMetadataData.Schema.__model__ = ScoreMetadataData
ProspectScoreData.Schema.__model__ = ProspectScoreData
RecalcScoringStart.Schema.__model__ = RecalcScoringStart
