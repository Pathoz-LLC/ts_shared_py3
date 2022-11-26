import google.cloud.ndb as ndb
from datetime import date
from typing import Union
from marshmallow import Schema


class BaseNdbModel(ndb.Model):
    """used to standardize my NDB Model methods"""

    # def __init__(self, /, **kwargs) -> None:
    #     super()
    #     self._updateAtts(kwargs)

    def updateViaDictOrSchema(
        self, dictOrSchema: Union[Schema, dict[str, any]]
    ) -> None:
        if isinstance(dictOrSchema, Schema):
            assert dictOrSchema.many in [False, None], "one instance only"
            self._updateAtts(dictOrSchema.dump(many=False))
        elif isinstance(dictOrSchema, dict):
            self._updateAtts(dictOrSchema)
        else:
            raise Exception("invalid argument")

    def _updateAtts(self, kwArgsDict: dict[str, any]):
        for key, value in kwArgsDict.items():
            setattr(self, key, value)

    @staticmethod
    def makeAncestor(userID: str, personID: int) -> ndb.Key:
        assert isinstance(userID, str) and isinstance(
            personID, int
        ), "invalid data for key: {0}:{1} -- {2}:{3}".format(
            userID, type(userID), personID, type(personID)
        )
        # userKey = ndb.Key("User", userID)
        return ndb.Key("User", userID, "Person", personID)

    @staticmethod
    def keyStrFromDate(dt: date) -> str:
        return dt.strftime("%y%m01")

    @classmethod
    def makeKey(cls, userID: str, personID: int, dateObj: date) -> ndb.Key:
        # used as keys for the monthly collection of score records

        # assert isinstance(dateObj, date) and dateObj.day == 1, "Err: %s %s" % (dateObj, dateObj.day)
        # call methods in superclass
        userPersAncestKey = cls.makeAncestor(userID, personID)
        monthStartStr = cls.keyStrFromDate(dateObj)
        return ndb.Key(cls.__name__, monthStartStr, parent=userPersAncestKey)
