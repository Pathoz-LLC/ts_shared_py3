from datetime import date
from typing import ClassVar, Type
from dataclasses import field  # , fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema

from .base import BaseApiData
from ..schemas.base import DataClassBaseSchema


@dataclass(base_schema=DataClassBaseSchema)
class CommStatsMsg(BaseApiData):
    # stats for each time period
    startDtTm: date = field()
    endDtTm: date = field()
    # count of total msgs I've sent in this period
    myMsgCount: int = field(default=0, metadata=dict(required=True))
    theirMsgCount: int = field(default=0, metadata=dict(required=True))
    # Wpm == avg words per msg
    myAvgWpmCount: int = field(default=0, metadata=dict(required=True))
    theirAvgWpmCount: int = field(default=0, metadata=dict(required=True))
    # LTR = avg length time to respond in minutes
    myAvgLtr: int = field(default=0, metadata=dict(required=True))
    theirAvgLtr: int = field(default=0, metadata=dict(required=False))
    # initiate = starting convo after x (eg 12) hours
    myInitiateCount: int = field(default=0, metadata=dict(required=True))
    theirInitiateCount: int = field(default=0, metadata=dict(required=False))
    # ended = # of times person stopped responding for x (eg 12) hrs
    myEndedCount: int = field(default=0, metadata=dict(required=True))
    theirEndedCount: int = field(default=0, metadata=dict(required=True))
    # drinkHrsStart = # of times person initiates msgs after drinking hrs
    myDrinkHrsStartCount: int = field(default=0, metadata=dict(required=True))
    theirDrinkHrsStartCount: int = field(default=0, metadata=dict(required=True))
    # overall score based on all stats
    myOverallScore: int = field(default=50, metadata=dict(required=True))
    theirOverallScore: int = field(default=50, metadata=dict(required=True))
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class CommStatsListMsg(BaseApiData):
    periodStats: list[CommStatsMsg] = field(default_factory=lambda: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class CommunicationEventMsg(BaseApiData):
    sentDttm: date = field()
    fromUser: bool = field(default=False, metadata=dict(required=True))
    wordCount: int = field(default=0, metadata=dict(required=True))
    text: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class CommunicationRawTranscriptMsg(BaseApiData):
    # raw msg transcript data
    startDtTm: date = field()
    endDtTm: date = field()
    persId: int = field(default=0, metadata=dict(required=True))
    messages: list[CommunicationEventMsg] = field(default_factory=lambda: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class CommunicationPrefsMsg(BaseApiData):
    # prefs
    allowTextAnalyss: bool = field(default=False, metadata=dict(required=True))
    makeTextAnnon: bool = field(default=False, metadata=dict(required=True))
    pathToMsgDb: str = field(default="")
    dataHarvestSchedule: int = field(default=0, metadata=dict(required=True))
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PhoneNumMsg(BaseApiData):
    #
    phoneNum: str = field(default="")
    monitorStatus: str = field(default="")
    personId: int = field(default=0, metadata=dict(required=True))
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class FollowedPhoneNums(BaseApiData):
    #
    items: list[PhoneNumMsg] = field(default_factory=lambda: [])

    #
    Schema: ClassVar[Type[Schema]] = Schema


CommStatsMsg.Schema.__model__ = CommStatsMsg
CommStatsListMsg.Schema.__model__ = CommStatsListMsg
CommunicationEventMsg.Schema.__model__ = CommunicationEventMsg
CommunicationRawTranscriptMsg.Schema.__model__ = CommunicationRawTranscriptMsg

CommunicationPrefsMsg.Schema.__model__ = CommunicationPrefsMsg
PhoneNumMsg.Schema.__model__ = PhoneNumMsg
FollowedPhoneNums.Schema.__model__ = FollowedPhoneNums
