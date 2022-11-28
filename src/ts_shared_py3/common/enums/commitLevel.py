from __future__ import annotations
from typing import Optional
from enum import IntEnum, unique
import random

#
# from google.cloud.ndb import msgprop

# from protorpc import messages
from .activityType import ActivityType

# from common.schemas.tracking import CommitLvlApiMsg, DevotionLevelListMessage

# even tho biz logic is driven from LogicCommitLvl, since client uses
# display vals, the public api to this module is via DisplayCommitLvl
# from common.enums.commitLevel import DisplayCommitLvl, LogicCommitLvl, NdbCommitLvlProp


_CommitLevelMasterDict = None  # key'd by code
_DevotionLevelListMessage = None


@unique
class LogicCommitLvl(IntEnum):
    """governs simplified logic for various DisplayCommitLvl
    dialog & incidents are driven by these values, not the DisplayCommitLvl
    """

    PREDATING = 0
    SEPARATED = 1
    NONEXCLUSIVE = 2
    EXCLUSIVE = 3

    def __eq__(self, other) -> bool:
        # handle both int and object cases
        if isinstance(other, LogicCommitLvl):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    @property
    def code(self) -> str:
        return self.name

    @property
    def isSeparated(self) -> bool:
        return self.value < 2

    @property
    def isExclusive(self) -> bool:
        return self.value == 3


@unique
class DisplayCommitLvl(IntEnum):
    """DisplayCommitLvl of user to prospect
    perhaps add PREDATING for future features?
    make all uppercase
    """

    BROKENUP = 0
    CASUAL = 1
    NONEXCLUSIVE = 2
    EXCLUSIVE_AS = 3  # assumed
    EXCLUSIVE_MA = 4  # mutually agreed

    def __eq__(self, other) -> bool:
        # handle both int and object cases
        if isinstance(other, DisplayCommitLvl):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def pointsFromDeltaToCurrent(self, currentPhase) -> int:
        # gap width between CL indicates how big the change
        if self == currentPhase:
            return 0  # no change
        elif currentPhase == DisplayCommitLvl.BROKENUP:
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
    def code(self) -> str:
        return self.name

    @property
    def displayVal(self) -> str:
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
    def iconName(self) -> str:
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
    def logic(self) -> LogicCommitLvl:
        val = self.value
        if val == 0:
            return LogicCommitLvl.SEPARATED
        elif val == 1:
            return LogicCommitLvl.NONEXCLUSIVE
        elif val == 2:
            return LogicCommitLvl.NONEXCLUSIVE
        elif val == 3:
            return LogicCommitLvl.EXCLUSIVE
        elif val == 4:
            return LogicCommitLvl.EXCLUSIVE
        else:
            return LogicCommitLvl.EXCLUSIVE

    @property
    def isExclusive(self) -> bool:
        return self.logic.isExclusive

    @property
    def isSeparated(self) -> bool:
        return self.logic.isSeparated

    # @property
    # def asApiMsg(self):
    #     raise Exception("missing schema CommitLvlApiMsg", "??")
    #     return CommitLvlApiMsg(
    #         displayCode=self.code,
    #         logicCode=self.logic.code,
    #         iconName=self.iconName,
    #         displayValue=self.displayVal,
    # )

    @property
    def asDict(self) -> map[str, str]:
        return dict(
            code=self.code,
            displayVal=self.displayVal,
            iconName=self.iconName,
            logicCode=self.logic.code,
        )

    # methods

    def isIncreaseFrom(self, prior) -> bool:
        # assert isinstance(prior, DisplayCommitLvl), "invalid arg"
        return self.value >= prior.value

    def newsTypeFromCommitLvlDelta(self, priorCl) -> Optional[ActivityType]:
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
    def masterList() -> list[DisplayCommitLvl]:
        # order by depth of commitment:   apart <---> exclusive
        return [
            DisplayCommitLvl.BROKENUP,
            DisplayCommitLvl.CASUAL,
            DisplayCommitLvl.NONEXCLUSIVE,
            DisplayCommitLvl.EXCLUSIVE_AS,
            DisplayCommitLvl.EXCLUSIVE_MA,
        ]

    @staticmethod
    def orderedListCodes() -> list[str]:
        # highest index is max commitment
        return [cl.name for cl in DisplayCommitLvl.masterList()]

    @staticmethod
    def fromStr(str) -> DisplayCommitLvl:
        # init instance from api msg value
        # should handle str or int
        if isinstance(str, (int, float)):
            return DisplayCommitLvl(int(str))
        upStr = str.upper()
        return DisplayCommitLvl[upStr]

    @staticmethod
    def default() -> DisplayCommitLvl:
        return DisplayCommitLvl.CASUAL

    # @staticmethod
    # def commitLvlListAsApiMsg():
    #     # value returned by client API
    #     global _DevotionLevelListMessage
    #     if _DevotionLevelListMessage is None:
    #         _DevotionLevelListMessage = DisplayCommitLvl._buildClientMsgList()
    #     return _DevotionLevelListMessage

    @staticmethod
    def typeCount() -> int:
        return 5  # len(DisplayCommitLvl.masterList())

    @staticmethod
    def masterDict() -> map[str, DisplayCommitLvl]:
        # key'd by code
        global _CommitLevelMasterDict
        if _CommitLevelMasterDict is None:
            for rec in DisplayCommitLvl.masterList():
                _CommitLevelMasterDict[rec.code] = rec
        return _CommitLevelMasterDict

    @staticmethod
    def logicClSeparated() -> LogicCommitLvl:
        return LogicCommitLvl.SEPARATED

    #
    @staticmethod
    def random(butNot: DisplayCommitLvl = None) -> DisplayCommitLvl:
        if butNot is None:
            butNot = DisplayCommitLvl.BROKENUP
        val: int = random.randint(0, 4)
        while val == butNot:
            val = random.randint(0, 4)
        return DisplayCommitLvl(val)

    # @staticmethod
    # def _buildClientMsgList():
    #     raise Exception("missing schema DevotionLevelListMessage", "??")
    #     msg = DevotionLevelListMessage()
    #     for cl in DisplayCommitLvl.masterList():
    #         # dl = CommitLvlApiMsg(displayCode=cl.code, logicCode=cl.logic.code
    #         #                      , displayValue=cl.displayVal, iconName=cl.iconName)
    #         msg.items.append(cl.asApiMsg)
    #     return msg

    # protorpc translators below
    # @staticmethod
    # def to_field(Model, property, count):
    #     # convert NdbCommitLvlProp to integer msg field
    #     raise Exception("missing messages.IntegerField", "??")
    #     return messages.IntegerField(count, repeated=property._repeated)

    # @staticmethod
    # def to_message(Model, property, field, value):
    #     return value.value  # value arg is DisplayCommitLvl obj

    # @staticmethod
    # def to_model(Message, property, field, value):
    #     from common.enums.commitLevel import DisplayCommitLvl

    #     return DisplayCommitLvl(value)


# class NdbCommitLvlProp(msgprop.EnumProperty):
#     def _validate(self, value):
#         if isinstance(value, (int)):
#             return DisplayCommitLvl(value)
#         elif isinstance(value, (bytes, str)):
#             return DisplayCommitLvl(int(value))
#         elif not isinstance(value, DisplayCommitLvl):
#             raise TypeError(
#                 "expected DisplayCommitLvl, int, str or unicd, got %s" % repr(value)
#             )

#     def _to_base_type(self, sx):
#         # convert DisplayCommitLvl to int
#         if isinstance(sx, int):
#             return sx
#         return int(sx.value)

#     def _from_base_type(self, value):
#         return DisplayCommitLvl(value)  # return DisplayCommitLvl
