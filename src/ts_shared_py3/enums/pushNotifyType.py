from __future__ import annotations
from marshmallow import fields, ValidationError
from enum import IntEnum, unique
from google.cloud.ndb import model

"""

"""


@unique
class NotifyType(IntEnum):
    """type of push notification

    NOTE:  keep all() up to date
    """

    INCIDENT = 0  # overlap has occurred
    CHAT_REQUEST = 1  # another user has reached out
    CHAT_MSG_RECEIVED = 2  # another user has responded
    # 3-5 below stem from batch jobs
    CL_DECREMENT_WARN = (
        3  # Commitment level decrement warning; after x days of no activity on Prospect
    )
    CL_DECREMENT_DONE = 4  # Commitment level decrement done
    VALS_QUEST_AVAIL = 5  # new values questions are available
    # from user entry of new prospect
    PROSPECT_VALS_MISSING = 6  # new prospect added; update values frequency for them
    SCORING_DONE = 7  # scoring has been completed

    @staticmethod
    def all() -> list[NotifyType]:
        return [
            NotifyType.INCIDENT,
            NotifyType.CHAT_REQUEST,
            NotifyType.CHAT_MSG_RECEIVED,
            NotifyType.CL_DECREMENT_WARN,
            NotifyType.CL_DECREMENT_DONE,
            NotifyType.VALS_QUEST_AVAIL,
            NotifyType.PROSPECT_VALS_MISSING,
            NotifyType.SCORING_DONE,
        ]

    @staticmethod
    def allAsStr() -> list[str]:
        return [t.name for t in NotifyType.all()]

    def getMockData(self) -> dict[str, str]:
        # for testing push
        rf = self.requiredFields
        d = dict()
        for fldNm in rf:
            d[fldNm] = "someTestString"
        if self.isDecrementCl:
            d["newClCode"] = "BROKENUP"
        return d

    @property
    def requiredFields(self) -> list[str]:
        # userID & type are reserved for ALL payloads
        # do not use them here or they will get replaced
        if self == NotifyType.INCIDENT:
            return ["otherUserID", "personID", "overlapCount"]
        elif self in [NotifyType.CHAT_REQUEST, NotifyType.CHAT_MSG_RECEIVED]:
            return ["otherUserID", "personID"]
        elif self.isDecrementCl:
            return ["personID", "newClCode"]

        elif self in [NotifyType.PROSPECT_VALS_MISSING, NotifyType.SCORING_DONE]:
            return ["personID"]
        else:
            return []

    @property
    def isDecrementCl(self) -> bool:
        return self in [NotifyType.CL_DECREMENT_WARN, NotifyType.CL_DECREMENT_DONE]

    @property
    def title(self) -> str:
        if self == NotifyType.INCIDENT:
            return "Overlap Incident occurred"
        elif self == NotifyType.CHAT_REQUEST:
            return "Anonymous Chat request"
        elif self == NotifyType.CHAT_MSG_RECEIVED:
            return "Anonymous Chat response"
        elif self == NotifyType.CL_DECREMENT_WARN:
            return "Prospect Status request"
        elif self == NotifyType.CL_DECREMENT_DONE:
            return "Prospect Status updated"
        elif self == NotifyType.VALS_QUEST_AVAIL:
            return "Survey Questions reminder"
        elif self == NotifyType.PROSPECT_VALS_MISSING:
            return "Update Survey for new prospects"
        elif self == NotifyType.SCORING_DONE:
            return "Rescore completed"

        else:
            return self.name + " Title_"

    @property
    def subtitle(self):
        """subtitle does not apply to android & niu on IOS"""
        return ""  # self.name + " subtitle"

    @property
    def body(self) -> str:
        if self == NotifyType.INCIDENT:
            # substitute prospect nickname
            return "A TS user entered dates that overlap your relationship with {0}"
        elif self == NotifyType.CHAT_REQUEST:
            # substitute prospect nickname
            return "A TS user is requesting a chat with you about {0}"
        elif self == NotifyType.CHAT_MSG_RECEIVED:
            # req 2 args;  substitute prospect nickname plus user ID
            return "A chat response about {0} is available from TS user {1}"
        elif self == NotifyType.CL_DECREMENT_WARN:
            # substitute prospect nickname
            return "TS suspects you & {0} are 'Broken Up'. If not, update your status"
        elif self == NotifyType.CL_DECREMENT_DONE:
            # substitute prospect nickname
            return "TS has changed your status with {0} to 'Broken Up'"

        elif self == NotifyType.VALS_QUEST_AVAIL:
            # no template value; value varies depending upon user type
            return "Answer more questions to improve prospect score accuracy."
            # return 'As a free TS user, you have 5 new survey questions available.'
        elif self == NotifyType.PROSPECT_VALS_MISSING:
            # substitute prospect nickname
            return "You've added a new prospect! Update your survey for {0}."
        elif self == NotifyType.SCORING_DONE:
            # substitute prospect nickname
            return "Scoring Calculations completed for {0}."
        else:
            return self.name + " Body_"

    @property
    def bodyIsConstant(self) -> bool:
        # no template value needed for these types
        return self in [NotifyType.VALS_QUEST_AVAIL]

    @property
    def bodyIncludesProspectName(self) -> bool:
        # NotifyType.CHAT_MSG_RECEIVED is special (2 args)
        return not self.bodyIsConstant

    @property
    def hasCategory(self) -> bool:
        return self in [
            NotifyType.CL_DECREMENT_WARN,
            NotifyType.CL_DECREMENT_DONE,
        ]  # , NotifyType.CL_DECREMENT_DONE

    @property
    def color(self):
        #  Color of the notification icon expressed in #rrggbb form (optional).
        return None

    @property
    def badge(self) -> int:
        return 1

    @property
    def sound(self) -> str | None:
        return None

    @property
    def tag(self):
        return None

    @property
    def icon(self):
        return None

    @property
    def contentAvail(self) -> bool:
        return False

    @property
    def topic(self) -> str:
        return self.name

    @property
    def category(self) -> str | None:
        # category allows client side selection UI to appear
        # if not self.hasCategory:
        #     return None

        if self in [
            NotifyType.CL_DECREMENT_WARN,
            NotifyType.CL_DECREMENT_DONE,
        ]:  #
            return "commitmentLevel"

        return None


class NdbNotifyTypeProp(model.IntegerProperty):
    def _validate(self, value: int):
        if isinstance(value, (int)):
            return NotifyType(value)
        elif isinstance(value, (bytes, str)):
            return NotifyType(int(value))
        elif not isinstance(value, NotifyType):
            raise TypeError(
                "expected NotifyType, int, str or unicd, got %s" % repr(value)
            )

    def _to_base_type(self, sx: NotifyType):
        # convert NotifyType to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return NotifyType(value)


class NotifyTypeSerializedMa(fields.Enum):
    """"""

    def _serialize(
        self: NotifyTypeSerializedMa, value: NotifyType, attr, obj, **kwargs
    ):
        if value is None:
            return ""
        return value.name

    def _deserialize(self: NotifyTypeSerializedMa, value: str, attr, data, **kwargs):
        try:
            return NotifyType[value]
        except ValueError as error:
            raise ValidationError("") from error

    # def dump_default(self: NotifyTypeSerializedMa) -> NotifyType:
    #     return NotifyType.CHAT_MSG_RECEIVED
