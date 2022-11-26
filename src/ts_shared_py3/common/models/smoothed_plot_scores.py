from __future__ import annotations
from datetime import date
from typing import Optional
import google.cloud.ndb as ndb

#
from common.utils.arg_types import ArgTypes
from .ripple_effect import RippleEffect
from .baseNdb_model import BaseNdbModel


class SmoothedScore(BaseNdbModel):
    """yVal stored as percent w 2 decimals:  56.45
    asDecimal property reverses % math below
    """

    yVal = ndb.FloatProperty(default=0.0)
    # slope is currently NIU
    slope = ndb.FloatProperty(default=0.0)

    @property
    def asDecimal(self: SmoothedScore):
        return round(((self.yVal / 100) * 2) - 1, 3)

    # @property
    # def asPercent(self: SmoothedScore):
    #     # example of conversion from range -1 <-> 1
    #     return round(((self.asDecimal + 1.0) / 2.0) * 100, 3)


class PlottableScores(BaseNdbModel):
    centerDt = ndb.DateProperty(required=True)
    userAppSmSc = ndb.LocalStructuredProperty(SmoothedScore)
    communitySmSc = ndb.LocalStructuredProperty(SmoothedScore)

    @property
    def userScore(self: PlottableScores) -> float:
        return self.userAppSmSc.yVal

    @property
    def commScore(self: PlottableScores) -> float:
        return self.communitySmSc.yVal

    @staticmethod
    def fromDcr(dcr: ArgTypes.DatedCalcResult):
        # m = "Constructing SmoothedScore (in PlottableScores) from {0} {1}".format(
        #     dcr.userAppScore, dcr.pointDt
        # )
        # print(m)
        return PlottableScores(
            centerDt=dcr.pointDt,
            userAppSmSc=SmoothedScore(yVal=dcr.userAppScore),
            communitySmSc=SmoothedScore(yVal=dcr.communityScore),
        )


class SmoothedPlottableMonthScores(BaseNdbModel):
    """stored scores AFTER smoothing math has been run
    its these vals that get sent to the client

    """

    monthStartDt = ndb.DateProperty(indexed=True)
    # LocalStructuredProperty is not indexed
    scores = ndb.LocalStructuredProperty(PlottableScores, repeated=True)
    rippleEffects = ndb.LocalStructuredProperty(RippleEffect, repeated=True)

    # @classmethod
    # def _post_get_hook(cls, key, future):

    @property
    def yearMonthKeyStr(self: SmoothedPlottableMonthScores) -> str:
        return BaseNdbModel.keyStrFromDate(self.monthStartDt)

    @property
    def mapDatesToScoreIdx(self: SmoothedPlottableMonthScores) -> dict[date, int]:
        # used to find idx of ps recs to replace
        return {ps.centerDt: idx for idx, ps in enumerate(self.scores)}

    @staticmethod
    def loadMonthsInRange(
        userId: str, persId: int, minDt: date, maxDt: date
    ) -> list[SmoothedPlottableMonthScores]:
        # return map with key being month str
        maxDt = date.today() if maxDt is None else maxDt
        ancestorKey = BaseNdbModel.makeAncestor(userId, persId)
        q = SmoothedPlottableMonthScores.query(ancestor=ancestorKey).filter(
            SmoothedPlottableMonthScores.monthStartDt >= minDt,
            SmoothedPlottableMonthScores.monthStartDt <= maxDt,
        )
        recs: list[SmoothedPlottableMonthScores] = q.fetch()

        return recs

    @classmethod
    def loadOrCreate(
        cls, userId: str, persId: int, dateInMonth: date
    ) -> SmoothedPlottableMonthScores:
        userPersonKey = BaseNdbModel.makeAncestor(userId, persId)
        yearMonthKeyStr = BaseNdbModel.keyStrFromDate(dateInMonth)
        # create key & see if rec exists in db?
        sspRecKey = ndb.Key(cls.__name__, yearMonthKeyStr, parent=userPersonKey)
        sspRec = sspRecKey.get()
        if sspRec is not None:
            return sspRec
        sspRec = SmoothedPlottableMonthScores(
            monthStartDt=dateInMonth.replace(day=1), scores=[], rippleEffects=[]
        )
        sspRec.key = sspRecKey
        return sspRec

    def _appendOrReplace(
        self: SmoothedPlottableMonthScores,
        dcr: ArgTypes.DatedCalcResult,
        idx: int = None,
    ) -> None:
        # check for append or replace
        if idx is None:
            self.scores.append(PlottableScores.fromDcr(dcr))
            # print(
            #     "Added PS-{0}  UsrScr:{1} to SmoothedPlottableMonthScores at {2}".format(
            #         dcr.pointDt, dcr.userAppScore, len(self.scores)
            #     )
            # )
        else:
            self.scores[idx] = PlottableScores.fromDcr(dcr)
            # print(
            #     "Replaced PS-{0}  UsrScr:{1} in SmoothedPlottableMonthScores at {2}".format(
            #         dcr.pointDt, dcr.userAppScore, idx
            #     )
            # )

    def updatePlotPointFromDcr(
        self: SmoothedPlottableMonthScores, dcr: ArgTypes.DatedCalcResult
    ) -> None:
        """
        ps: PlottableScores = None
        """
        # mapDatesToIdx = {ps.centerDt: idx for idx, ps in enumerate(self.scores)}
        idxOrNone = self.mapDatesToScoreIdx.get(dcr.pointDt, None)
        self._appendOrReplace(dcr, idxOrNone)

    # def addPlottablesFromDcrList(
    #     self: SmoothedPlottableMonthScores,
    #     lstDatedDcrTup: ArgTypes.ListOfDatedCalcResult,
    #     thenSave: bool = False,
    # ) -> None:
    #     """not used currently"""
    #     mapDatesToIdx = {ps.centerDt: idx for idx, ps in enumerate(self.scores)}
    #     for dcr in lstDatedDcrTup:
    #         self._appendOrReplace(dcr, mapDatesToIdx.get(dcr.pointDt, None))

    #     if thenSave:
    #         self.save()

    def save(self: SmoothedPlottableMonthScores) -> None:
        print("Storing SmoothedPlottableMonthScores for {0}:".format(self.monthStartDt))
        # for ps in self.scores:
        #     print("{0}  u:{1}  c:{2}".format(ps.centerDt, ps.userScore, ps.commScore))
        self.put()

    # def _idxIfExists(self: SmoothedPlottableMonthScores, dt: date) -> Optional[int]:
    #     # NIU
    #     return next((i for i, ps in enumerate(self.scores) if ps.centerDt == dt), None)


MapMonthKeyToPersonMonthSmoothedScores = dict[str, SmoothedPlottableMonthScores]
