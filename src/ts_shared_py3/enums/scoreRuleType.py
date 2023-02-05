from __future__ import annotations
from typing import Callable
from datetime import date
from enum import IntEnum, unique
from collections import namedtuple
from random import randint
from google.cloud.ndb import model

#
from ..enums.alloc import AllocType  # , AllocLookup
from ..enums.commitLevel import CommitLevel_Display

# from .alloc import AllocType
from ..constants import IMPACT_WEIGHT_DECIMALS

VAL_ASSESS_TYPES = []  # SET below to subset of ScoreRuleType when module loads

# behCode yields one of these for each
MinPlusNotchForAppAndCommunity = namedtuple(
    "MinPlusNotchForAppAndCommunity",
    ["appMin", "appNotch", "communityMin", "communityNotch"],
)

StdCalcCallableSig = Callable[[float, float, list[float]], float]


@unique
class ScoreRuleType(IntEnum):
    """governs how scoring engine
    treats these types of entries

    for example, some are repeating (forever)
    or echo x distance into the future

    note:  update allIds() below if you add more
    DO NOT change existing int ID vals w/out fixing properties below

    Note:  sometimes valuesAsses weights can be positive vals
        when frequency == 1 (he never does this)
    TODO:
        this breaks tests --> the compare to the Numbers validation sheet
        update and re-export the numbers sheet to return min pos weight
        for the RECIPROCAL POS behavior
        (right now, I'm returning pos for the NEG behavior)
    """

    # neg-behaviors magnified by impact.yaml & community values
    BEHAVIOR_POSITIVE = 0
    BEHAVIOR_NEGATIVE = 1
    #
    FEELING_POSITIVE = 2
    FEELING_NEGATIVE = 3

    # vals magnified by impact.yaml & community values
    VAL_ASSESS_NEVER = 10
    VAL_ASSESS_LITTLE = 11
    VAL_ASSESS_FREQUENT = 12
    VAL_ASSESS_LOTS = 13

    # ******* start default magnification
    BREAKUP = 20
    INCIDENT = 30
    #
    PROSPECT_STATUS_INCREASE = 40
    PROSPECT_STATUS_DECREASE = 41
    # ******* end default magnification

    # scores from communication assessment
    COMMUNICATION_POSITIVE = 50
    COMMUNICATION_NEGATIVE = 51

    # used when converting ScopedRawScore into InputEntryAdapter
    # not sure why/when I need to do that??
    PRE_SCORED = 999

    @property
    def hasStaticCode(self: ScoreRuleType) -> bool:
        return self in [
            ScoreRuleType.INCIDENT,
            ScoreRuleType.PROSPECT_STATUS_INCREASE,
            ScoreRuleType.PROSPECT_STATUS_DECREASE,
            ScoreRuleType.BREAKUP,
        ]

    @property
    def staticIdCode(self: ScoreRuleType) -> str:
        # simply to normalize recID values for locating recs in testing
        if self == ScoreRuleType.INCIDENT:
            return "cheatedOnMeWhenTempted"
        else:
            return "commitLevelChange"

    @property
    def isPositive(self: ScoreRuleType) -> bool:
        return self in [
            ScoreRuleType.BEHAVIOR_POSITIVE,
            ScoreRuleType.FEELING_POSITIVE,
            ScoreRuleType.PROSPECT_STATUS_INCREASE,
        ]

    @property
    def usesBehaviorStruct(self: ScoreRuleType) -> bool:
        # true if db model is Behavior or Feel Entry (pos or neg)
        return 0 <= self.value <= 3

    @property
    def allocWeightType(self: ScoreRuleType) -> AllocType:
        if self.isBehavior:
            return AllocType.BEHAVIOR
        elif self.isFeeling:
            return AllocType.FEELING
        elif self.isValueAssesment:
            return AllocType.ASSESS
        elif self == ScoreRuleType.INCIDENT:
            return AllocType.INCIDENT
        elif self == ScoreRuleType.BREAKUP:
            # breakup needs SPECIAL alloc type;  do not use isCommitLevelChange
            return AllocType.BREAKUP
        elif self in [
            ScoreRuleType.PROSPECT_STATUS_INCREASE,
            ScoreRuleType.PROSPECT_STATUS_DECREASE,
        ]:
            return AllocType.COMMITCHANGE
        # elif self in [ScoreRuleType.COMMUNICATION_POSITIVE, ScoreRuleType.COMMUNICATION_NEGATIVE]:
        #     return 1    # FIXME
        elif self == ScoreRuleType.PRE_SCORED:
            return AllocType.PRESCORE
        else:
            raise ValueError

    @property
    def sliderRange(self: ScoreRuleType) -> SliderRange:
        if self.isValueAssesment:
            return SliderRange.FOUR
        else:
            return SliderRange.THREE

    @property
    def isValueAssesment(self: ScoreRuleType) -> bool:
        return 10 <= self.value <= 13
        # return self in VAL_ASSESS_TYPES

    @property
    def isBehavior(self: ScoreRuleType) -> bool:
        return 0 <= self.value <= 1
        # return self in [ScoreRuleType.BEHAVIOR_POSITIVE, ScoreRuleType.BEHAVIOR_NEGATIVE]

    @property
    def isFeeling(self: ScoreRuleType) -> bool:
        return 2 <= self.value <= 3
        # return self in [ScoreRuleType.FEELING_POSITIVE, ScoreRuleType.FEELING_NEGATIVE]

    @property
    def isFeelingOrBehavior(self: ScoreRuleType) -> bool:
        return self.isFeeling or self.isBehavior

    @property
    def isCommitLevelChange(self: ScoreRuleType) -> bool:
        # does NOT apply to allocWeights;  includes BREAKUP
        return 40 <= self.value <= 41 or self.value == 20
        # return self in [ScoreRuleType.PROSPECT_STATUS_INCREASE, ScoreRuleType.PROSPECT_STATUS_DECREASE, ScoreRuleType.BREAKUP]

    def minAndNotchForUserAndCommunity(
        self: ScoreRuleType, staticAppImpact: float, stdCommunityHybrid: float
    ) -> MinPlusNotchForAppAndCommunity:
        """pass in Pierce/app/user weight (appImpact)
        or community weight (communityImpact)
        and use those to figure out base
        math vals based on rule type
        converts raw impact vals to hybrids and such based on rule-type
        userImpact == a single user (1 concern vote); only for valuesAssesment

        NOTCH should always have SAME SIGN as impact weight
        """
        rp = IMPACT_WEIGHT_DECIMALS  # roundPrecision == 4
        # stdCommunityHybrid = (communityImpact * 0.700) + (staticAppImpact * 0.300)
        communityImpact = stdCommunityHybrid

        if self.isFeelingOrBehavior:
            # based on 3 position slider
            appNotchSize = ScoreRuleType._getBoundedNotchSizeBySliderScale(
                staticAppImpact, 3.0
            )
            appMin = staticAppImpact - appNotchSize
            communityNotchSize = ScoreRuleType._getBoundedNotchSizeBySliderScale(
                communityImpact, 3.0
            )
            communityMin = stdCommunityHybrid - communityNotchSize
            return MinPlusNotchForAppAndCommunity(
                round(appMin, rp),
                round(appNotchSize, rp),
                round(communityMin, rp),
                round(communityNotchSize, rp),
            )

        # elif self in [ScoreRuleType.FEELING_NEGATIVE, ScoreRuleType.FEELING_POSITIVE]:
        #     return ScoreRuleType._behCalc()

        elif self.isValueAssesment:
            """based on 4 position slider
            sliderFraction = 1.0 / float(self.sliderRange) == 0.25
            note that userScore calc creates custom hybrid with user-concern-level

            value assessment impact weights are almost always negative
            but they CAN have positive vals when: "he never does this"
            so assert test below is invalid

            TODO: check math for +- below:
            """
            # assert appImpact <= 0 and communityImpact <= 0, "invalid valAssess weight A:{0}  C:{1}".format(appImpact, communityImpact)

            appNotchSize = ScoreRuleType._getBoundedNotchSizeBySliderScale(
                staticAppImpact, 4.0
            )
            # 1.5 is CORRECT on a 4 slot slider
            appMin = staticAppImpact - (1.5 * appNotchSize)
            communityNotchSize = ScoreRuleType._getBoundedNotchSizeBySliderScale(
                stdCommunityHybrid, 4.0
            )
            communityMin = stdCommunityHybrid - (1.5 * communityNotchSize)
            # print(
            #     "Constructing MinPlusNotchAppPlusCommunity ValAss UM:{0}  UNS:{1}  AM:{2}  ANS:{3}  SAI:{4}  CI:{5}".format(
            #         userMin,
            #         userNotchSize,
            #         appMin,
            #         appNotchSize,
            #         staticAppImpact,
            #         communityImpact,
            #     )
            # )

            return MinPlusNotchForAppAndCommunity(
                round(appMin, rp),
                round(appNotchSize, rp),
                round(communityMin, rp),
                round(communityNotchSize, rp),
            )

        elif self == ScoreRuleType.INCIDENT:
            # using fraction of relationship length to bump up to max score of -1
            # notch & impact weights should have same sign
            assert (
                staticAppImpact < -0.5 and communityImpact < -0.5
            ), "invalid incident impact weight {0}-{1}".format(
                staticAppImpact, communityImpact
            )

            # subtracting a negative is same as adding
            appNotchSize = -1 - staticAppImpact  # notch is delta up to max of -1

            # app score user hybrid between the two
            hybridNotchSize = -1 - stdCommunityHybrid
            return MinPlusNotchForAppAndCommunity(
                round(staticAppImpact, rp),
                round(appNotchSize, rp),
                round(stdCommunityHybrid, rp),
                round(hybridNotchSize, rp),
            )

        elif self.isCommitLevelChange:
            # min & notch is n/a for breakups & commitLevel changes
            return MinPlusNotchForAppAndCommunity(0.0, 0.0, 0.0, 0.0)

    def appUserScoreFunc(self: ScoreRuleType) -> StdCalcCallableSig:
        """logic for this User (& most app) score calculations
        same function but passed different min & notch vals
        depending on which scoreScope (user vs app) is being executed
        """
        if self.isBehavior:
            return ScoreRuleType._behAndFeelingsCalc

        elif self.isFeeling:
            return ScoreRuleType._behAndFeelingsCalc

        elif self.isValueAssesment:
            return ScoreRuleType._valCalcUserApp

        elif self == ScoreRuleType.INCIDENT:
            return ScoreRuleType._incidentCalc

        elif self.isCommitLevelChange:
            return ScoreRuleType._clChangehCalc

        raise Exception("unknow data-type without scoring method")

    def communityHybridScoreFunc(self: ScoreRuleType) -> StdCalcCallableSig:
        """logic for App score calculation
        the only difference is that different weights and notches
        will be passed in so use the same functions
        """
        if self.isValueAssesment:
            # hybrid impact calc differs for App Score
            return ScoreRuleType._valCalcCommunityHybrid
        return self.appUserScoreFunc()

    @staticmethod
    def _behAndFeelingsCalc(
        minWeight: float, notchSize: float, dataVals: list[float]
    ) -> float:
        # print("behCalc got:  {0}-{1}-{2}".format(minWeight, notchSize, dataVals))
        feelingSliderPosInt = int(dataVals[0])
        assert 1 <= feelingSliderPosInt <= 3, "_behCalc: {0}".format(
            feelingSliderPosInt
        )
        # score = (minWeight, minWeight + notchSize, minWeight + (2 * notchSize))[
        #     feelingSliderPosInt - 1
        # ]

        score = minWeight + ((feelingSliderPosInt - 1) * notchSize)
        # print("Start BehCalc using:")
        # print(minWeight, minWeight + notchSize, minWeight + (2 * notchSize))
        # m = "SliderVal:{0} Score:{1} MinWt:{2} NotchSz:{3}".format(feelingSliderPosInt, score, minWeight, notchSize)
        # print(m)
        if abs(score) > 1:
            return 1.0 if score > 0 else -1.0
        return score

    # values assessment for user score
    @staticmethod
    def _valCalcUserApp(
        minWeight: float, notchSize: float, dataVals: list[float]
    ) -> float:
        """for user score
        minWeight & notchSize always have SAME sign (neg here)
        """
        # end user entered vals
        return ScoreRuleType._valCalcCommunityHybrid(minWeight, notchSize, dataVals)

    # values assessment for community-hybrid score
    @staticmethod
    def _valCalcCommunityHybrid(
        minWeight: float, notchSize: float, dataVals: list[float]
    ) -> float:
        """for app score
        minWeight & notchSize always have SAME sign (neg here)

        value assess can now be POSITIVE if "he never does this"
        """
        # assert minWeight < 0.001, "should be negative; only zero on bypass"
        # end user entered vals
        concernSliderPosInt: float = dataVals[0]
        # prospFrequ: pos 1 means NEVER so just subtract 1
        frequSliderPosInt: float = dataVals[1]
        assert 1 <= concernSliderPosInt <= 4, "_valCalc: {0}-{1}".format(
            concernSliderPosInt, frequSliderPosInt
        )
        # if slider in far-left (1) position, then the weight and notch should be positive
        assert frequSliderPosInt > 1.0 or (
            minWeight > 0
        ), "weird condition: sliderPos: {0}  impactWt: {1}".format(
            frequSliderPosInt, minWeight
        )
        # print("concern: {0}  prospFreq: {1}".format(concernSliderPosInt, frequSliderPosInt))
        if frequSliderPosInt < 2.0:  # == 1.0
            # give user a small (min) positive score for never doing something negative
            # print(
            #     "NeverDoesThis:  minWeight: {0}  dataVals: {1}   {2}".format(
            #         minWeight, dataVals, frequSliderPosInt
            #     )
            # )
            return minWeight

        # assert False, "should not hit this"
        if minWeight > 0:
            return min(1, minWeight + ((frequSliderPosInt - 1) * notchSize))
        else:
            return max(-1, minWeight + ((frequSliderPosInt - 1) * notchSize))

    @staticmethod
    def _incidentCalc(
        minWeight: float, notchSize: float, dataVals: list[float]
    ) -> float:
        #
        overlapDays = float(dataVals[0])
        relationshipLength = float(dataVals[1])
        overlapRatio = overlapDays / relationshipLength
        weightIncrease = notchSize * overlapRatio
        return minWeight + weightIncrease

    @staticmethod
    def _clChangehCalc(
        posOrNegPoints: float, niu: float, dataVals: list[float]
    ) -> float:
        return posOrNegPoints

    @staticmethod
    def _getBoundedNotchSizeBySliderScale(
        sliderMiddleScore: float, scale3or4: float = 4.0
    ) -> float:
        """notch size forms the brackets (3 or 4) around the sliderMiddleScore
        for positive events:
            most-score should never go ABOVE 1
        for negative events:
            most-score should never go BELOW -1

        this means we need to adjust notch-size according to avail space
        for any app/community weight near HIGH-SIDE boundary edges
        this means weights of 7,8 on the high side (7/8 are close to 9)

        0.751 is above max on the 3 slider scale
        0.7279 is above max on the 4 slider scale

        I've checked the math and 1/[3,4] of low side can't kick it below zero
        so only need to worry about the high side

        simply reduce appNotchSize so score can't go outside -1 to 1 range
        """
        assert scale3or4 in [
            3.0,
            4.0,
        ], "divisionFactor {0} out of [3,4] bounds".format(scale3or4)

        estimatedNotchSize: float = sliderMiddleScore / scale3or4
        highThreshold: float = 0.7510 if scale3or4 < 4.0 else 0.7279
        if sliderMiddleScore < highThreshold:
            # too small
            # 1/4 of this score is not big enough to push over 1 or -1
            return estimatedNotchSize

        gapToOneOnHighSide = 1 - abs(sliderMiddleScore)
        # if divisionFactor == 3.0, use entire space
        boundedNotchSize: float = gapToOneOnHighSide
        if scale3or4 == 4.0:
            # if 4.0, use 2/3 of the gap (1/1.5)
            boundedNotchSize = gapToOneOnHighSide * 0.6667

        boundedNotchSize *= 1 if sliderMiddleScore > 0 else -1
        return boundedNotchSize

    def rippleAdjustWeight(
        self: ScoreRuleType, magnification: float, windowCountSince: int
    ) -> float:
        """window length is arbitrary and set by the WindowResolver
        it is the time-span represented by one data-point on client graph
        TODO: based on type, you must reduce weight over time
        """
        if not self.hasRippleEffect:
            return 0
        else:
            # use self & windowCountSince to figure out how much to reduce
            if self.isRepeating:
                return magnification
            elif self.hasEcho:
                return magnification

    @property
    def isSevereNeg(self: ScoreRuleType) -> bool:
        return self in [ScoreRuleType.BREAKUP, ScoreRuleType.INCIDENT]

    # ripple related properties below
    @property
    def hasRippleEffect(self: ScoreRuleType) -> bool:
        return self.isRepeating or self.hasEcho

    @property
    def isRepeating(self: ScoreRuleType) -> bool:
        """e.g. repeating Prospect behavior
        true if it affects scores indefinitely going forward
            self in [ScoreRuleType.VAL_ASSESS_NEVER,
                         ScoreRuleType.VAL_ASSESS_LITLE,
                         ScoreRuleType.VAL_ASSESS_FREQUENT,
                         ScoreRuleType.VAL_ASSESS_LOTS
                    ]
        """
        return (
            ScoreRuleType.VAL_ASSESS_LITTLE.value
            <= self.value
            <= ScoreRuleType.VAL_ASSESS_LOTS.value
        )

    @property
    def hasEcho(self: ScoreRuleType) -> bool:
        # true if it affects score BEYOND day in which it was recorded
        return self in [
            ScoreRuleType.BREAKUP,
            ScoreRuleType.INCIDENT,
            ScoreRuleType.PROSPECT_STATUS_INCREASE,
            ScoreRuleType.PROSPECT_STATUS_DECREASE,
        ]

    @property
    def echoDistance(self: ScoreRuleType) -> int:
        """how many buckets / windows into the future should this affect score
        TODO  make make another module for this???
        """
        if self.hasEcho:
            return self._echoDist
        else:
            return 0

    @property
    def _echoDist(self: ScoreRuleType) -> int:
        """TODO how many windows/buckets going fwd does this affect
        should also specify rate of diminishing
        """
        return 4

    # all static methods
    @staticmethod
    def allIds() -> list[int]:
        # return [0, 1, 2, 3, 10, 11, 12, 13, 20, 30, 40, 41, 50, 51]
        # not sure why this is missing some??  TODO
        return [0, 1, 10, 11, 12, 20, 30, 40, 41, 50, 51]

    @staticmethod
    def random() -> ScoreRuleType:
        _allIDs = ScoreRuleType.allIds()
        randInt = randint(0, len(_allIDs) - 1)
        typInt = _allIDs[randInt]
        return ScoreRuleType(typInt)

    @staticmethod
    def valueRuleTypeFromNormFreqVot(freqVote: int) -> ScoreRuleType:
        """all values (concern & frequency) votes range 1 to 4
        lookup scale between 0-3
        """
        assert isinstance(freqVote, int), "bad arg"
        # assert -1 <= normalizedFreqVote <= 0, "vote was %f; should be -1 to 0" % normalizedFreqVote
        # idx = int(normalizedFreqVote * VALUES_MAX_SLIDER_POSITION) * -1
        return VAL_ASSESS_TYPES[freqVote - 1]

    @staticmethod
    def fromPhaseChange(
        currentPhase: CommitLevel_Display, priorPhase: CommitLevel_Display
    ) -> ScoreRuleType:
        assert isinstance(currentPhase, CommitLevel_Display), "invalid arg"
        if currentPhase == CommitLevel_Display.BROKENUP:
            return ScoreRuleType.BREAKUP

        if currentPhase.value < priorPhase.value:
            return ScoreRuleType.PROSPECT_STATUS_DECREASE
        else:
            return ScoreRuleType.PROSPECT_STATUS_INCREASE

    @staticmethod
    def _testUniqueIdForRec(
        srt: ScoreRuleType, occurDt: date, code: str, sumArgs: float
    ) -> str:
        # give each rec a unique ID for matching in dataLoadMock
        assert isinstance(srt, ScoreRuleType), "invalid arg"
        assert isinstance(occurDt, date), "invalid data: {0} should be date".format(
            occurDt
        )
        return "{0}-{1}-{2:.3f}-{3:%y%m%d}".format(srt.name, code, sumArgs, occurDt)


class SliderRange(IntEnum):
    """we currently have sliders of range 3 & 4
    sliders with even positions need special handling
    """

    THREE = 3  # use as divisor
    FOUR = 4

    @property
    def divisor(self: SliderRange) -> int:
        return self.value

    @property
    def notchMultiple(self: SliderRange) -> float:
        # how much to subtract from midWeight to reach minWeight
        if self == SliderRange.FOUR:
            return 1.5  # sliders with even positions need special handling
        else:
            return 1


# ScoreRuleType defined above
VAL_ASSESS_TYPES = [
    ScoreRuleType.VAL_ASSESS_NEVER,
    ScoreRuleType.VAL_ASSESS_LITTLE,
    ScoreRuleType.VAL_ASSESS_FREQUENT,
    ScoreRuleType.VAL_ASSESS_LOTS,
]


class NdbScoringRuleProp(model.IntegerProperty):
    #
    def _validate(self, value):
        if isinstance(value, int):
            return ScoreRuleType(value)
        elif isinstance(value, str):
            return ScoreRuleType(int(value))
        elif not isinstance(value, ScoreRuleType):
            raise TypeError(
                "expected ScoreRuleType, int, str or unicd, got %s" % repr(value)
            )

    def _to_base_type(self, sx: ScoreRuleType):
        # convert sex to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return ScoreRuleType(value)  # return ScoreRuleType


from marshmallow import fields, ValidationError


class ScoreRuleTypeSerialized(fields.Enum):
    """"""

    def _serialize(
        self: ScoreRuleTypeSerialized, value: ScoreRuleType, attr, obj, **kwargs
    ) -> str:
        if value is None:
            return ""
        return value.name

    def _deserialize(
        self: ScoreRuleTypeSerialized, value: str, attr, data, **kwargs
    ) -> ScoreRuleType:
        try:
            return ScoreRuleType[value]
        except ValueError as error:
            raise ValidationError("") from error

    def dump_default(self: ScoreRuleTypeSerialized) -> ScoreRuleType:
        return ScoreRuleType.BEHAVIOR_NEGATIVE


# from datetime import date
# from enum import Enum, unique
# from collections import namedtuple
# from random import randint
# from google.cloud.ndb import ndb

# from constants import IMPACT_WEIGHT_DECIMALS
# from common.enums.commitLevel import DisplayCommitLvl
# from common.utils.arg_types import MinPlusNotchAppUser
# from .alloc import AllocType

# VAL_ASSESS_TYPES = []  # SET below when module loads


# @unique
# class ScoreRuleType(Enum):
#     """governs how scoring engine
#     treats these types of entries

#     for example, some are repeating (forever)
#     or echo x distance into the future

#     note:  update allIds() below if you add more
#     DO NOT change existing int ID vals w/out fixing properties below

#     Note:  sometimes valuesAsses weights can be positive vals
#         when frequency == 1 (he never does this)
#     TODO:
#         this breaks tests --> the compare to the Numbers validation sheet
#         update and re-export the numbers sheet to return min pos weight
#         for the RECIPROCAL POS behavior
#         (right now, I'm returning pos for the NEG behavior)
#     """

#     # neg-behaviors magnified by impact.yaml & community values
#     BEHAVIOR_POSITIVE = 0
#     BEHAVIOR_NEGATIVE = 1
#     #
#     FEELING_POSITIVE = 2
#     FEELING_NEGATIVE = 3

#     # vals magnified by impact.yaml & community values
#     VAL_ASSESS_NEVER = 10
#     VAL_ASSESS_LITTLE = 11
#     VAL_ASSESS_FREQUENT = 12
#     VAL_ASSESS_LOTS = 13

#     # ******* start default magnification
#     BREAKUP = 20
#     INCIDENT = 30
#     #
#     PROSPECT_STATUS_INCREASE = 40
#     PROSPECT_STATUS_DECREASE = 41
#     # ******* end default magnification

#     # scores from communication assessment
#     COMMUNICATION_POSITIVE = 50
#     COMMUNICATION_NEGATIVE = 51

#     # ROLLUP = 99

#     @property
#     def allocWeightType(self):
#         if self.isBehavior:
#             return AllocType.BEHAVIOR
#         elif self.isFeeling:
#             return AllocType.FEELING
#         elif self.isValueAssesment:
#             return AllocType.ASSESS
#         elif self == ScoreRuleType.INCIDENT:
#             return AllocType.INCIDENT
#         elif self == ScoreRuleType.BREAKUP:
#             # breakup needs SPECIAL alloc type;  do not use isCommitLevelChange
#             return AllocType.BREAKUP
#         elif self in [
#             ScoreRuleType.PROSPECT_STATUS_INCREASE,
#             ScoreRuleType.PROSPECT_STATUS_DECREASE,
#         ]:
#             return AllocType.COMMITCHANGE
#         # elif self in [ScoreRuleType.COMMUNICATION_POSITIVE, ScoreRuleType.COMMUNICATION_NEGATIVE]:
#         #     return 1    # FIXME
#         # elif self == ScoreRuleType.ROLLUP:
#         #     return AllocType.
#         else:
#             raise ValueError

#     @property
#     def sliderRange(self):
#         if self.isValueAssesment:
#             return SliderRange.FOUR
#         else:
#             return SliderRange.THREE

#     @property
#     def isValueAssesment(self):
#         return 10 <= self.value <= 13
#         # return self in VAL_ASSESS_TYPES

#     @property
#     def isBehavior(self):
#         return 0 <= self.value <= 1
#         # return self in [ScoreRuleType.BEHAVIOR_POSITIVE, ScoreRuleType.BEHAVIOR_NEGATIVE]

#     @property
#     def isFeeling(self):
#         return 2 <= self.value <= 3
#         # return self in [ScoreRuleType.FEELING_POSITIVE, ScoreRuleType.FEELING_NEGATIVE]

#     @property
#     def isCommitLevelChange(self):
#         # does NOT apply to allocWeights;  includes BREAKUP
#         return 40 <= self.value <= 41 or self.value == 20
#         # return self in [ScoreRuleType.PROSPECT_STATUS_INCREASE, ScoreRuleType.PROSPECT_STATUS_DECREASE, ScoreRuleType.BREAKUP]

#     def minAndNotchForUserAndApp(self, appImpact, communityImpact):
#         """figure out base math vals based on rule type
#         converts raw impact vals to hybrids and such based on rule-type
#             userImpact == a single user (1 concern vote); only for valuesAssesment

#             NOTCH should always have SAME SIGN as impact weight
#         """
#         rp = IMPACT_WEIGHT_DECIMALS  # roundPrecision == 4

#         if self.isFeeling or self.isBehavior:
#             # based on 3 position slider
#             oneThird = 0.3333
#             userNotch = appImpact * oneThird
#             userMin = appImpact - userNotch

#             stdHybrid = (communityImpact * 0.700) + (appImpact * 0.300)
#             appNotch = stdHybrid * oneThird
#             appMin = stdHybrid - appNotch
#             return MinPlusNotchAppUser(
#                 round(userMin, rp),
#                 round(userNotch, rp),
#                 round(appMin, rp),
#                 round(appNotch, rp),
#             )

#         # elif self in [ScoreRuleType.FEELING_NEGATIVE, ScoreRuleType.FEELING_POSITIVE]:
#         #     return ScoreRuleType._behCalc()

#         elif self.isValueAssesment:
#             """based on 4 position slider
#             sliderFraction = 1.0 / float(self.sliderRange) == 0.25
#             note that userScore calc creates custom hybrid with user-concern-level

#             value assessment impact weights are almost always negative
#             but they CAN have positive vals when: "he never does this"
#             so assert test below is invalid

#             TODO: check math for +- below:
#             """
#             # assert appImpact <= 0 and communityImpact <= 0, "invalid valAssess weight A:{0}  C:{1}".format(appImpact, communityImpact)
#             oneFourth = 0.250
#             userNotch = appImpact * oneFourth
#             # 1.5 is CORRECT on a 4 slot slider
#             userMin = appImpact - (1.5 * userNotch)

#             appNotch = communityImpact * oneFourth
#             if communityImpact < 0:  # negative
#                 # I dont understand next line of code
#                 # if 1/4 of commImpct is greater than 1-commImpct, then use the lesser
#                 # means: when is BIG (close to 1), then pick a smaller notch size
#                 # I guess this is because community vals can go higher than app/Pierce?
#                 # given sign change of commImpct, prior logic was in error anyway
#                 appNotch = min(appNotch, (1 - abs(communityImpact)) * -1)
#             else:
#                 pass
#             appMin = communityImpact - (1.5 * appNotch)
#             return MinPlusNotchAppUser(
#                 round(userMin, rp),
#                 round(userNotch, rp),
#                 round(appMin, rp),
#                 round(appNotch, rp),
#             )

#         elif self == ScoreRuleType.INCIDENT:
#             # using fraction of relationship length to bump up to max score of -1
#             # notch & impact weights should have same sign
#             assert (
#                 appImpact < -0.5 and communityImpact < -0.5
#             ), "invalid incident impact weight {0}-{1}".format(
#                 appImpact, communityImpact
#             )

#             # subtracting a negative is same as adding
#             userNotch = -1 - appImpact  # notch is delta up to max of -1

#             # app score user hybrid between the two
#             minHybridImpact = (appImpact * 0.300) + (communityImpact * 0.700)
#             hybridNotch = -1 - minHybridImpact
#             return MinPlusNotchAppUser(
#                 round(appImpact, rp),
#                 round(userNotch, rp),
#                 round(minHybridImpact, rp),
#                 round(hybridNotch, rp),
#             )

#         elif self.isCommitLevelChange:
#             # min & notch is n/a for breakups & commitLevel changes
#             return MinPlusNotchAppUser(0.0, 0.0, 0.0, 0.0)

#     def userScoreFunc(self):
#         """logic for this User (& most app) score calculations
#         same function but passed different min & notch vals
#         depending on which scoreScope (user vs app) is being executed
#         """
#         if self.isBehavior:
#             return ScoreRuleType._behCalc()

#         elif self.isFeeling:
#             return ScoreRuleType._behCalc()

#         elif self.isValueAssesment:
#             return ScoreRuleType._valCalcUser()

#         elif self == ScoreRuleType.INCIDENT:
#             return ScoreRuleType._incidentCalc()

#         elif self.isCommitLevelChange:
#             return ScoreRuleType._clChangehCalc()

#     def appScoreFunc(self):
#         """logic for App score calculation
#         the only difference is that different weights and notches
#         will be passed in so use the same functions
#         """
#         if self.isValueAssesment:
#             # hybrid impact calc differs for App Score
#             return ScoreRuleType._valCalcApp()
#         return self.userScoreFunc()

#     @staticmethod
#     def _behCalc():
#         def calc(minWeight, notchSize, dataVals):
#             # print("behCalc got:  {0}-{1}-{2}".format(minWeight, notchSize, dataVals))
#             feelingSliderPosInt = dataVals[0]
#             assert 1 <= feelingSliderPosInt <= 3, "_behCalc: {0}".format(
#                 feelingSliderPosInt
#             )
#             score = (minWeight, minWeight + notchSize, minWeight + (2 * notchSize))[
#                 feelingSliderPosInt - 1
#             ]
#             # print("Start BehCalc using:")
#             # print(minWeight, minWeight + notchSize, minWeight + (2 * notchSize))
#             # m = "SliderVal:{0} Score:{1} MinWt:{2} NotchSz:{3}".format(feelingSliderPosInt, score, minWeight, notchSize)
#             # print(m)
#             if abs(score) > 1:
#                 return 1 if score > 0 else -1
#             return score

#         return calc

#     @staticmethod
#     def _valCalcUser():
#         # values assessment for user score
#         def calc(minWeight, notchSize, dataVals):
#             """for user score
#             minWeight & notchSize always have SAME sign (neg here)
#             """
#             assert minWeight < 0.001, "should be negative; only zero on bypass"
#             # end user entered vals
#             concernSliderPosInt = dataVals[0]
#             frequSliderPosInt = dataVals[
#                 1
#             ]  # prospFrequ: pos 1 means NEVER so just subtract 1
#             assert 1 <= concernSliderPosInt <= 4, "_valCalc: {0}-{1}".format(
#                 concernSliderPosInt, frequSliderPosInt
#             )
#             # print("concern: {0}  prospFreq: {1}".format(concernSliderPosInt, frequSliderPosInt))
#             if frequSliderPosInt == 1:
#                 # give user a small positive score for never doing something negative
#                 # FIXME:  this will break the scoring test; disable for testing
#                 return abs(minWeight)

#             endUserConcernImpact = float(concernSliderPosInt) / -4.000
#             # restore impact weight to midpoint
#             fullStaticWeight = minWeight + (1.5 * notchSize)
#             hybridUserImpactWeight = (endUserConcernImpact * 0.700) + (
#                 fullStaticWeight * 0.300
#             )
#             score = hybridUserImpactWeight * (float(frequSliderPosInt - 1) / 3.00)
#             assert abs(score) <= 1, "oops"
#             return score

#         return calc

#     @staticmethod
#     def _valCalcApp():
#         # values assessment for app score
#         def calc(minWeight, notchSize, dataVals):
#             """for app score
#             minWeight & notchSize always have SAME sign (neg here)

#             value assess can now be positive if "he never does this"
#             assert below is no longer useful
#             """
#             # assert minWeight < 0.001, "should be negative; only zero on bypass"
#             # end user entered vals
#             concernSliderPosInt = dataVals[0]
#             frequSliderPosInt = dataVals[
#                 1
#             ]  # prospFrequ: pos 1 means NEVER so just subtract 1
#             assert 1 <= concernSliderPosInt <= 4, "_valCalc: {0}-{1}".format(
#                 concernSliderPosInt, frequSliderPosInt
#             )
#             # print("concern: {0}  prospFreq: {1}".format(concernSliderPosInt, frequSliderPosInt))
#             if frequSliderPosInt == 1:
#                 # give user a small positive score for never doing something negative
#                 # FIXME:  this will break the scoring test; disable for testing
#                 return abs(minWeight)

#             endUserConcernImpact = float(concernSliderPosInt) / -4.000
#             # restore impact weight to midpoint
#             fullStaticWeight = minWeight + (1.5 * notchSize)
#             hybridAppImpactWeight = (endUserConcernImpact * 0.100) + (
#                 fullStaticWeight * 0.900
#             )
#             score = hybridAppImpactWeight * (float(frequSliderPosInt - 1) / 3.000)
#             assert abs(score) <= 1, "oops"
#             return score

#         return calc

#     @staticmethod
#     def _incidentCalc():
#         def calc(minWeight, notchSize, dataVals):
#             #
#             incident = dataVals[0]
#             overlapDays = incident.overlapDays
#             relationshipLength = 30  # FIXME dataVals[1]
#             overlapRatio = float(overlapDays) / float(relationshipLength)
#             weightIncrease = notchSize * overlapRatio
#             return minWeight + weightIncrease

#         return calc

#     @staticmethod
#     def _clChangehCalc():
#         def calc(posOrNegPoints, niu, dataVals):
#             return posOrNegPoints

#         return calc

#     def rippleAdjustWeight(self, magnification, windowCountSince):
#         """window length is arbitrary and set by the WindowResolver
#         it is the time-span represented by one data-point on client graph
#         TODO: based on type, you must reduce weight over time
#         """
#         if not self.hasRippleEffect:
#             return 0
#         else:
#             # use self & windowCountSince to figure out how much to reduce
#             if self.isRepeating:
#                 return magnification
#             elif self.hasEcho:
#                 return magnification

#     @property
#     def isSevereNeg(self):
#         return self in [ScoreRuleType.BREAKUP, ScoreRuleType.INCIDENT]

#     # ripple related properties below
#     @property
#     def hasRippleEffect(self):
#         return self.isRepeating or self.hasEcho

#     @property
#     def isRepeating(self):
#         """e.g. repeating Prospect behavior
#         true if it affects scores indefinitely going forward
#             self in [ScoreRuleType.VAL_ASSESS_NEVER,
#                          ScoreRuleType.VAL_ASSESS_LITLE,
#                          ScoreRuleType.VAL_ASSESS_FREQUENT,
#                          ScoreRuleType.VAL_ASSESS_LOTS
#                     ]
#         """
#         return (
#             ScoreRuleType.VAL_ASSESS_LITTLE.value
#             <= self.value
#             <= ScoreRuleType.VAL_ASSESS_LOTS.value
#         )

#     @property
#     def hasEcho(self):
#         # true if it affects score BEYOND day in which it was recorded
#         return self in [
#             ScoreRuleType.BREAKUP,
#             ScoreRuleType.INCIDENT,
#             ScoreRuleType.PROSPECT_STATUS_INCREASE,
#             ScoreRuleType.PROSPECT_STATUS_DECREASE,
#         ]

#     @property
#     def echoDistance(self):
#         """how many buckets / windows into the future should this affect score
#         TODO  make make another module for this???
#         """
#         if self.hasEcho:
#             return self._echoDist
#         else:
#             return 0

#     @property
#     def _echoDist(self):
#         """TODO how many windows/buckets going fwd does this affect
#         should also specify rate of diminishing
#         """
#         return 4

#     # all static methods
#     @staticmethod
#     def allIds():
#         # return [0, 1, 2, 3, 10, 11, 12, 13, 20, 30, 40, 41, 50, 51]
#         # not sure why this is missing some??  TODO
#         return [0, 1, 10, 11, 12, 20, 30, 40, 41, 50, 51]

#     @staticmethod
#     def random():
#         _allIDs = ScoreRuleType.allIds()
#         randInt = randint(0, len(_allIDs) - 1)
#         typInt = _allIDs[randInt]
#         return ScoreRuleType(typInt)

#     @staticmethod
#     def valueRuleTypeFromNormFreqVot(freqVote):
#         """all values (concern & frequency) votes are negative -1 to -4
#         and normalized values are between -1 to 0
#         convert back to int to use as index
#         """
#         assert isinstance(freqVote, int), "bad arg"
#         # assert -1 <= normalizedFreqVote <= 0, "vote was %f; should be -1 to 0" % normalizedFreqVote
#         # idx = int(normalizedFreqVote * VALUES_MAX_SLIDER_POSITION) * -1
#         return VAL_ASSESS_TYPES[freqVote - 1]

#     @staticmethod
#     def fromPhaseChange(currentPhase, priorPhase):
#         assert isinstance(currentPhase, DisplayCommitLvl), "invalid arg"
#         if currentPhase == DisplayCommitLvl.BROKENUP:
#             return ScoreRuleType.BREAKUP

#         if currentPhase.value < priorPhase.value:
#             return ScoreRuleType.PROSPECT_STATUS_DECREASE
#         else:
#             return ScoreRuleType.PROSPECT_STATUS_INCREASE

#     @staticmethod
#     def _testUniqueIdForRec(srt, occurDt, code, data):
#         # give each rec a unique ID for matching in dataLoadMock
#         assert isinstance(srt, ScoreRuleType), "invalid arg"
#         assert isinstance(occurDt, (date, str)), "invalid data"
#         return "{0}-{1}-{2}-{3}".format(srt.name, code, data, occurDt)


# class SliderRange(Enum):
#     """we currently have sliders of range 3 & 4
#     sliders with even positions need special handling
#     """

#     THREE = 3  # use as divisor
#     FOUR = 4

#     @property
#     def divisor(self):
#         return self.value

#     @property
#     def notchMultiple(self):
#         # how much to subtract from midWeight to reach minWeight
#         if self == SliderRange.FOUR:
#             return 1.5  # sliders with even positions need special handling
#         else:
#             return 1


# VAL_ASSESS_TYPES = [
#     ScoreRuleType.VAL_ASSESS_NEVER,
#     ScoreRuleType.VAL_ASSESS_LITTLE,
#     ScoreRuleType.VAL_ASSESS_FREQUENT,
#     ScoreRuleType.VAL_ASSESS_LOTS,
# ]


# class NdbScoringRuleProp(ndb.IntegerProperty):
#     # class NdbScoringRuleProp():
#     #
#     #     def __init__(self, indexed, default):
#     #         pass    # remove me when you re-activate ndb

#     def _validate(self, value):
#         if isinstance(value, (int, long)):
#             return ScoreRuleType(value)
#         elif isinstance(value, (str, unicode)):
#             return ScoreRuleType(int(value))
#         elif not isinstance(value, ScoreRuleType):
#             raise TypeError(
#                 "expected ScoreRuleType, int, str or unicd, got %s" % repr(value)
#             )

#     def _to_base_type(self, sx):
#         # convert sex to int
#         if isinstance(sx, int):
#             return sx
#         return int(sx.value)

#     def _from_base_type(self, value):
#         return ScoreRuleType(value)  # return ScoreRuleType


# # class ValueAssessRawEntry(object):
# #
# #     def __init__(self, code, concernVote, freqVote, date):
# #         # er is instance of
# #         self.behCode = code
# #         self.concernVote = concernVote
# #         self.frequVote = freqVote
# #         self.changeDt = date
# #
# #     @staticmethod
# #     def fromTestEntryRow(er):
# #         # method EXCLUSIVELY for testing
# #         return ValueAssessRawEntry(er.code, er.val1, er.val2, er.date)
# #
# #     # @staticmethod
# #     # def fromEntryRow(er):
# #     #     # method EXCLUSIVELY for testing
# #     #     return ValueAssessRawEntry(er.code, er.val1, er.val2, er.date)
