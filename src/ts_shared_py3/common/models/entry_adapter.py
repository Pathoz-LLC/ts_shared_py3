from __future__ import annotations
from datetime import date
import google.cloud.ndb as ndb

#
# from tests.helpers.trial_data_loader import TestInputRow
from common.enums.scoreScope import ScoreScope
from common.models.baseNdb_model import BaseNdbModel
from common.models.incident_table_only import Incident
from common.models.interval_model import Interval
from common.models.behavior_model import Entry
from common.enums.scoreRuleType import ScoreRuleType
import common.enums.commitLevel as cmtLvl
from scoring.alloc import AllocType
from scoring.calc_servant import RowCalcServant
from scoring.commitLevel import getCommitLevelImpact  # CommitLvlWeight
import scoring.weighting as Weighting

# , RowCalcServant, RollupCalcServant
from constants import (
    FEELING_CD_PREFIX,
    FINAL_SCORE_DECIMALS,
)
from common.config.behavior.beh_constants import (
    FEELING_ONLY_CODE_NEG,
    FEELING_ONLY_CODE_POS,
)

staticWeightsLookup: Weighting.WeightAndAllocLookup = None


class AdapterWrapper(object):
    """this object wraps the stored InputEntryAdapter rec for only 3 purposes
    1. use the scoreRuleType & other vals (behCode) to load the proper calc-servant
    2. run the calc-servant with proper input values
    3. return row-scores to the calc service
    """

    def __init__(self: AdapterWrapper, entryAdapter: InputEntryAdapter) -> None:
        super().__init__()
        global staticWeightsLookup

        self.adapter: InputEntryAdapter = entryAdapter
        if staticWeightsLookup is None:
            staticWeightsLookup = Weighting.WeightAndAllocLookup()

        _rowCalcServant: RowCalcServant = staticWeightsLookup.calcServantFor(
            entryAdapter
        )
        self._userAppScore: float = self._calc(ScoreScope.APP_AND_USER, _rowCalcServant)
        self._communityScore: float = self._calc(
            ScoreScope.COMMUNITY_HYBRID, _rowCalcServant
        )

    # math logic is dispatched from calcServant to it's ScoreRuleType
    def _calc(
        self: AdapterWrapper, scoreScope: ScoreScope, rowCalcServant: RowCalcServant
    ) -> float:
        """returns the score for this data;  may be neg or pos

        use the following values for math:
            self.point  --  -1 to 1
            self.appImpactWeight -- set by pierce on pos/neg behaviors
            self.communityImpactWeight -- voted by community on neg-behaviors
            self.hybridImpactWeight (blend of app & community)
            self.customImpactWeight -- special cases for vals-assesments
        """
        return round(
            rowCalcServant.calc(scoreScope, self.calcArgs), FINAL_SCORE_DECIMALS
        )

    @property
    def isValueAssessmentWithPositiveWeight(self: AdapterWrapper) -> bool:
        return self.adapter.isValueAssessmentWithPositiveWeight

    @property
    def userAppScore(self: AdapterWrapper) -> float:
        # return self._calc(ScoreScope.USER)
        return self._userAppScore

    @property
    def communityScore(self: AdapterWrapper) -> float:
        # return self._calc(ScoreScope.APP)
        return self._communityScore

    @property
    def allocWeightInt(self) -> int:
        return self.adapter.allocWeightInt

    @property
    def ruleType(self) -> ScoreRuleType:
        return self.adapter.ruleType

    @property
    def calcArgs(self) -> list[float]:
        # important to pass along all args needed by the calculation
        return self.adapter.numArgs
        # rt = self.ruleType
        # numArgs = self.adapter.numArgs
        # if rt.isBehavior or rt.isFeeling:
        #     # feel strength
        #     return numArgs[0:1]
        # elif rt.isValueAssesment:
        #     # concern & per-prospect-frequency
        #     return numArgs[0:2]
        # elif rt.isCommitLevelChange:
        #     # pos or neg weight (float) based on change direction
        #     return numArgs[0:3]
        # elif rt == ScoreRuleType.INCIDENT:
        #     # overLapDayCount = numArgs[0]
        #     # relLengthInDays = numArgs[1]
        #     # return [overLapDayCount, relLengthInDays]
        #     return numArgs[0:2]

        # return [0, 0]

    # @property
    # def asInputRow(self: AdapterWrapper) -> TestInputRow:
    #     # NIU
    #     args = self.calcArgs
    #     return TestInputRow(
    #         type=self.ruleType,
    #         date=self.adapter.occurDt,
    #         code=self.adapter._code_name_from_stored_name,
    #         val1=args[0],
    #         val2=args[1],
    #     )


class InputEntryAdapter(BaseNdbModel):
    """intermediate stage between an app input record (entry)
    and rollup into an actual RawDayScores
        (stored by month in PersonMonthScoresRaw)

    numArgs:  stores feelings & concern votes
    strArgs:  stores behCode and commit-lvl code
    dtArgs:   stores dates (only for commit level changes & incidents)
    ruleTypeInt governs how to parse each series of args

    its RawDayScores that get interpolated, smoothed and stored
    in ProcessedMonthScores as PlottableScores recs
    and PlottableScores recs get loaded & sent to the client for graph
    """

    ruleTypeInt = ndb.IntegerProperty(
        required=True, indexed=False, choices=[rt.value for rt in ScoreRuleType]
    )
    occurDt = ndb.DateProperty(required=True, indexed=True)
    numArgs = ndb.FloatProperty(repeated=True, indexed=False)
    strArgs = ndb.TextProperty(repeated=True, indexed=False)
    dtArgs = ndb.DateProperty(repeated=True, indexed=False)
    # scored set true after calc when occurDt stored on:  PersonMonthScoresRaw.perDayScores
    scored = ndb.BooleanProperty(default=False, indexed=True)
    # recID mostly for testing; many be empty on disk
    recID = ndb.TextProperty(repeated=False, indexed=False, default="")
    # saveDtTm used to control the transaction that sets scored flag
    saveDtTm = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    # debugRecId = ndb.StringProperty(indexed=False)

    def setKeyProperties(self: InputEntryAdapter, userId: str, prospId: int):
        # unique ID will be assigned for me
        parentKey = BaseNdbModel.makeAncestor(userId, prospId)
        self.key = ndb.Key(self.__class__.__name__, None, parent=parentKey)

    def save(self: InputEntryAdapter):
        self.put()

    @property
    def isValueAssessmentWithPositiveWeight(self: InputEntryAdapter) -> bool:
        return (
            self.ruleType.isValueAssesment
            and len(self.numArgs) > 1
            and self.numArgs[1] < 1.09
        )

    # @property
    # def niu_calcArgs(self) -> list[float]:
    #     # values used by the calc servant;
    #     # see AdapterWrapper.calcArgs
    #     # NIU:  moved up to wrapper
    #     return [0.0, 0.0]
    #     # return self.numArgs[0:2]

    @property
    def ruleType(self: InputEntryAdapter) -> ScoreRuleType:
        # rt = ScoreRuleType(self.ruleTypeInt)
        # assert isinstance(
        #     rt, ScoreRuleType
        # ), "err: {0} is not a ScoreRuleType  {1}".format(type(rt), rt)
        # return rt
        return ScoreRuleType(self.ruleTypeInt)

    @property
    def allocWeightType(self) -> AllocType:
        # determines how much weight to apply to this entry
        return self.ruleType.allocWeightType

    @property
    def allocWeightInt(self: InputEntryAdapter) -> int:
        # int value of AllocType enum
        return self.allocWeightType.value

    @classmethod
    def fromFeeling(cls, beh: Entry) -> InputEntryAdapter:
        """
        called fromBehavior below
        behavior reports with no behCode;  aka feeling-only report
        """
        ruleType: ScoreRuleType = (
            ScoreRuleType.FEELING_POSITIVE
            if beh.positive
            else ScoreRuleType.FEELING_NEGATIVE
        )

        behCode: str = FEELING_ONLY_CODE_POS if beh.positive else FEELING_ONLY_CODE_NEG
        ieAdapt = cls(
            ruleTypeInt=ruleType.value,
            occurDt=beh.occurDateTime.date(),
            numArgs=[beh.feelingStrength],
            strArgs=[behCode],
        )
        # track IDs for testing
        # ieAdapt.debugRecId = ScoreRuleType._testUniqueIdForRec(
        #     ruleType, beh.occurDateTime.date(), beh.behaviorCode, 0
        # )
        return ieAdapt

    @classmethod
    def fromBehavior(cls, beh: Entry) -> InputEntryAdapter:
        """
        point = beh.normalizedFeeling from -1 to 1
        """

        if beh.behaviorCode.startswith(FEELING_CD_PREFIX):
            return InputEntryAdapter.fromFeeling(beh)

        ruleType = (
            ScoreRuleType.BEHAVIOR_POSITIVE
            if beh.positive
            else ScoreRuleType.BEHAVIOR_NEGATIVE
        )
        ieAdapt = cls(
            ruleTypeInt=ruleType.value,
            occurDt=beh.occurDateTime.date(),
            numArgs=[beh.feelingStrength],
            strArgs=[beh.behaviorCode],
        )
        # print(
        #     "$$$ ieAdapt: {0}-{1}-{2}={3}".format(
        #         ieAdapt.ruleTypeInt,
        #         ieAdapt.ruleType.name,
        #         ieAdapt.allocWeightType,
        #         ieAdapt.allocWeightInt,
        #     )
        # )
        # if ieAdapt.wasStrongNegBehavior or ieAdapt.wasStrongPosBehavior:
        #     ieAdapt.createsRipples = True
        # ieAdapt.debugRecId = ScoreRuleType._testUniqueIdForRec(
        #     ruleType, beh.occurDateTime.date(), beh.behaviorCode, 0
        # )
        return ieAdapt

    @classmethod
    def fromValueAssessment(
        cls, behCode: str, concernVote: int, freqVote: int, changeDt: date
    ) -> InputEntryAdapter:
        """
        concern is how much this behavior "would" bother me
        freq is how often my prospect does it
        even tho these behaviors are negative, I suspect (check me)
        both concern & freq are stored as positive
        """
        ruleType: ScoreRuleType = ScoreRuleType.valueRuleTypeFromNormFreqVot(freqVote)
        # calcServant = staticWeightsLookup.rowServantFor(behCode, ruleType)

        # if normalizedFreqVote is positive, it will cause ieAdapt.isPositive to be wrong
        # ieAdapt = cls(calcServant, changeDt, [concernVote, freqVote])
        ieAdapt = cls(
            ruleTypeInt=ruleType.value,
            occurDt=changeDt,
            numArgs=[concernVote, freqVote],
            strArgs=[behCode],
        )

        # how serious was this entry;  votes always positive so abs() is unneeded with new data
        # theyDoThisLots = abs(freqVote) > 2
        # thisUserReallyCares = abs(concernVote) > 2

        # if theyDoThisLots and (thisUserReallyCares or ieAdapt.wasStrongNegBehavior):
        #     ieAdapt.createsRipples = True

        # recID is test code only
        # ieAdapt.debugRecId = ScoreRuleType._testUniqueIdForRec(
        #     ScoreRuleType.VAL_ASSESS_LITTLE, changeDt, behCode, 0
        # )
        return ieAdapt

    @classmethod
    def fromIncident(
        cls, inc: Incident, relationshipLen: int = 30
    ) -> InputEntryAdapter:
        """get relationshipLen from the tracking rec
        we use # of days overlap / relationshipLen to increase
        severity weight for this specific event
        """

        ieAdapt = cls(
            ruleTypeInt=ScoreRuleType.INCIDENT.value,
            occurDt=inc.earliestOverlapDate,
            numArgs=[inc.overlapDays, relationshipLen],
            strArgs=["cheatedOnMeWhenTempted"],
            dtArgs=[
                inc.overlapStartDate,
                inc.overlapEndDate,
            ],
        )
        # no need to set impact weight because xxx handles multiplying
        # ieAdapt.createsRipples = True  # prob unnecesary
        # ieAdapt.debugRecId = ScoreRuleType._testUniqueIdForRec(
        #     ScoreRuleType.INCIDENT, inc.earliestOverlapDate, "cheatedOnMeWhenTempted", 0
        # )
        return ieAdapt

    @classmethod
    def fromCommitLevelChange(
        cls, priorPhase: Interval, mostRecentPhase: Interval
    ) -> InputEntryAdapter:
        """includes breakups"""

        # print(type(priorPhase.commitLevelEnum))
        # print(type(mostRecentPhase.commitLevelEnum))
        assert isinstance(
            mostRecentPhase.commitLevelEnum, cmtLvl.DisplayCommitLvl
        ) and isinstance(
            priorPhase.commitLevelEnum, cmtLvl.DisplayCommitLvl
        ), "invalid arg"

        recentPhaseStart = mostRecentPhase.startDate
        # assert isinstance(recentPhaseStart, date), "invalid arg"

        # assert isinstance(priorPhase, DisplayCommitLvl), "invalid arg"
        ruleType = ScoreRuleType.fromPhaseChange(
            mostRecentPhase.commitLevelEnum, priorPhase.commitLevelEnum
        )
        posOrNegPoints: float = getCommitLevelImpact(
            priorPhase.commitLevelEnum, mostRecentPhase.commitLevelEnum
        )
        # calcServant = staticWeightsLookup.commitLvlChngServant(
        #     ruleType, priorPhase, mostRecentPhase
        # )
        # ieAdapt = cls(calcServant, recentPhaseStart)
        ieAdapt = cls(
            ruleTypeInt=ruleType.value,
            occurDt=recentPhaseStart,
            numArgs=[
                posOrNegPoints,
                priorPhase.commitLevel,
                mostRecentPhase.commitLevel,
            ],
            dtArgs=[
                priorPhase.startDate,
                priorPhase.endDate,
                recentPhaseStart,
                mostRecentPhase.endDate,
            ],
            strArgs=[ruleType.name],
        )

        # these are big events either way; might do more for BREAKUP
        # ieAdapt.createsRipples = True  # prob unnecesary
        # ieAdapt.debugRecId = ScoreRuleType._testUniqueIdForRec(
        #     ruleType, recentPhaseStart, "commitLevelChange", 0
        # )
        # print("CLChng: {0} with recent: {1}  prior:{2}".format(ieAdapt.recID, mostRecentPhase.commitLevel, priorPhase.commitLevel))
        return ieAdapt


ListAdapterWrapper = list[AdapterWrapper]
ListInputAdapterRecs = list[InputEntryAdapter]
MapOccurDtToInputAdapterLst = dict[date, ListInputAdapterRecs]
