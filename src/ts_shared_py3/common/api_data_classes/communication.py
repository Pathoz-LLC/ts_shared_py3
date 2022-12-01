from datetime import date
from typing import ClassVar, Type
from dataclasses import field  # , fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema

from .base import BaseApiData
from ...common.schemas.base import NdbBaseSchema


@dataclass(base_schema=NdbBaseSchema)
class CommStatsMsg(BaseApiData):
    # stats for each time period
    startDtTm: date = field()
    endDtTm: date = field()
    # count of total msgs I've sent in this period
    myMsgCount: int = field(default=0, required=True)
    theirMsgCount: int = field(default=0, required=True)
    # Wpm == avg words per msg
    myAvgWpmCount: int = field(default=0, required=True)
    theirAvgWpmCount: int = field(default=0, required=True)
    # LTR = avg length time to respond in minutes
    myAvgLtr: int = field(default=0, required=True)
    theirAvgLtr: int = field(default=0, required=False)
    # initiate = starting convo after x (eg 12) hours
    myInitiateCount: int = field(default=0, required=True)
    theirInitiateCount: int = field(default=0, required=False)
    # ended = # of times person stopped responding for x (eg 12) hrs
    myEndedCount: int = field(default=0, required=True)
    theirEndedCount: int = field(default=0, required=True)
    # drinkHrsStart = # of times person initiates msgs after drinking hrs
    myDrinkHrsStartCount: int = field(default=0, required=True)
    theirDrinkHrsStartCount: int = field(default=0, required=True)
    # overall score based on all stats
    myOverallScore: int = field(default=50, required=True)
    theirOverallScore: int = field(default=50, required=True)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class CommStatsListMsg(BaseApiData):
    periodStats: list[CommStatsMsg] = []
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class CommunicationEventMsg(BaseApiData):
    fromUser: bool = field(default=False, required=True)
    sentDttm: date = field()
    wordCount: int = field(default=0, required=True)
    text: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class CommunicationRawTranscriptMsg(BaseApiData):
    # raw msg transcript data
    persId: int = field(default=0, required=True)
    startDtTm: date = field()
    endDtTm: date = field()
    messages: list[CommunicationEventMsg] = []
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class CommunicationPrefsMsg(BaseApiData):
    # prefs
    allowTextAnalyss: bool = field(default=False, required=True)
    makeTextAnnon: bool = field(default=False, required=True)
    pathToMsgDb: str = field(default="")
    dataHarvestSchedule: int = field(default=0, required=True)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class PhoneNumMsg(BaseApiData):
    #
    phoneNum: str = field(default="")
    monitorStatus: str = field(default="")
    personId: int = field(default=0, required=True)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class FollowedPhoneNums(BaseApiData):
    #
    items: list[PhoneNumMsg] = []

    #
    Schema: ClassVar[Type[Schema]] = Schema
