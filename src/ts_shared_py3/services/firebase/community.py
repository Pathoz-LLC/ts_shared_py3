import json
from datetime import datetime, date
from common.utils.date_conv import (
    dateTime_to_epoch,
    dateTime_from_epoch,
    date_to_epoch,
    date_from_epoch,
)
from ..models.behavior import BehaviorSourceSingleton
from ..enums.activityType import ActivityType
from ..enums.sex import Sex

behaviorDataShared = BehaviorSourceSingleton()  # read only singleton

DEFAULT_USER_DOB = date(1998, 1, 9)  # if missing


class CommContentInfo(object):
    """represents some user action that will feed community news
    args are an enums.ActivityType, a string & optional context obj

    good json encode and decode examples below
    """

    @staticmethod
    def makeWithBehaviorCode(activityType, behCode):
        # behavior or feeling or value assessment
        contentInfo = CommContentInfo(activityType, behCode)
        return contentInfo

    @staticmethod
    def makeWithCommitLevel(activityType, displayCommitLvlEnum):
        meta = displayCommitLvlEnum.asDict
        contentInfo = CommContentInfo(
            activityType, displayCommitLvlEnum.code, meta=meta
        )
        return contentInfo

    @staticmethod
    def makeWithIncident(activityType, incident):
        days = incident.overlapDays
        # use meta to store more info if needed
        contentInfo = CommContentInfo(activityType, days, meta=None)
        return contentInfo

    def __init__(self, activityType, typeSpecificValue, meta=None):
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
            behNodeAsDict = behaviorDataShared.getBehAsDict(typeSpecificValue)
            assert len(behNodeAsDict) > 2, "invalid behavior code %s" % (
                typeSpecificValue
            )
            self.appendMeta(behNodeAsDict)

        elif activityType.appliesToProspect:
            """normally a change in commit-level or phase-dates
            typeSpecificValue contains commitment level or other prospect info?
            """
            pass

    def appendMeta(self, meta):
        """add extra payload depending on activityType"""
        assert isinstance(meta, dict), "invalid arg to appendMeta (should be dict)"
        # client expects all meta vals to be string
        self.meta.update(CommContentInfo._castMetaValsToStr(meta))

    @property
    def commitmentLevel(self):
        return self.typeSpecificValue

    @property
    def isPublic(self):
        return self.activityType.isPublic

    @property
    def toDict(self):
        return {
            "activityType": int(self.activityType.value),
            "typeSpecificValue": self.typeSpecificValue,
            "meta": self.meta,
        }

    @staticmethod
    def _castMetaValsToStr(meta):
        # client expects meta dict to be all string vals
        for k, v in meta.iteritems():
            meta[k] = str(v)
        return meta

    @staticmethod
    def fromDict(dct):
        typ = ActivityType(dct.get("activityType", 1))
        val = dct.get("typeSpecificValue", "")
        meta = dct.get("meta", None)
        return CommContentInfo(typ, val, meta=meta)


class CommUserInfo(object):
    """
    summarize who did the news event being reported
    """

    def __init__(self, province, sex):
        self.province = province
        self._sex = sex
        self.dob = DEFAULT_USER_DOB

    @staticmethod
    def fromUser(user):
        cui = CommUserInfo(user.city, user.sex)
        # assert user.dob, "DOB required"
        if isinstance(user.dob, date):
            cui.dob = user.dob
        return cui

    @property
    def displaySex(self):
        return self._sex.toDisplayVal

    @property
    def toDict(self):
        return {
            "sex": int(self._sex.value),
            "province": self.province,
            "dob": date_to_epoch(self.dob),
        }

    @staticmethod
    def fromDict(dct):
        prov = dct.get("province", "_unk")
        sex = Sex(dct.get("sex", "2"))
        cui = CommUserInfo(prov, sex)
        cui.dob = date_from_epoch(dct.get("dob", 100))
        return cui


class CommunityFeedEvent(object):
    """
    main news object posted to firebase for community data stream
    """

    def __init__(self, userInfo, contentInfo):
        # all info needed to create a community newsfeed entry
        self.userInfo = userInfo  # describe person doing posting
        self.contentInfo = contentInfo
        self.dttm = datetime.now()  # when did this happen

    @property
    def toDict(self):
        # print("toEpoch: %s" % self.dttm)
        # print("Converting CommunityFeedEvent to dict")
        return {
            "userInfo": self.userInfo.toDict,
            "contentInfo": self.contentInfo.toDict,
            "dttm": dateTime_to_epoch(self.dttm),
        }

    @property
    def activityType(self):  # what did they do
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
    def asJson(self):
        return json.dumps(self, cls=CommFeedEncoder)

    @staticmethod
    def fromJson(data):
        return json.loads(data, cls=CommFeedDecoder)

    def __eq__(self, other):
        """for comparison using encode/decode tests"""
        if isinstance(other, CommunityFeedEvent):
            return (
                self.userInfo.province == other.userInfo.province
                and self.contentInfo.activityType == other.contentInfo.activityType
                and self.contentInfo.typeSpecificValue
                == other.contentInfo.typeSpecificValue
            )
        return False


class CommFeedEncoder(json.JSONEncoder):
    """convert a CommunityFeedEvent instance to a dict for JSON"""

    def default(self, cfe):
        if isinstance(cfe, CommunityFeedEvent):
            return cfe.toDict
        else:
            super(CommFeedEncoder, self).default(cfe)


class CommFeedDecoder(json.JSONDecoder):
    """convert Json str into CommunityFeedEvent & return"""

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
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
