from __future__ import annotations
from typing import Dict, Any, Union
from datetime import datetime, date
import json
from typing import ClassVar, Type
from dataclasses import field  # , fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema

#
from .base import BaseApiData
from ..models.user import DbUser
from ..schemas.base import DataClassBaseSchema
from ts_shared_py3.utils.date_conv import (
    dateTime_to_epoch,
    dateTime_from_epoch,
    date_to_epoch,
    date_from_epoch,
)
from ..config.behavior.load_yaml import BehaviorSourceSingleton
from ..enums.activityType import ActivityType
from ..enums.commitLevel import CommitLevel_Display
from ..enums.sex import Sex

behaviorDataShared = BehaviorSourceSingleton()  # read only singleton

DEFAULT_USER_DOB = date(1998, 1, 9)  # if missing

"""_summary_
{"userInfo": {"sex": 1, "province": "", "dob": 1685491200.0}, 
    "contentInfo": {"activityType": 20, "typeSpecificValue": "showedHealthyBoundWithEx",
    "meta": {"code": "showedHealthyBoundWithEx", "parentCode": "respSensitivePos", "text": "had good boundaries with ex",
    "catCode": "respectPos", "pos": "True", "parentDescription": "Good Boundaries", "impact": "0.4444", "catName": "Respect"}},
"dttm": 1687910400.0}
"""


@dataclass(base_schema=DataClassBaseSchema, init=False)
class CommContentInfo(BaseApiData):
    """represents some user action that will feed community news
    args are an enums.ActivityType, a string & optional context obj

    good json encode and decode examples below
    """

    activityType: ActivityType = field(default=0, metadata=dict(required=True))
    typeSpecificValue: Union[str, int, CommitLevel_Display] = field(
        default="", metadata=dict(required=True)
    )
    meta: Dict[str, Any] = field(default_factory=lambda: {})

    def __init__(
        self: CommContentInfo,
        activityType: ActivityType,
        typeSpecificValue: Union[str, int, CommitLevel_Display],
        meta: Dict[str, Any] = None,
    ):
        """typeSpecificValue is one of:
            behCode or catCode
            commitmentLevel

        depending on activityType
        meta is other values as {String:String}
        """
        assert isinstance(activityType, ActivityType), "invalid arg!"
        # print("ActType: {0!r}".format(activityType))
        self.activityType = activityType
        self.typeSpecificValue = typeSpecificValue

        # meta is for when typeSpecific values is more complex
        # like it contains the behavior rec to which this activity applies
        if isinstance(meta, dict):
            self.meta = CommContentInfo._castMetaValsToStr(meta)
        else:
            self.meta = {}  # xtra vals depending upon activityType

        if activityType.hasBehCode:
            # typeSpecificValue should be a behCode
            behNodeAsDict: Dict[str, Any] = behaviorDataShared.getBehAsDict(
                typeSpecificValue
            )
            assert len(behNodeAsDict) > 2, "invalid behavior code %s" % (
                typeSpecificValue
            )
            self.appendMeta(behNodeAsDict)

        elif activityType.appliesToProspect:
            """normally a change in commit-level or phase-dates
            typeSpecificValue contains commitment level or other prospect info?
            """
            pass

    @staticmethod
    def makeWithBehaviorCode(activityType: ActivityType, behCode: str):
        # behavior or feeling or value assessment
        contentInfo = CommContentInfo(activityType, behCode)
        return contentInfo

    @staticmethod
    def makeWithCommitLevel(
        activityType: ActivityType, displayCommitLvlEnum: CommitLevel_Display
    ):
        displayCommitLvlEnum = displayCommitLvlEnum or CommitLevel_Display.random(
            butNot=CommitLevel_Display.BROKENUP
        )
        meta = displayCommitLvlEnum.asDict
        contentInfo = CommContentInfo(
            activityType, displayCommitLvlEnum.code, meta=meta
        )
        return contentInfo

    @staticmethod
    def makeWithIncident(activityType: ActivityType, incident: Incident):
        days: int = incident.overlapDays
        # use meta to store more info if needed
        contentInfo = CommContentInfo(activityType, days, meta=None)
        return contentInfo

    def appendMeta(self: CommContentInfo, meta: Dict[str, Any]):
        """add extra payload depending on activityType"""
        assert isinstance(meta, dict), "invalid arg to appendMeta (should be dict)"
        # client expects all meta vals to be string
        self.meta.update(CommContentInfo._castMetaValsToStr(meta))

    @property
    def commitmentLevel(self: CommContentInfo) -> CommitLevel_Display:
        assert (self.activityType.hasCommitLevel, "invalid activityType")
        return self.typeSpecificValue

    @property
    def isPublic(self: CommContentInfo):
        return self.activityType.isPublic

    @property
    def toDict(self: CommContentInfo):
        return {
            "activityType": int(self.activityType.value),
            "typeSpecificValue": self.typeSpecificValue,
            "meta": self.meta,
        }

    @staticmethod
    def _castMetaValsToStr(meta: Dict[str, Any]):
        # client expects meta dict to be all string vals
        for k, v in meta.items():
            meta[k] = str(v)
        return meta

    @staticmethod
    def fromDict(dct: Dict[str, Any]):
        typ = ActivityType(dct.get("activityType", 1))
        val = dct.get("typeSpecificValue", "")
        meta = dct.get("meta", None)
        return CommContentInfo(typ, val, meta=meta)


@dataclass(base_schema=DataClassBaseSchema)
class CommUserInfo(BaseApiData):
    """
    summarize who did the news event being reported
    """

    sex: Sex = field(default=Sex.UNKNOWN, metadata=dict(required=True))
    province: str = field(default=0, metadata=dict(required=True))
    dob: date = field(default=DEFAULT_USER_DOB, metadata=dict(required=False))

    # def __init__(self, province, sex):
    #     self.province = province
    #     self._sex = sex
    #     self.dob = DEFAULT_USER_DOB

    @staticmethod
    def fromUser(user: DbUser):
        cui = CommUserInfo(user.city, user.sex)
        # assert user.dob, "DOB required"
        if isinstance(user.dob, date):
            cui.dob = user.dob
        return cui

    @property
    def displaySex(self: CommUserInfo):
        return self.sex.toDisplayVal

    @property
    def toDict(self: CommUserInfo):
        return {
            "sex": int(self.sex.value),
            "province": self.province,
            "dob": date_to_epoch(self.dob),
        }

    @staticmethod
    def fromDict(dct: Dict[str, Any]):
        prov = dct.get("province", "_unk")
        sex = Sex(dct.get("sex", 2))
        dob = date_from_epoch(dct.get("dob", 100))
        cui = CommUserInfo(prov, sex, dob)
        return cui


@dataclass(base_schema=DataClassBaseSchema, eq=False)
class CommunityFeedEvent(BaseApiData):
    """
    main news object posted to firebase for community data stream
    """

    userInfo: CommUserInfo = field(metadata=dict(required=True))
    contentInfo: CommContentInfo = field(metadata=dict(required=True))
    dttm: date = field(
        default_factory=lambda: date.today(), metadata=dict(required=True)
    )

    # def __init__(
    #     self: CommunityFeedEvent, userInfo: CommUserInfo, contentInfo: CommContentInfo
    # ):
    #     # all info needed to create a community newsfeed entry
    #     self.userInfo = userInfo  # describe person doing posting
    #     self.contentInfo = contentInfo
    #     self.dttm = datetime.now()  # when did this happen

    @property
    def toDict(self: CommunityFeedEvent) -> Dict[str, Any]:
        # print("toEpoch: %s" % self.dttm)
        # print("Converting CommunityFeedEvent to dict")
        return {
            "userInfo": self.userInfo.toDict,
            "contentInfo": self.contentInfo.toDict,
            "dttm": dateTime_to_epoch(self.dttm),
        }

    @property
    def activityType(self) -> ActivityType:  # what did they do
        return self.contentInfo.activityType

    @property
    def partitionPath(self):  # aka timeWindow in which to store this record
        """return discrete str key for firebase data partition
        may partition further by user-region in a future version
        """
        dt = self.dttm
        # seconds since midnight rounded to xx minute increments
        # print("dt: %s" % dt)
        secondsSinceMidnight = (
            dt - dt.replace(hour=0, minute=0, second=0, microsecond=0)
        ).total_seconds()
        # print("secondsSinceMidnight %s" % secondsSinceMidnight)
        xMinsInSecs = 20 * 60
        roundToEvenXMins = int(
            secondsSinceMidnight - (secondsSinceMidnight % xMinsInSecs)
        )
        rootPath = "{0}-{1}-{2}-{3}".format("usa", dt.year, dt.month, dt.day)
        return "/commNews/{0}/{1}".format(rootPath, str(roundToEvenXMins))

    @property
    def toJson(self: CommunityFeedEvent) -> str:
        return json.dumps(self.toDict)

    @staticmethod
    def fromJson(data):
        return json.loads(data, cls=CommFeedDecoder)

    def __eq__(self: CommunityFeedEvent, other: CommunityFeedEvent):
        """for comparison using encode/decode tests"""
        if isinstance(other, CommunityFeedEvent):
            return (
                self.userInfo.province == other.userInfo.province
                and self.contentInfo.activityType == other.contentInfo.activityType
                and self.contentInfo.typeSpecificValue
                == other.contentInfo.typeSpecificValue
            )
        return False


# class CommFeedEncoder(json.JSONEncoder):
#     """convert a CommunityFeedEvent instance to a dict for JSON"""

#     def default(self, cfe):
#         if isinstance(cfe, CommunityFeedEvent):
#             return cfe.toDict
#         else:
#             super(CommFeedEncoder, self).default(cfe)


class CommFeedDecoder(json.JSONDecoder):
    """convert Json str into CommunityFeedEvent & return"""

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self: CommFeedDecoder, dct: Dict[str, Any]):
        if "contentInfo" not in dct:
            return dct
        userInfoDct = dct.get("userInfo")
        contentInfoDct = dct.get("contentInfo")
        if userInfoDct is not None and contentInfoDct is not None:
            userInfo = CommUserInfo.fromDict(userInfoDct)
            ctxInfo = CommContentInfo.fromDict(contentInfoDct)
            cf = CommunityFeedEvent(userInfo, ctxInfo)
            cf.dttm = dateTime_from_epoch(dct.get("dttm"))
            return cf
        return dct
