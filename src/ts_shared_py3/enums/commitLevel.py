from __future__ import annotations
from typing import Optional
from enum import IntEnum, unique
from marshmallow import fields, ValidationError
from marshmallow_dataclass import NewType
from google.cloud.ndb import model
import random

#
from .activityType import ActivityType


# next line causes circular import;  leave commented
# from ..api_data_classes.tracking import CommitLvlApiMsg

# even tho biz logic is driven from LogicCommitLvl, since client uses
# display vals, the public api to this module is via CommitLevel_Display
# from ts_shared_py3.enums.commitLevel import (
#     CommitLevel_Display,
#     LogicCommitLvl,
#     NdbCommitLvlProp,
# )


# DO NOT change init vals below; and dont import CommitLvlApiMsg
_CommitLevelMasterDict: map[str, CommitLevel_Display] = None  # key'd by code
_CommitLevelListMessage: list[CommitLvlApiMsg] = None


@unique
class CommitLevel_Logic(IntEnum):
    """governs simplified logic for various CommitLevel_Display
    dialog & incidents are driven by these values, not the CommitLevel_Display
    """

    PREDATING = 0
    SEPARATED = 1
    NONEXCLUSIVE = 2
    EXCLUSIVE = 3

    def __eq__(self: CommitLevel_Logic, other: CommitLevel_Logic) -> bool:
        # handle both int and object cases
        if isinstance(other, CommitLevel_Logic):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    @property
    def code(self: CommitLevel_Logic) -> str:
        return self.name

    @property
    def isSeparated(self: CommitLevel_Logic) -> bool:
        return self.value < 2

    @property
    def isExclusive(self: CommitLevel_Logic) -> bool:
        return self.value == 3


@unique
class CommitLevel_Display(IntEnum):
    """CommitLevel_Display of user to prospect
    perhaps add PREDATING for future features?
    make all uppercase
    """

    BROKENUP = 0
    CASUAL = 1
    NONEXCLUSIVE = 2
    EXCLUSIVE_AS = 3  # assumed
    EXCLUSIVE_MA = 4  # mutually agreed

    def __eq__(self: CommitLevel_Display, other: CommitLevel_Display) -> bool:
        # handle both int and object cases
        if isinstance(other, CommitLevel_Display):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def pointsFromDeltaToCurrent(self: CommitLevel_Display, currentPhase) -> int:
        # gap width between CL indicates how big the change
        if self == currentPhase:
            return 0  # no change
        elif currentPhase == CommitLevel_Display.BROKENUP:
            return -1  # breakup is severe no matter distance from prior CL

        posGap = max(self.value, currentPhase.value) - min(
            self.value, currentPhase.value
        )
        # now convert gap into pos or neg from -1 to 1
        flip = 1 if currentPhase.value > self.value else -1
        return flip * (posGap / 4)

    # @property
    # def asMsg(self):
    #     # from common.messages.tracking import CommitLvlApiMsg
    #     raise Exception("missing schema CommitLvlApiMsg", "??")
    #     return CommitLvlApiMsg(
    #         displayCode=self.code,
    #         logicCode=self.logic.code,
    #         iconName=self.iconName,
    #         displayValue=self.displayVal,
    # )

    @property
    def code(self: CommitLevel_Display) -> str:
        return self.name

    @property
    def displayVal(self: CommitLevel_Display) -> str:
        val = self.value
        if val == 0:
            return "BrokenUp; On a Break"
        elif val == 1:
            return "Casual; Hooking Up"
        elif val == 2:
            return "NonMonogamous; Dating"
        elif val == 3:
            return "Exclusive Assumed"
        elif val == 4:
            return "Exclusive Agreed"
        else:
            return "?Non-Monogamous"

    @property
    def iconName(self: CommitLevel_Display) -> str:
        if self == 0:
            return "cl_brokenUp"
        elif self == 1:
            return "cl_casual"
        elif self == 2:
            return "cl_nonExclusive"
        elif self == 3:
            return "cl_exclusiveAssumed"
        elif self == 4:
            return "cl_exclusiveAgreed"
        else:
            return "cl_nonExclusive"

    @property
    def logic(self: CommitLevel_Display) -> CommitLevel_Logic:
        val = self.value
        if val == 0:
            return CommitLevel_Logic.SEPARATED
        elif val == 1:
            return CommitLevel_Logic.NONEXCLUSIVE
        elif val == 2:
            return CommitLevel_Logic.NONEXCLUSIVE
        elif val == 3:
            return CommitLevel_Logic.EXCLUSIVE
        elif val == 4:
            return CommitLevel_Logic.EXCLUSIVE
        else:
            return CommitLevel_Logic.EXCLUSIVE

    @property
    def isExclusive(self: CommitLevel_Display) -> bool:
        return self.logic.isExclusive

    @property
    def isSeparated(self: CommitLevel_Display) -> bool:
        return self.logic.isSeparated

    @property
    def asApiMsg(self: CommitLevel_Display):  # -> CommitLvlApiMsg:
        # raise Exception("missing schema CommitLvlApiMsg", "??")
        from ..schemas.tracking import CommitLvlApiMsg

        return CommitLvlApiMsg(
            displayCode=self.code,
            logicCode=self.logic.code,
            iconName=self.iconName,
            displayValue=self.displayVal,
        )

    @property
    def asDict(self: CommitLevel_Display) -> map[str, str]:
        return dict(
            code=self.code,
            displayVal=self.displayVal,
            iconName=self.iconName,
            logicCode=self.logic.code,
        )

    # methods

    def isIncreaseFrom(self: CommitLevel_Display, prior: CommitLevel_Display) -> bool:
        # assert isinstance(prior, CommitLevel_Display), "invalid arg"
        return self.value >= prior.value

    def newsTypeFromCommitLvlDelta(
        self: CommitLevel_Display, priorCl: CommitLevel_Display
    ) -> Optional[ActivityType]:
        """self == latest/newest
        priorCL is one right before this latest cl
        return None
        """
        if priorCl is None:
            priorCl = self
        if self.isSeparated:
            return ActivityType.PROSPECT_STATUS_BREAKUP
        elif self.value > priorCl.value:
            return ActivityType.PROSPECT_STATUS_INCREASE
        elif self.value < priorCl.value:
            return ActivityType.PROSPECT_STATUS_DECREASE
        else:  # let caller figure this out (probably date changes)
            None

    # static

    @staticmethod
    def masterList() -> list[CommitLevel_Display]:
        # order by depth of commitment:   apart <---> exclusive
        return [
            CommitLevel_Display.BROKENUP,
            CommitLevel_Display.CASUAL,
            CommitLevel_Display.NONEXCLUSIVE,
            CommitLevel_Display.EXCLUSIVE_AS,
            CommitLevel_Display.EXCLUSIVE_MA,
        ]

    @staticmethod
    def orderedListCodes() -> list[str]:
        # highest index is max commitment
        return [cl.name for cl in CommitLevel_Display.masterList()]

    @staticmethod
    def fromStr(str: str):  # -> CommitLevel_Display:
        # init instance from api msg value
        # should handle str or int
        if isinstance(str, (int, float)):
            return CommitLevel_Display(int(str))
        upStr = str.upper()
        return CommitLevel_Display[upStr]

    @staticmethod
    def default() -> CommitLevel_Display:
        return CommitLevel_Display.CASUAL

    @staticmethod
    def commitLvlListAsApiMsg():
        # value returned by client API
        global _CommitLevelListMessage
        if _CommitLevelListMessage is None:
            _CommitLevelListMessage = CommitLevel_Display._buildClientMsgList()
        return _CommitLevelListMessage

    @staticmethod
    def typeCount() -> int:
        return 5  # len(CommitLevel_Display.masterList())

    @staticmethod
    def masterDict() -> map[str, CommitLevel_Display]:
        # key'd by code
        global _CommitLevelMasterDict
        if _CommitLevelMasterDict is None:
            for rec in CommitLevel_Display.masterList():
                _CommitLevelMasterDict[rec.code] = rec
        return _CommitLevelMasterDict

    @staticmethod
    def logicClSeparated() -> CommitLevel_Logic:
        return CommitLevel_Logic.SEPARATED

    #
    @staticmethod
    def random(butNot: CommitLevel_Display = None) -> CommitLevel_Display:
        if butNot is None:
            butNot = CommitLevel_Display.BROKENUP
        val: int = random.randint(0, 4)
        while val == butNot:
            val = random.randint(0, 4)
        return CommitLevel_Display(val)

    @staticmethod
    def _buildClientMsgList():  # -> list[CommitLvlApiMsg]
        from ..api_data_classes.tracking import (
            CommitLvlApiMsg,
            DevotionLevelListMessage,
        )

        msg: list[CommitLvlApiMsg] = []
        for cl in CommitLevel_Display.masterList():
            apMsg = CommitLvlApiMsg(
                displayCode=cl.code,
                logicCode=cl.logic.code,
                displayValue=cl.displayVal,
                iconName=cl.iconName,
            )
            msg.append(apMsg)
        return msg

    # protorpc translators below
    # @staticmethod
    # def to_field(Model, property, count):
    #     # convert NdbCommitLvlProp to integer msg field
    #     raise Exception("missing messages.IntegerField", "??")
    #     return messages.IntegerField(count, repeated=property._repeated)

    # @staticmethod
    # def to_message(Model, property, field, value):
    #     return value.value  # value arg is CommitLevel_Display obj

    # @staticmethod
    # def to_model(Message, property, field, value):
    #     from common.enums.commitLevel import CommitLevel_Display

    #     return CommitLevel_Display(value)


class NdbCommitLvlProp(model.IntegerProperty):
    def _validate(self, value: int):
        if isinstance(value, (int)):
            return CommitLevel_Display(value)
        elif isinstance(value, (bytes, str)):
            return CommitLevel_Display(int(value))
        elif not isinstance(value, CommitLevel_Display):
            raise TypeError(
                "expected CommitLevel_Display, int, str or unicd, got %s" % repr(value)
            )

    def _to_base_type(self, sx: CommitLevel_Display):
        # convert CommitLevel_Display to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return CommitLevel_Display(value)  # return CommitLevel_Display

    # @property
    # def asEnum(self: NdbCommitLvlProp):
    #     return self._from_base_type(self.value)


class CommitLvlSerializedMa(fields.Enum):
    """Field that serializes to a string of sex name"""

    def _serialize(
        self: CommitLvlSerializedMa, value: CommitLevel_Display, attr, obj, **kwargs
    ) -> str:
        if value is None:
            return ""
        return value.name

    def _deserialize(
        self: CommitLvlSerializedMa, value: str, attr, data, **kwargs
    ) -> CommitLevel_Display:
        try:
            return CommitLevel_Display[value]
        except ValueError as error:
            raise ValidationError("") from error

    # def dump_default(self: CommitLvlSerializedMa) -> CommitLevel_Display:
    #     return CommitLevel_Display.NONEXCLUSIVE


# CommitLvlSerializedMsg = NewType("CommitLvlSerialized", str, _CommitLvlSerialized)
