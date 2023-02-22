from __future__ import annotations
from datetime import date
import google.cloud.ndb as ndb

#
from ..enums.alloc import AllocType, Alloc
from ..enums.scoreRuleType import ScoreRuleType
from .baseNdb_model import BaseNdbModel
from ..models.behavior import Entry
from ..models.incident import Incident
from ..models.interval import Interval
from ..scoring.commitLevel import getCommitLevelImpact
from ..config.behavior.beh_constants import (
    FEELING_ONLY_CODE_NEG,
    FEELING_ONLY_CODE_POS,
    FEELING_CD_PREFIX,
)


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
        # unique ID will be assigned for me  : InputEntryAdapter
        parentKey = BaseNdbModel.makeAncestor(userId, prospId)
        self.key = ndb.Key(self.__class__.__name__, None, parent=parentKey)

    def save(self: InputEntryAdapter):  # : InputEntryAdapter
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
    def allocWeightType(self: InputEntryAdapter) -> AllocType:
        # determines how much weight to apply to this entry
        return self.ruleType.allocWeightType

    @property
    def allocWeightInt(self: InputEntryAdapter) -> int:
        # int value of AllocType enum
        return self.allocWeightType.value

    @classmethod
    def fromFeeling(cls: InputEntryAdapter.__class__, beh: Entry) -> InputEntryAdapter:
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
    def fromBehavior(cls: InputEntryAdapter.__class__, beh: Entry) -> InputEntryAdapter:
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
        cls: InputEntryAdapter.__class__,
        behCode: str,
        concernVote: int,
        freqVote: int,
        changeDt: date,
    ) -> InputEntryAdapter:
        """
        concern is how much this behavior "would" bother me
        freq is how often my prospect does it
        even tho these behaviors are negative, I suspect (check me)
        both concern & freq are stored as positive
        """
        if changeDt == None:
            changeDt = date.today()

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
