# from __future__ import annotations
# from typing import TYPE_CHECKING
from datetime import date
from collections import namedtuple

#
# if TYPE_CHECKING:
# import common.models.entry_adapter as Ea  # InputEntryAdapter
# import common.scoring.oneScoreMsgWrapper as Osmw  # import OneScoreMsgWrapper, BitCdScoreRollup
# import common.models.raw_day_scores_by_month as Rds  # import PersonMonthScoresRaw, RawDayScores
# import common.models.smoothed_plot_scores as Sps


# class DatedCalcResult(object):
#     def __init__(
#         self, dt: date, userScore: float = 0, appScore: float = 0, bitCd: int = 2
#     ) -> None:
#         # super().__init__()
#         self.pointDt: date = dt
#         self.userScore: float = userScore
#         self.appScore: float = appScore
#         self.itemsBitCode: int = bitCd

#     def setScore(
#         self,
#     ):
#         pass


class ArgTypes:

    DatedCalcResult = namedtuple(
        "DatedCalcResult", ["pointDt", "userAppScore", "communityScore", "itemsBitCode"]
    )

    MinPlusNotchAppUser = namedtuple(
        "MinPlusNotchAppUser",
        ["userAppMin", "userAppNotch", "communityMin", "communityNotch"],
    )

    MissingDateSourceKey = namedtuple(
        "MissingDateSourceKey", ["missingDay", "priorSourceDay"]
    )

    # DayToOsmwMap = dict[date, Osmw.OneScoreMsgWrapper]
    ListOfDatedCalcResult = list[DatedCalcResult]
    # ListAdapterRecs = list[Ea.InputEntryAdapter]

    # MapOccurDtToScoreAdaptLst = dict[date, list[Ea.InputEntryAdapter]]
    # MapDateToListRawScoreDays = Mapping[date, List[RawDayScores]]
    # MapMonthKeyToListRawDayScores = dict[str, list[RawDayScores]]
    # MapMonthKeyToPersonMonthRawScores = dict[str, Rds.PersonMonthScoresRaw]
    # MapMonthKeyToPersonMonthSmoothedScores = dict[str, Sps.SmoothedPlottableMonthScores]
