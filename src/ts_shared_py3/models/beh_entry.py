from datetime import date, datetime, timedelta, time

import google.cloud.ndb as ndb

#
from ..config.behavior.beh_constants import (
    FEELING_ONLY_CODE_NEG,
    FEELING_ONLY_CODE_POS,
)
from .baseNdb_model import BaseNdbModel
from ..config.behavior.load_yaml import BehaviorSourceSingleton


behaviorDataShared = BehaviorSourceSingleton()  # read only singleton


class Entry(BaseNdbModel):  # ndb.model.Expando
    """
    each behavior log entry looks like this
        stored as a sub-property of PersonBehavior table
        on per-month based on self.occurDateTime
    """

    rowNum = ndb.IntegerProperty(indexed=False, default=1)
    behaviorCode = ndb.StringProperty(indexed=True, required=True)
    positive = ndb.BooleanProperty(indexed=False, default=False)
    feelingStrength = ndb.IntegerProperty(
        indexed=False, default=1
    )  # feeling strength re beh (1-3) 3vals

    coords = ndb.GeoPtProperty()

    comments = ndb.TextProperty(indexed=False, default="")  # any notes or comments
    shareDetails = ndb.TextProperty(
        indexed=False, default=""
    )  # as str: "F:kadkdfj;T:388844" share IDs from both FB & Twitter
    occurDateTime = ndb.DateTimeProperty(indexed=True)
    # occurDateTime = ndb.DateTimeProperty(indexed=True)
    addDateTime = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    modifyDateTime = ndb.DateTimeProperty(indexed=False)
    categoryCode = ndb.StringProperty(
        indexed=True, default="communicationPos"
    )  # top category

    # Scoring adjustments
    # @property
    # def normalizedFeeling(self):
    #     assert sc.BEH_MIN_SLIDER_POSITION <= self.feelingStrength <= sc.BEH_MAX_SLIDER_POSITION, "was: %d" % self.feelingStrength
    #     mult = 1.0 if self.positive else -1.0
    #     return float(self.feelingStrength / sc.BEH_MAX_SLIDER_POSITION * mult)

    # End ScoringOld adjustments

    @property
    def isFeelingOnly(self):
        return self.behaviorCode in (FEELING_ONLY_CODE_NEG, FEELING_ONLY_CODE_POS)

    @property
    def longitude(self):
        if self.coords is not None:
            # print(self.coords.longitude)
            return self.coords.longitude  # type: ignore
        else:
            return 0

    @property
    def latitude(self):
        if self.coords is not None:
            self.coords.latitude  # type: ignore
        else:
            return 0

    def to_msg(self, personId: int = 0):  # -> BehaviorRowMsg
        from ..api_data_classes.behavior import BehaviorRowMsg

        brm = BehaviorRowMsg(
            behaviorCode=self.behaviorCode,
            feelingStrength=self.feelingStrength,
            comments=self.comments,
        )
        #
        brm.secsToOrigDtTm = 0
        brm.positive = self.positive
        brm.shareDetails = self.shareDetails
        brm.lon = self.longitude
        brm.lat = self.latitude
        brm.personId = personId
        brm.occurDateTime = self.occurDateTime
        brm.categoryCode = self.categoryCode
        return brm
