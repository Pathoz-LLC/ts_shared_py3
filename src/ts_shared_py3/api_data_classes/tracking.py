from datetime import date
from typing import ClassVar, Type
from dataclasses import field
from marshmallow_dataclass import dataclass

from marshmallow import Schema, fields

from .base import BaseApiData
from ..schemas.base import DataClassBaseSchema
from ..enums.sex import Sex, SexSerializedMa
from ..enums.commitLevel import CommitLevel_Display


@dataclass(base_schema=DataClassBaseSchema)
class CommitLvlApiMsg(BaseApiData):
    # full descrip of a commitment level payload
    displayCode: str = field(default="")
    logicCode: str = field(default="")
    iconName: str = field(default="")
    displayValue: str = field(default="")

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class CommitLvlUpdateMsg(BaseApiData):
    """used to update CommitLvl for in-active users"""

    startDate: date = field()
    persId: int = field(default=0, metadata=dict(required=True))
    userId: int = field(default=0, metadata=dict(required=True))
    commitLvlDisplayCd: CommitLevel_Display = field(
        default=CommitLevel_Display.CASUAL, metadata={"enum": CommitLevel_Display}
    )
    # notificationId serves for authentication b4 changing data
    notificationId: str = field(default="")

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class IntervalMessage(BaseApiData):
    """used for add update delete
    oldStartDate is key for update/delete
    """

    # oldStartDate is key to find which row edited or deleted; ignored for Add
    oldStartDate: date = field()
    startDate: date = field()
    endDate: date = field()
    commitLvl: CommitLvlApiMsg = field()
    persId: int = field(default=0, metadata=dict(required=True))

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class TrackingPayloadMsgDc(BaseApiData):
    # the std msg to update a tracking record
    persId: int = field(default=0, metadata=dict(required=True))
    enabled: bool = field(default=True)
    # repeating intervals:
    phases: list[IntervalMessage] = field(default_factory=lambda: [])

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class IncidentRowMessage(BaseApiData):
    """ """

    earliestOverlapDate: date = field()
    addDateTime: date = field()
    modDateTime: date = field()

    userInterval: IntervalMessage = field()
    reportingUserInterval: IntervalMessage = field()

    incidentId: int = field(default=0, metadata=dict(required=True))
    userTruthOpinion: int = field(default=0, metadata=dict(required=True))
    evidenceStatus: int = field(default=0, metadata=dict(required=True))

    # details: reportingUser is the OTHER user
    reportingUserId: str = field(default="")

    overlapDays: int = field(default=0, metadata=dict(required=True))
    userIntervalRowNum: int = field(default=0, metadata=dict(required=True))

    # housekeeping
    # if reporting user changes their dates, store old vals here
    repUserIntervalReviseHistory: str = field(default="")

    reportingUserIntervalRowNum: int = field(default=0)
    # reportingUserSex: Sex = SexSerializedMa(Sex, default=Sex.UNKNOWN)
    reportingUserSex: Sex = field(default=Sex.UNKNOWN, metadata={"enum": Sex})
    # a sequential user ID starting from 1 to keep privacy
    reportingUserDisplayID: int = field(default=0, metadata=dict(required=True))
    # how many distinct incidents has this user had with prospect
    reportingUserIncdSeqNum: int = field(default=0, metadata=dict(required=True))

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class IncidentDetailsMessage(BaseApiData):
    asOfDate: date = field()
    persId: int = field(default=0, metadata=dict(required=True))
    userOverlapCount: int = field(default=0, metadata=dict(required=True))
    items: list[IncidentRowMessage] = field(default_factory=lambda: [])

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class IncidentTruthMessage(BaseApiData):
    incidentId: int = field(default=0, metadata=dict(required=True))
    incidentTruthVote: int = field(
        default=0, metadata=dict(required=True)
    )  # 0 means not seen; 1-4 = true->false

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class DevotionLevelListMessage(BaseApiData):
    items: list[CommitLvlApiMsg] = field(default_factory=lambda: [])

    Schema: ClassVar[Type[Schema]] = Schema


CommitLvlApiMsg.Schema.__model__ = CommitLvlApiMsg

CommitLvlUpdateMsg.Schema.__model__ = CommitLvlUpdateMsg

IntervalMessage.Schema.__model__ = IntervalMessage

TrackingPayloadMsgDc.Schema.__model__ = TrackingPayloadMsgDc

IncidentRowMessage.Schema.__model__ = IncidentRowMessage

IncidentDetailsMessage.Schema.__model__ = IncidentDetailsMessage

IncidentTruthMessage.Schema.__model__ = IncidentTruthMessage
DevotionLevelListMessage.Schema.__model__ = DevotionLevelListMessage
