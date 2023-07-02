from __future__ import annotations
from typing import Dict, Any, Union, ClassVar, Type
from datetime import datetime, date
import json
from marshmallow_dataclass import dataclass, field_for_schema, add_schema
from marshmallow import Schema
from marshmallow import fields as ma_fields

#
from ts_shared_py3.utils.date_conv import (
    dateTime_to_epoch,
    dateTime_from_epoch,
    date_to_epoch,
    date_from_epoch,
)

#
from .base import BaseApiData
from ..schemas.base import DataClassBaseSchema
from ..models.user import DbUser
from ..models.incident import Incident
from ..enums.activityType import ActivityType
from ..enums.commitLevel import CommitLevel_Display
from ..enums.sex import Sex
from ..config.behavior.load_yaml import BehaviorSourceSingleton

behaviorDataShared = BehaviorSourceSingleton()  # read only singleton

DEFAULT_USER_DOB = date(1998, 1, 9)  # if missing

# field_for_schema = 123

"""_summary_
{"userInfo": {"sex": 1, "province": "", "dob": 1685491200.0}, 
    "contentInfo": {"activityType": 20, "typeSpecificValue": "showedHealthyBoundWithEx",
    "meta": {"code": "showedHealthyBoundWithEx", "parentCode": "respSensitivePos", "text": "had good boundaries with ex",
    "catCode": "respectPos", "pos": "True", "parentDescription": "Good Boundaries", "impact": "0.4444", "catName": "Respect"}},
"dttm": 1687910400.0}
"""


@dataclass(base_schema=DataClassBaseSchema)
class CommUserInfo(BaseApiData):
    """
    summarize who did the news event being reported
    """

    province: str = field_for_schema(
        str, metadata=dict(marshmallow_field=ma_fields.Str(), required=True)
    )  # default="",
    sexInt: int = field_for_schema(
        int,
        # default=1,  # Sex.UNKNOWN.value
        metadata=dict(marshmallow_field=ma_fields.Int(), required=True),
    )
    dob: date = field_for_schema(
        date,
        # default=DEFAULT_USER_DOB,
        metadata=dict(marshmallow_field=ma_fields.Date(), required=False),
    )

    Schema: ClassVar[Type[Schema]] = DataClassBaseSchema

    @property
    def sex(self: CommUserInfo) -> Sex:
        return Sex(self.sexInt)

    @staticmethod
    def fromUser(user: DbUser) -> CommUserInfo:
        cui = CommUserInfo(user.city, user.sex, user.dob.date())
        # assert user.dob, "DOB required"
        # if isinstance(user.dob, date):
        #     cui.dob = user.dob
        return cui

    @property
    def displaySex(self: CommUserInfo) -> str:
        return self.sex.toDisplayVal

    @property
    def toDict(self: CommUserInfo) -> Dict:
        return {
            "sex": self.sexInt,
            "province": self.province,
            "dob": date_to_epoch(self.dob),
        }

    @staticmethod
    def fromDict(dct: Dict[str, Any]) -> CommUserInfo:
        prov = dct.get("province", "_unk")
        sex = Sex(dct.get("sex", 2))
        dob = date_from_epoch(dct.get("dob", 100000.0))
        cui = CommUserInfo(prov, sex, dob)
        return cui


@dataclass(base_schema=DataClassBaseSchema)
class CommContentInfo(BaseApiData):
    """represents some user action that will feed community news
    args are an enums.ActivityType, a string & optional context obj

    good json encode and decode examples below
    """

    activityTypeInt: int = field_for_schema(
        int,
        # default=ActivityType.FEELING_RECORDED.value,
        metadata=dict(marshmallow_field=ma_fields.Int(), required=True),
    )
    # custom types based on activityTypeInt
    aTypSpecValStr: str = field_for_schema(
        str,
        default="",
        metadata=dict(marshmallow_field=ma_fields.Str(), required=False),
    )
    aTypSpecValInt: int = field_for_schema(
        int, default=0, metadata=dict(marshmallow_field=ma_fields.Int(), required=False)
    )

    meta: Dict[str, Any] = field_for_schema(
        dict,
        metadata=dict(
            marshmallow_field=ma_fields.Dict(
                keys=ma_fields.Str(), values=ma_fields.Inferred()
            ),
            default_factory=lambda x: {},
        ),
    )

    Schema: ClassVar[Type[Schema]] = DataClassBaseSchema

    @property
    def activityType(self: CommContentInfo) -> ActivityType:
        return ActivityType(self.activityTypeInt)

    @property
    def commitmentLevel(self: CommContentInfo) -> CommitLevel_Display:
        assert self.activityType.hasCommitLevel, "invalid activityType"
        return CommitLevel_Display(self.aTypSpecValInt)

    @property
    def lenIncidentInDays(self: CommContentInfo) -> int:
        assert self.activityType.isIncident, "invalid activityType"
        return self.aTypSpecValInt

    def __post_init__(self: CommContentInfo) -> None:
        """typeSpecificValue is one of:
            behCode or catCode
            commitmentLevel

        depending on activityType
        meta is other values as {String:String}

                activityType: ActivityType,
        typeSpecificValue: Union[str, int, CommitLevel_Display],
        meta: Dict[str, Any] = None,
        """
        assert isinstance(self.activityType, ActivityType), "invalid arg!"
        # print("ActType: {0!r}".format(activityType))

        # meta is for when typeSpecific values is more complex
        # like it contains the behavior rec to which this activity applies
        if isinstance(self.meta, dict):
            self._castMetaValsToStr()
        else:
            self.meta = {}  # xtra vals depending upon activityType

        if self.activityType.hasBehCode:
            # typeSpecificValue should be a behCode
            behNodeAsDict: Dict[str, Any] = behaviorDataShared.getBehAsDict(
                self.aTypSpecValStr
            )
            assert len(behNodeAsDict) > 2, "invalid behavior code {0}".format(
                self.aTypSpecValStr
            )
            self.appendMeta(behNodeAsDict)

        elif self.activityType.appliesToProspect:
            """normally a change in commit-level or phase-dates
            typeSpecificValue contains commitment level or other prospect info?
            """
            pass

    @staticmethod
    def makeWithBehaviorCode(
        activityType: ActivityType, behCode: str
    ) -> CommContentInfo:
        # behavior or feeling or value assessment
        contentInfo = CommContentInfo(activityType, behCode, 0)
        return contentInfo

    @staticmethod
    def makeWithCommitLevel(
        activityType: ActivityType, displayCommitLvlEnum: CommitLevel_Display
    ) -> CommContentInfo:
        displayCommitLvlEnum = displayCommitLvlEnum or CommitLevel_Display.random(
            butNot=CommitLevel_Display.BROKENUP
        )
        meta = displayCommitLvlEnum.asDict
        contentInfo = CommContentInfo(
            activityType, displayCommitLvlEnum.code, 0, meta=meta
        )
        return contentInfo

    @staticmethod
    def makeWithIncident(
        activityType: ActivityType, incident: Incident
    ) -> CommContentInfo:
        days: int = int(incident.overlapDays)
        # use meta to store more info if needed
        contentInfo = CommContentInfo(activityType, "", days, meta=None)
        return contentInfo

    def appendMeta(self: CommContentInfo, meta: Dict[str, Any]) -> None:
        """add extra payload depending on activityType"""
        assert isinstance(meta, dict), "invalid arg to appendMeta (should be dict)"
        # client expects all meta vals to be string
        self.meta.update(self._castMetaValsToStr(meta))

    @property
    def typeValueDynamicAsStr(self: CommContentInfo) -> str:
        if self.activityType.hasCommitLevel:
            return self.commitmentLevel.code
        elif self.activityType.hasBehCode:
            return self.aTypSpecValStr
        elif self.activityType.appliesToValues:
            return self.aTypSpecValStr
        elif self.activityType.isIncident:
            # probably an incident report showing overlap days
            return str(self.aTypSpecValInt)
        else:
            return self.aTypSpecValStr

    @property
    def isPublic(self: CommContentInfo) -> bool:
        return self.activityType.isPublic

    @property
    def toDict(self: CommContentInfo) -> Dict:
        return {
            "activityType": self.activityTypeInt,
            "typeSpecificValue": self.typeValueDynamicAsStr,
            "meta": self.meta,
        }

    def _castMetaValsToStr(self: CommContentInfo) -> None:
        # client expects meta dict to be all string vals
        for k, v in self.meta.items():
            self.meta[k] = str(v)

    @staticmethod
    def fromDict(dct: Dict[str, Any]) -> CommContentInfo:
        typInt: int = dct.get("activityType", 1)
        typ = ActivityType(typInt)

        val: str = dct.get("typeSpecificValue", "")
        valStr = val if typ.hasBehCode or typ.appliesToProspect else None
        valInt = int(val) if typ.isIncident or typ.hasCommitLevel else None
        meta = dct.get("meta", None)
        return CommContentInfo(typInt, valStr, valInt, meta=meta)


@dataclass(base_schema=DataClassBaseSchema, eq=False)
class CommunityFeedEvent(BaseApiData):
    """
    main news object posted to firebase for community data stream
    """

    userInfo: CommUserInfo = field_for_schema(
        CommUserInfo,
        metadata=dict(
            required=True
        ),  # marshmallow_field=ma_fields.Nested(CommUserInfo.Schema),
    )
    contentInfo: CommContentInfo = field_for_schema(
        CommContentInfo,
        metadata=dict(
            required=True
        ),  # marshmallow_field=ma_fields.Nested(CommContentInfo.Schema),
    )
    dttm: datetime = field_for_schema(
        datetime,
        metadata=dict(
            marshmallow_field=ma_fields.DateTime(),
            required=True,
            default_factory=lambda x: datetime.now(),
        ),
    )

    Schema: ClassVar[Type[DataClassBaseSchema]] = DataClassBaseSchema

    @property
    def toDict(self: CommunityFeedEvent) -> Dict[str, Union[Dict[str, Any], int]]:
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
    def partitionPath(
        self: CommunityFeedEvent,
    ) -> str:  # aka timeWindow in which to store this record
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
    def fromJson(data) -> CommunityFeedEvent:
        return json.loads(data, cls=CommFeedDecoder)

    def __eq__(self: CommunityFeedEvent, other: CommunityFeedEvent) -> bool:
        """for comparison using encode/decode tests"""
        if isinstance(other, CommunityFeedEvent):
            return (
                self.userInfo.province == other.userInfo.province
                and self.contentInfo.activityType == other.contentInfo.activityType
                and self.contentInfo.aTypSpecValStr == other.contentInfo.aTypSpecValStr
            )
        return False


class CommFeedDecoder(json.JSONDecoder):
    """convert Json str into CommunityFeedEvent & return"""

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self: CommFeedDecoder, dct: Dict[str, Any]):
        if "contentInfo" not in dct:
            return dct
        userInfoDct: Dict[str, Any] = dct.get("userInfo")
        contentInfoDct: Dict[str, Any] = dct.get("contentInfo")
        if userInfoDct is not None and contentInfoDct is not None:
            userInfo = CommUserInfo.fromDict(userInfoDct)
            ctxInfo = CommContentInfo.fromDict(contentInfoDct)
            cf = CommunityFeedEvent(userInfo, ctxInfo)
            cf.dttm = dateTime_from_epoch(dct.get("dttm"))
            return cf
        return dct


CommUserInfo.Schema.__model__ = CommUserInfo
CommContentInfo.Schema.__model__ = CommContentInfo
CommunityFeedEvent.Schema.__model__ = CommunityFeedEvent

# class CommFeedEncoder(json.JSONEncoder):
#     """convert a CommunityFeedEvent instance to a dict for JSON"""

#     def default(self, cfe):
#         if isinstance(cfe, CommunityFeedEvent):
#             return cfe.toDict
#         else:
#             super(CommFeedEncoder, self).default(cfe)
