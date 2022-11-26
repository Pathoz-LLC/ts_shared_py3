from datetime import date
import google.cloud.ndb as ndb

#
from common.enums.scoreRuleType import ScoreRuleType  # , NdbScoringRuleProp
from common.models.baseNdb_model import BaseNdbModel


class RippleEffect(BaseNdbModel):
    """repeating or echo event that occurred in the relationship
    stored with each date when it happened

    prior (or future??) ripple effect objects are coalesced & used
    each time scores are recalculated

    combination of ruleType & occur date indicate how far fwd (or back)
    this item should ripple
    ruleType also dictates the recurrence interval & half-life of weight
    """

    ruleType = ndb.IntegerProperty(
        indexed=False, default=ScoreRuleType.BEHAVIOR_NEGATIVE.value
    )
    occurDt = ndb.DateProperty(indexed=False)
    weightFactor = ndb.FloatProperty(indexed=False, default=0)
    impactStrength = ndb.FloatProperty(indexed=False, default=0)
    initialPoints = ndb.FloatProperty(indexed=False, default=0)
    expireDt = ndb.DateProperty(indexed=False)

    def daysSinceOccurred(self, compareDate=date.today()):
        """used to determine how many periods since
        an event so it's weight can be reduced over time
        """
        return (compareDate - self.occurDt).days

    def periodsSinceOccurred(self, compareDate, periodWidthInDays=7):
        """TODO i'm sure this rounding logic is wrong"""
        return round(self.daysSinceOccurred(compareDate) / periodWidthInDays)

    def rippleWeightOn(self, scoreDate, periodWidth=7):
        """reduce power of weight (based on ruleType) as time passes"""
        periodsSince = self.periodsSinceOccurred(scoreDate, periodWidth)
        adjustedWeight = self.ruleType.rippleAdjustWeight(
            self.weightFactor, periodsSince
        )
        return adjustedWeight

    @property
    def yearMonthKeyStr(self):
        # identify which ScorePerist (ie month) window this score should live in for persist
        return BaseNdbModel.keyStrFromDate(self.occurDt)

    @property
    def hasExpired(self):
        return self.expireDt < date.today()
