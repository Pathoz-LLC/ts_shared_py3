from __future__ import annotations
from datetime import datetime, date, time, timedelta
from typing import Union
from datetime import datetime, timedelta
import google.cloud.ndb as ndb

# circular import
from ts_shared_py3.api_data_classes.person import RedFlagReportDc

from ..enums.redFlag import RedFlagType, NdbRedFlagProp
from .baseNdb_model import BaseNdbModel
from .person import Person
from .user import DbUser


class RedFlagReport(BaseNdbModel):  # ndb.model.Expando
    """red flag report types
            case REVENGE = 0
            case DEEP_FAKE = 1
            case PHYSICAL_ABUSE = 2
            case DATERAPE = 3
    vals in Person.redFlagBits on Person & Person local are respectively:  1,2,4,8

    status vals are:  ( 0=submitted, 1=proven, 2=rescinded, 3=overriden)
    """

    userKey = ndb.KeyProperty(DbUser, required=True, indexed=True)
    flagType = NdbRedFlagProp(
        required=True, default=RedFlagType.NEVERSET, indexed=False
    )
    status = ndb.IntegerProperty(indexed=True, default=0)

    comment = ndb.TextProperty(indexed=False)  # any notes or comments
    url = ndb.TextProperty(indexed=False)  # evidence location
    beganDateTime = ndb.DateTimeProperty(indexed=False)  # first time they did this
    addDateTime = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    modifyDateTime = ndb.DateTimeProperty(indexed=False)

    @property
    def personID(self: RedFlagReport):
        persKey = self.key.parent().parent()
        return persKey.integer_id()

    def toMsg(self: RedFlagReport):
        from ..api_data_classes.person import RedFlagReportDc

        return RedFlagReportDc(
            userId=self.userKey.string_id(),
            personId=self.personID,
            flagType=self.flagType.value,
            comment=self.comment,
            url=self.url,
            beganDateTime=self.beganDateTime,
        )

    @staticmethod
    def fromMsg(msg: RedFlagReportDc, userId: str):
        now = datetime.now()
        beganDt = msg.beganDateTime if msg.beganDateTime else now
        beganDt = beganDt.replace(tzinfo=None)
        rfr = RedFlagReport(
            userKey=ndb.Key(DbUser, userId),
            flagType=msg.flagType,
            comment=msg.comment,
            addDateTime=now,
            modifyDateTime=now,
            url=msg.url,
            beganDateTime=beganDt,
        )
        rfr.key = RedFlagReport._makeKey(userId, msg.personId, msg.flagType)
        return rfr

    @staticmethod
    def _makeKey(userID: str, personID: int, flagType: RedFlagType):
        # this structure prevents duplicates & makes deletion/recindtion a simple operation
        flagTypeKey = RedFlagReport.getAncestorKey(personID, flagType)
        return ndb.Key(RedFlagReport, userID, parent=flagTypeKey)

    @staticmethod
    def getAncestorKey(personID: int, flagType: Union[RedFlagType, int]):
        # this structure prevents duplicates & makes deletion/recindtion a simple operation
        # personID = long(personID)  # convert to 64bit
        if isinstance(flagType, RedFlagType):
            flagType = flagType.value
        persKey = ndb.Key(Person, personID)  # top ancestor; makes loading all easy
        return ndb.Key("FlagType", flagType, parent=persKey)
