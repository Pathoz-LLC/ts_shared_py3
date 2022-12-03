from __future__ import annotations

# import logging

# from logging import error   # , warning, info
from datetime import datetime, timedelta

# ************ for local file testing
# remember to restore NDB in scoringRuleType.py AFTER testing

from random import randint

# import sys
# sys.path.insert(0, "/Users/dgaedcke/dev/TouchstoneMicroservices/")
# sys.path.insert(1, "/Users/dgaedcke/dev/TouchstoneMicroservices/lib")
# sys.path.insert(2, "/Users/dgaedcke/google-cloud-sdk/platform/google_appengine/")
# sys.path.insert(
#     3, "/Users/dgaedcke/google-cloud-sdk/platform/google_appengine/lib/protorpc-1.0/"
# )

# *********** end local testing
from ..utils.singleton import Singleton

# from common.models.behGlobal import BehaviorRollup, VoteTypeRollup
from ..enums.voteType import VoteType
from ..config.behavior.load_yaml import BehCatNode, BehaviorSourceSingleton

#
from ..constants import IMPACT_WEIGHT_DECIMALS, COMMIT_CHNG_CODE_CONST
from ..config.behavior.beh_constants import FEELING_ONLY_CODE_NEG

# this module serves ONLY to keep stats of
# latest community consensus on negative behaviors
# range of consensusImpactStrength should be  0.5<-->1.5

behStaticLookup = BehaviorSourceSingleton()

COMMIT_CHNG_FAKE_CCIW = None  # set below after class declaration


class AppCommHybridImpactWt(object):
    """wrapper for community impact weight
    based on values assessment votes
    these are MIDRANGE (middle) values
    so prospect frequency will be used to move
    impactWeight up or down
    """

    def __init__(
        self: AppCommHybridImpactWt,
        behCode: str,
        commImpactWeight: float = -0.5,
        userAppImpactWeight: float = -0.5,
    ) -> None:
        assert 0.0 < abs(commImpactWeight) <= 1.0, "Err: cciw {0} got {1}".format(
            behCode, commImpactWeight
        )
        self.behCode: str = behCode
        self.communityImpactWeight: float = round(
            commImpactWeight, IMPACT_WEIGHT_DECIMALS
        )
        self.userAppImpactWeight: float = round(
            userAppImpactWeight, IMPACT_WEIGHT_DECIMALS
        )
        self._setHybrid()

    def _setHybrid(self: AppCommHybridImpactWt):
        """since we only use communityImpactWeight to derive hybrid
        and then never use it again (WRONG -- see below), I'm copying
        hybrid onto communityImpactWeight to avoid
        bugs or confusion elsewhere in the code
        where we might use the wrong property
        going forward, on this object:
        communityImpactWeight and hybridImpactWeight are synonomous
        I've also added a property below to get it back for local methods
        """
        self.hybridImpactWeight = round(
            (0.7 * self.communityImpactWeight) + (0.3 * self.userAppImpactWeight),
            IMPACT_WEIGHT_DECIMALS,
        )
        # decided that next line is a bad idea
        # I need original Community value when
        # converting from neg to pos
        # this change was causing Pos-hybrid to be too low
        # self.communityImpactWeight = self.hybridImpactWeight

    def _getInvertedCloneForPositive(
        self: AppCommHybridImpactWt,
        posBehNode: BehCatNode,
        ratioOfPosWeightToNeg: float,
    ) -> AppCommHybridImpactWt:
        """
        self must always be a negative record
        flip the value for the positive behCode
        and adjust commHybrid impact weight for
        impact ratio between pos & neg
        always return a NEW CommConsensusImpactWt
        """

        # validate ranges for both neg & pos recs
        # disable after testing
        assert (
            -1.0 <= self.userAppImpactWeight <= 0.0
        ), "Err: self shoud be negative!!  negRecAppImpact: {0}".format(self)

        # use the inverted of the negative, bumped for ratio, but cap at 1.0
        estAdjustedPosCommWeight: float = min(
            1, abs(ratioOfPosWeightToNeg * self._origCommunityImpactWeight)
        )

        estAdjustedPosHybridWeight = (0.3 * posBehNode.impact) + (
            0.7 * estAdjustedPosCommWeight
        )
        minCommWeightForFlippedPos = estAdjustedPosHybridWeight - (
            1.5 * (estAdjustedPosHybridWeight / 4)
        )

        achWt = AppCommHybridImpactWt(
            posBehNode.code, estAdjustedPosCommWeight, posBehNode.impact
        )
        achWt.hybridImpactWeight = minCommWeightForFlippedPos
        achWt.communityImpactWeight = minCommWeightForFlippedPos
        return achWt

    def __str__(self: AppCommHybridImpactWt) -> str:
        return "AppCommHybridImpactWt Cd:{0}  App:{1}  Comm:{2}  Hyb:{3}".format(
            self.behCode,
            self.userAppImpactWeight,
            self.communityImpactWeight,
            self.hybridImpactWeight,
        )

    def updateCommConsensus(
        self: AppCommHybridImpactWt, commImpactWeight: float
    ) -> None:
        # called only by the refresh job
        self.communityImpactWeight = round(commImpactWeight, IMPACT_WEIGHT_DECIMALS)
        self._setHybrid()

    @property
    def _origCommunityImpactWeight(self: AppCommHybridImpactWt) -> float:
        """
        is started copying hybridImpactWeight onto communityImpactWeight
        to prevent bugs elsewhere in the system
        (from using the wrong property)
        but locally, there may be cases in which I need
        the original communityImpactWeight
        this property reverses the math and gives it back to you
        """
        if self.communityImpactWeight != self.hybridImpactWeight:
            # must not be setting them equal anymore
            return self.communityImpactWeight
        else:
            # assert self.communityImpactWeight == self.hybridImpactWeight, "oops?"
            return (self.hybridImpactWeight - (0.3 * self.userAppImpactWeight)) / 0.7

    @property
    def isPositive(self: AppCommHybridImpactWt) -> bool:
        return self.communityImpactWeight > 0

    @staticmethod
    def default(behCode: str, showErr: bool = True) -> AppCommHybridImpactWt:
        # force scores to zero for unknown codes
        if showErr:
            msg = "Err: no CommImpactWt found for {0}".format(behCode)
            print(msg)
        return AppCommHybridImpactWt(behCode, 0.00001, 0.00001)


if COMMIT_CHNG_FAKE_CCIW is None:
    # global COMMIT_CHNG_FAKE_CCIW
    COMMIT_CHNG_FAKE_CCIW = AppCommHybridImpactWt.default(
        COMMIT_CHNG_CODE_CONST, showErr=False
    )


class CommImpactConsensus(object, metaclass=Singleton):
    """singleton object with all cummulative community
    consensus status rolled into a vote

    community only votes on negative behaviors
    so we flip those votes for positive ones

    WARNING:  likely to have race conditions on this object under load

    """

    def __init__(self: CommImpactConsensus) -> None:
        # dict of CommConsensusImpactWt
        self.impactWeightByComm: map[str, AppCommHybridImpactWt] = dict()
        # dict: key = posBehCode; val = negBehCode
        self.posToNegMap: map[str, str] = dict()

        self.lastRefresh = datetime.now() - timedelta(days=1)
        self._isRefreshing = False

        self._populateDefaultDict()
        # print("CommImpactConsensus single created w:")
        # print(list(self.posToNegMap.values()))
        # print("\n\n")
        # print(list(self.impactWeightByComm.keys()))

    def getCommunityImpactAssessment(
        self: CommImpactConsensus, behNode: BehCatNode
    ) -> AppCommHybridImpactWt:
        """
        community impact consensus for NEG values created here at app-start
        starts with estimated defaults (based on userApp [bcn.impact] * 1.2)
        and then updated from user data as people vote

        positive impact consensus weight vals are DERRIVED
        and created on the fly based on existing negative values
        """
        behCode: str = behNode.code
        if behCode == COMMIT_CHNG_CODE_CONST:
            return COMMIT_CHNG_FAKE_CCIW

        # next lookup ONLY works INITIALLY on negative codes (default vals)
        # but derived community weights for Positive entries will be added on the fly
        # if it fails, treat behCode as positive & use negative to derive community consensus vote
        ccw: AppCommHybridImpactWt = self.impactWeightByComm.get(behCode)
        if ccw is not None:
            # ccw may be pos or neg
            return ccw

        # behNode must be positive below here or else error
        behIsPositive: bool = behNode.positive
        if not behIsPositive:
            # log error;  all negs should be in the impactWeightByComm dict
            m = "Ser.Error:  Neg behCode '{0}' missing from impactWeightByComm dict".format(
                behCode
            )
            # logging.error(m)
            # return AppCommHybridImpactWt(behCode, 0.0, 0.0)
            raise Exception(m)

        # received a positive behCode; find its sibling
        negBehCode: str = behNode.oppositeCode

        # find negative rec & then flip it to positive
        impactWeightsForNegBeh: AppCommHybridImpactWt
        if negBehCode in self.impactWeightByComm:
            impactWeightsForNegBeh = self.impactWeightByComm[negBehCode]
        else:
            # impactWeightsForNegBeh = AppCommHybridImpactWt.default(negBehCode)
            raise Exception(
                "Err:  behCode {0} not found; all negs should be found".format(
                    negBehCode
                )
            )

        # print(negCCW)
        # pos is generally HIGHER impact than neg behaviors
        ratioOfPosWeightToNeg: float = 1.0 + (
            1.0 - abs(impactWeightsForNegBeh.userAppImpactWeight / behNode.impact)
        )

        # create new pos record with all positve vals
        impactWeightsForPosBeh: AppCommHybridImpactWt = AppCommHybridImpactWt(
            behCode,
            ratioOfPosWeightToNeg * impactWeightsForNegBeh.communityImpactWeight * -1,
            behNode.impact,
        )
        # memoize:  now store in dict for fast access later
        self.setDerrivedPositiveCommWeight(impactWeightsForPosBeh)
        return impactWeightsForPosBeh

    def setDerrivedPositiveCommWeight(
        self: CommImpactConsensus, posCcw: AppCommHybridImpactWt
    ) -> None:
        """
        store community impact weight for positive behCode
        positives will get replaced every time negatives
        are updated from community votes
        """
        if posCcw.behCode not in self.impactWeightByComm:
            self.impactWeightByComm[posCcw.behCode] = posCcw

    # def _negCodeFromPosCode(self: CommImpactConsensus, posCode: str):
    #     # WARN: returns invalid code if not found
    #     return self.posToNegMap.get(posCode, FEELING_ONLY_CODE_NEG)

    def refreshIfNeeded(self: CommImpactConsensus):
        if not self._needsRefresh:
            return
        self._isRefreshing = True
        self._refresh()
        self._isRefreshing = False

    @property
    def _needsRefresh(self: CommImpactConsensus):
        # reload & recalc every hour (60 * 60)
        return (
            not self._isRefreshing
            and (datetime.now() - self.lastRefresh).seconds > 3600
        )

    def _refresh(self: CommImpactConsensus):
        """
        negValAssessVTRDict has:
            key: string == behCode  (negatives only
            value: VoteTypeRollup (ndb) record

        this is a singleton obj so don't change data that is being read
            leave impactWeightByComm readable while doing this work

        we replace self.impactWeightByComm with ONLY negative values
        because newest communityImpactWeight needs to be inverted again for positive recs

        shallowCopyNegOnly is new dict but holds ref to same NEG objects in impactWeightByComm
        """
        shallowCopy = self.impactWeightByComm.copy()
        # must skip positives and let them be derived again from neg
        shallowCopyNegOnly = {
            code: cciw
            for (code, cciw) in shallowCopy.iteritems()
            if not cciw.isPositive
        }

        negValAssessVTRDict = BehaviorRollup.loadAllStats(VoteType.CONCERN, False)
        for code, vtr in negValAssessVTRDict.iteritems():
            # vtr is a VoteTypeRollup()
            # these are all negative behCodes that community has ranked
            impactWeightForBeh = shallowCopyNegOnly.get(code)
            if impactWeightForBeh is not None:
                # update with latest derived community consensusWeight
                impactWeightForBeh.updateCommConsensus(vtr.consensusWeight)
            else:
                # should not happen while running;  log me
                bcn = behStaticLookup.bcnFromCode(code)
                impactWeightForBeh = AppCommHybridImpactWt(
                    code, vtr.consensusWeight, bcn.impact
                )
                shallowCopyNegOnly[code] = impactWeightForBeh

        # intentionally replace whole dict so that Positive impacts are re-derived
        # from latest community votes
        self.impactWeightByComm = shallowCopyNegOnly
        self.lastRefresh = datetime.now()

    def _populateDefaultDict(self: CommImpactConsensus):
        # only runs a server startup & builds negative defaults
        # positive will be the inverse when requested
        negCodesWithWeights: list[tuple[str, float]] = _defaultNegCommImpactWeights()
        mapBehCodeToCcIw: map[str, AppCommHybridImpactWt] = dict()
        for defaultInitialNegCommWeightEstimate in negCodesWithWeights:
            negBehCode: str = defaultInitialNegCommWeightEstimate[0]
            negBcn: BehCatNode = behStaticLookup.bcnFromCode(negBehCode)
            if negBcn is None:
                print(
                    "Err: bcn not found for {0} (all negs should be here w defaults)".format(
                        negBehCode
                    )
                )
                continue
            # if negBehCode == "feelingReportNeg":
            #     print(negBcn)

            mapBehCodeToCcIw[negBehCode] = AppCommHybridImpactWt(
                negBehCode, float(defaultInitialNegCommWeightEstimate[1]), negBcn.impact
            )
            # keep a dict to convert posBehCode into its negative sibling
            self.posToNegMap[negBcn.oppositeCode] = negBehCode
        self.impactWeightByComm = mapBehCodeToCcIw


def _defaultNegCommImpactWeights() -> list[tuple[str, float]]:
    # default community impact weights to be set on startup
    # should be quickly overwritten by real comm votes
    # add ("commitLevelChange", 000), manually
    return [
        ("commitLevelChange", 000),
        ("actedOverlyJealousEtc", -0.667),
        ("answeredCellDuringConvers", -0.533),
        ("askedMeOutAndNoShow", -0.533),
        ("ateOfferMeFoodTurnMeOff", -0.4),
        ("ateUnhealthyFood", -0.533),
        ("avoidedCommitConversation", -0.4),
        ("badEmotionalConnection", -0.934),
        ("behavedEmbarrassingly", -0.667),
        ("blamedMeAsTheCause", -0.8),
        ("bodyOdor", -0.533),
        ("boredMeWithTooMuchRoutine", -0.4),
        ("boringPhysIntimacy", -0.533),
        ("breathBad", -0.533),
        ("brokePromiseCommitToMe", -0.533),
        ("brokeUpUnexpectedly", -0.4),
        ("burdenTimeWithFamFriends", -0.533),
        ("calledMeInsultingName", -0.667),
        ("changeAppearanceNotNoticed", -0.4),
        ("changedPlansLastMoment", -0.266),
        ("changedPlansNoCheckIn", -0.667),
        ("cheatedOnMeWhenTempted", -1.0),
        ("cleanUpAfterFamFrndGather", -0.4),
        ("coldPhysIntimacy", -0.4),
        ("coldWithdrawnTowardsMe", -0.533),
        ("contributionsNotOwned", -0.8),
        ("conversationLightNeg", -0.4),
        ("conversationTooSerious", -0.266),
        ("crudeMannersEatingPublic", -0.4),
        ("damagedMyGoodRep", -0.533),
        ("delayReturnMsg", -0.667),
        ("desiresSexLessThanWanted", -0.533),
        ("didNotAtmptSexWhenWanted", -0.533),
        ("didNotCheckInB4LuxPurch", -0.266),
        ("didNotPayBackMoneyOwed", -0.4),
        ("didNotShareEffortToAssist", -0.266),
        ("didNotTakeSuggestSeriously", -0.4),
        ("didTaskPoorlyMinEffort", -0.4),
        ("diffHrsMakeRelatDifficult", -0.266),
        ("disagreeHurtMeGotViolent", -0.8),
        ("disagreeThreatenLeave", -0.8),
        ("disagreeThreatenPunish", -0.8),
        ("disregardedMyOpinion", -0.533),
        ("ditchedMeToBeWithFriends", -0.4),
        ("doesNotSeemToLikeChildrenNeg", -0.533),
        ("drankAlcoholExcess", -0.667),
        ("drankAlcUsedDrugsSecretly", -0.8),
        ("empathizedPoorly", -0.667),
        ("engageCrimBehPutMeAtRisk", -0.8),
        ("exaggeratedMyMistake", -0.667),
        ("failedToNoticeMyHints", -0.4),
        ("feelingReportNeg", -0.4),
        ("focusedOnPastMistakes", -0.8),
        ("forgotMyBirthday", -0.533),
        ("forgotToFollowThrough", -0.4),
        ("gotUptightNotAbleToLetGo", -0.4),
        ("guiltTripManipMeForget", -0.8),
        ("hadLittleInterestMySexNeeds", -0.4),
        ("hasChildrenNeg", -0.533),
        ("heightNotRightForMe", -0.4),
        ("ignoredMyNeeds", -0.533),
        ("ignoredStressWarning", -0.667),
        ("impatientTimeConsidCommit", -0.533),
        ("interactedTalkedXcessWithEx", -0.4),
        ("interestConceivingNeg", -0.667),
        ("interestsTooDiffFromMineNeg", -0.4),
        ("interestsTooSimilarToMineNeg", -0.266),
        ("interruptedBlockedMyRoutine", -0.266),
        ("isNotLikedByChildren", -0.4),
        ("keptMeAwayFromFamFriends", -0.533),
        ("lateForDateMtg", -0.4),
        ("laughedAtOrMadeFunOfMe", -0.667),
        ("leftMessyDidNotCleanUp", -0.4),
        ("liedByOmission", -0.667),
        ("liedWhatSaidDid", -0.8),
        ("likesBeingAroundKidsNeg", -0.266),
        ("livingSpaceDirty", -0.266),
        ("manipulatedMeToGetSex", -0.4),
        ("marriedBeforeNeg", -0.4),
        ("minimizedDiscountedEfforts", -0.8),
        ("minimizedMyWorkEffortValue", -0.667),
        ("misusedLegalDrugs", -0.533),
        ("msgMixedConfusing", -0.4),
        ("newsBadSurprise", -0.4),
        ("notAbleSolveDiffFamFriends", -0.8),
        ("notChangedOnlineRelStatus", -0.533),
        ("notGoodAtTakingTurns", -0.667),
        ("notHonoringSchedAgreedTo", -0.4),
        ("notInterestConceivingNeg", -0.533),
        ("notInterestImproveChildSkills", -0.4),
        ("notMakingEnufSpendIncome", -0.667),
        ("notRespectedByChildren", -0.4),
        ("notSupportRaisingMyChild", -0.667),
        ("openToAlcoholDrugDoesNotWork", -0.533),
        ("poorSkillsChildDiscipline", -0.667),
        ("poorTimingBadNews", -0.8),
        ("pressuredCommunicating", -0.667),
        ("procrastDoingWhatPromised", -0.4),
        ("procrastMakingSchedule", -0.266),
        ("publiclyEmbarrassedMe", -0.533),
        ("pushedEtcMeFeltOffensive", -0.934),
        ("pushedSexWhenNotWanted", -0.533),
        ("putMeInDangerousSituation", -0.8),
        ("refusedDiscExclRelatWithMe", -0.667),
        ("refusedMyOfferOfExclRelat", -0.667),
        ("refusedMyOfferToHaveSex", -0.667),
        ("resentDiscountMySuccess", -0.533),
        ("revealedNeverMarriedBeforeNeg", -0.4),
        ("roughPhysIntimacy", -0.8),
        ("rudeTowardMyFamilyFriends", -0.667),
        ("sexWasUnsatisfyingToMe", -0.533),
        ("shoutOverreactDuringConflict", -0.8),
        ("showedExcessMoodSwing", -0.533),
        ("showedLackFocusOnMoney", -0.533),
        ("showedLittleInterestFitness", -0.533),
        ("showedMeAddictHabitBehav", -0.266),
        ("showedNoInterestInConvers", -0.266),
        ("showedWeakPassionForMe", -0.533),
        ("showedXcessFocusOnMoney", -0.533),
        ("shutMeOutEmotionally", -0.4),
        ("simSchedTooMuchTogether", -0.266),
        ("smokedCigsTurnedMeOff", -0.266),
        ("spentMoneyFoolishly", -0.4),
        ("spentOverFinBudgetAgreedTo", -0.533),
        ("spoiledRomanticEvent", -0.266),
        ("spokeNegAboutEconStatus", -0.4),
        ("spokeNegAboutGender", -0.667),
        ("spokeNegAboutRaceEthnicity", -0.667),
        ("spokeNegAboutSexOrient", -0.667),
        ("staredAtOtherPossPartners", -0.533),
        ("suggestionNotUseful", -0.4),
        ("talkedAboutSelfTooMuch", -0.266),
        ("teethUneven", -0.533),
        ("tooCritical", -0.934),
        ("tookItemsWithoutPermission", -0.4),
        ("treatedWaitStaffPoorly", -0.533),
        ("triedGetMeToPayTheirExp", -0.4),
        ("unbrushedGrimyTeeth", -0.667),
        ("unclearCommPlans", -0.266),
        ("undesiredMsgs", -0.8),
        ("unkindCommentsBody", -0.667),
        ("usedIllegalDrugs", -0.667),
        ("usedIllegalMarijuana", -0.533),
        ("usedMeGetAccessToMyMoney", -0.533),
        ("usedPornToAvoidIntimacy", -0.533),
        ("valuesNotStoodUpFor", -0.4),
        ("wantsSexMoreThanWanted", -0.4),
        ("wasFinanciallyControlling", -0.667),
        ("wasOverlyFlirtacious", -0.667),
        ("wasStingyDidNotShareMoney", -0.4),
        ("wastefulSpendingMoney", -0.533),
        ("weightNotRightForMe", -0.4),
        ("wimpyPhysIntimacy", -0.533),
        ("withheldImportantInfo", -0.667),
        ("withheldSexToPunishMe", -0.667),
        ("woreClothingDisliked", -0.266),
    ]


# tooCritical

# ******************** testing below


def _oneFreq(id):
    # from common.messages.values import PersonFrequencyMsg

    vote = randint(1, 4)
    # return PersonFrequencyMsg(personID=id, frequency=vote, origFrequency=-1)


def _getFreqs(personIds):

    return [_oneFreq(personIds[idx]) for idx in range(len(personIds))]


def _getRandVote(personIds):
    pass
    # from common.messages.values import ValueRateMsg, PersonFrequencyMsg

    # # , ValueOrStatsReqMsg, ValuesCollectionMsg, BehaviorAssessMsg

    # bcn = behStaticLookup.getRandomBcns(1, pos=False)[0]
    # print("ValAss for: {0}".format(bcn.code))
    # vote = randint(1, 4)
    # dt = date_to_message(datetime.today())
    # freq = _getFreqs(personIds)
    # return ValueRateMsg(
    #     behCode=bcn.code,
    #     categoryCode=bcn.topCategoryCode,
    #     concernVote=vote,
    #     origConcernVote=-1,
    #     changeDt=dt,
    #     frequencies=freq,
    #     decrementQuota=False,
    # )


def _addDummyVotes(personIds):

    # from common.tests.helpers.user_helper import UserHelper
    # from common.assess.values import ValuesClient

    # uh = UserHelper()
    # user = uh.get_new_user()

    # for i in range(30):
    #     req = _getRandVote(personIds)
    #     valClient = ValuesClient(user, savePayload=req)
    #     valClient.saveAnswer()  # will also update global stats
    pass


def _rollUpScores():
    pass


def _runValsTests():
    pass


def main():
    # testHarness("/Users/dgaedcke/gcloud_tools/google-cloud-sdk/platform/google_appengine", "common/tests/", runThem=False)
    # _clearOldVotes()
    personIds = []
    _addDummyVotes(personIds)
    _rollUpScores()
    _runValsTests()


if __name__ == "__main__":
    main()
