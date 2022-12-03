from datetime import date
from typing import ClassVar, Type
from dataclasses import field  # , fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ..schemas.base import NdbBaseSchema
from ..enums.sex import Sex


@dataclass(base_schema=NdbBaseSchema)
class CommitLvlApiMsg(BaseApiData):
    # full descrip of a commitment level payload
    displayCode: str = field(default="")
    logicCode: str = field(default="")
    iconName: str = field(default="")
    displayValue: str = field(default="")


@dataclass(base_schema=NdbBaseSchema)
class CommitLvlUpdateMsg(BaseApiData):
    """used to update CommitLvl for in-active users"""

    persId: int = field(default=0, required=True)
    userId: int = field(default=0, required=True)
    commitLvlDisplayCd: str = field(default="")
    startDate: date = field()
    # notificationId serves for authentication b4 changing data
    notificationId: str = field(default="")


@dataclass(base_schema=NdbBaseSchema)
class IntervalMessage(BaseApiData):
    """used for add update delete
    oldStartDate is key for update/delete
    """

    persId: int = field(default=0, required=True)
    # oldStartDate is key to find which row edited or deleted; ignored for Add
    oldStartDate: date = field()
    startDate: date = field()
    endDate: date = field()
    commitLvl: CommitLvlApiMsg = field()


@dataclass(base_schema=NdbBaseSchema)
class TrackingPayloadMessage(BaseApiData):
    # the std msg to update a tracking record
    persId: int = field(default=0, required=True)
    enabled: bool = field(default=True)
    # repeating intervals:
    phases: list[IntervalMessage] = []


@dataclass(base_schema=NdbBaseSchema)
class IncidentRowMessage(BaseApiData):
    """ """

    incidentId: int = field(default=0, required=True)
    userTruthOpinion: int = field(default=0, required=True)
    evidenceStatus: int = field(default=0, required=True)

    # details: reportingUser is the OTHER user
    reportingUserId: str = field(default="")
    earliestOverlapDate: date = field()

    overlapDays: int = field(default=0, required=True)
    userIntervalRowNum: int = field(default=0, required=True)
    userInterval: IntervalMessage = None
    reportingUserInterval: IntervalMessage = None

    # housekeeping
    # if reporting user changes their dates, store old vals here
    repUserIntervalReviseHistory: str = field(default="")
    addDateTime: date = field()
    modDateTime: date = field()
    reportingUserIntervalRowNum: int = field(default=0, required=False)
    reportingUserSex: Sex = field(default=0, required=True)
    # a sequential user ID starting from 1 to keep privacy
    reportingUserDisplayID: int = field(default=0, required=True)
    # how many distinct incidents has this user had with prospect
    reportingUserIncdSeqNum: int = field(default=0, required=True)


@dataclass(base_schema=NdbBaseSchema)
class IncidentDetailsMessage(BaseApiData):
    persId: int = field(default=0, required=True)
    asOfDate: date = field()
    items: list[IncidentRowMessage] = []
    userOverlapCount: int = field(default=0, required=True)


@dataclass(base_schema=NdbBaseSchema)
class IncidentTruthMessage(BaseApiData):
    incidentId: int = field(default=0, required=True)
    incidentTruthVote: int = field(
        default=0, required=True
    )  # 0 means not seen; 1-4 = true->false


@dataclass(base_schema=NdbBaseSchema)
class DevotionLevelListMessage(BaseApiData):
    items: list[CommitLvlApiMsg] = []
