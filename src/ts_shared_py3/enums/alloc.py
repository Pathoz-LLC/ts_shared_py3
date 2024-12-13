from __future__ import annotations
from typing import List, Union

from enum import IntEnum, unique
from math import floor, log

#
from ..utils.singleton import Singleton

""" When row-scores are grouped into days, buckets or months
    it's important that the more impactful entries
    dominate those rounded/averaged scores
    this module controls how those grouped scores are calculated

    our total bitCode space is 64, but the following shortcuts
    should streamline the data and simplify the code

    DayScore Allocation Logic ShortCuts
        for a given grouping of prospect scores
        calculate a weighMap from the types of entries in the group

    if weightMap == 48, give 25-75 to breakup & incident (other data is moot)
    if weightMap > 31, give 100% of weight to incident (32)
    if weightMap > 15, give 100% of weight to breakup (16)
    if weightMap < 16, consult the alloc table (below) for proportional score allocation 
"""

MAX_REAL_ALLOC_INT = 32


@unique
class AllocType(IntEnum):
    """
    progresses from least to most severe
    any given window (day or bucket) can contain a mix of scores from
    the following record types
    the value for each type is a unique bitCode
    each BCR in the window holds the sum of those bits
    """

    PRESCORE = 0  # aka NO ALLOCATION

    FEELING = 1
    BEHAVIOR = 2
    ASSESS = 4  # values
    COMMITCHANGE = 8  # up or down
    BREAKUP = 16
    INCIDENT = 32

    def __str__(self: AllocType) -> str:
        return "{0}".format(self.name)

    @staticmethod
    def maxAllocWeightType(groupBitSum: int) -> AllocType:
        return _deriveHighestAlloc(groupBitSum)

    @staticmethod
    def maxAllocWeightInt(groupBitSum: int) -> int:
        return AllocType.maxAllocWeightType(groupBitSum).value


# top level methods
def _deriveHighestBitSet(someInt: int) -> int:
    # returns the highest bit set
    return floor(log(someInt, 2))


def _deriveHighestAlloc(someInt: int) -> AllocType:
    if someInt < 1:
        return AllocType.PRESCORE

    ex: int = _deriveHighestBitSet(someInt)
    intRepr = int(2**ex)
    assert intRepr < 33, "bit too high to construct AllocType {0}".format(intRepr)
    return AllocType(intRepr)


class Alloc(object):
    """
    holds the weight distribution for a given group of score types
    for example, in a window with both a feeling and a commit change
    the commit change will carry more weight for the rolled-up day's score
    our matrix below makes all total 1.0
    keeps alloc vals for each of the score-type combinations
    in the Numbers.Constants.ScoreGroupWeightMap
    """

    def __init__(
        self: Alloc,
        bitCode: int,
        feeling: float = 0.0,
        behavior: float = 0.0,
        assess: float = 0.0,
        commit: float = 0.0,
        breakup: float = 0.0,
        incident: float = 0.0,
    ):
        # values passed are int + floats
        sum: int = int(feeling + behavior + assess + commit + breakup + incident)
        assert sum == 1 or sum == 0, "invalid Alloc construction"
        self.bitCode = int(bitCode)
        # different types of entries
        self.feel = float(feeling)
        self.behave = float(behavior)
        self.assess = float(assess)
        self.commit = float(commit)
        self.breakup = float(breakup)
        self.incident = float(incident)

    def weightFor(self: Alloc, weightTyp: Union[AllocType, int]) -> float:
        """caution: if you send weightTyp as an int, you automatically get ONLY
        the weight for the most severe part of this alloc rec
        """
        assert isinstance(weightTyp, (AllocType, int)), "Invalid arg"
        if isinstance(weightTyp, int):
            weightTyp: AllocType = _deriveHighestAlloc(weightTyp)

        if weightTyp == AllocType.FEELING:
            return self.feel
        elif weightTyp == AllocType.BEHAVIOR:
            return self.behave
        elif weightTyp == AllocType.ASSESS:
            return self.assess
        elif weightTyp == AllocType.COMMITCHANGE:
            return self.commit
        elif weightTyp == AllocType.BREAKUP:
            return self.breakup
        elif weightTyp == AllocType.INCIDENT:
            return self.incident
        else:
            return 0.0

    def __str__(self: Alloc) -> str:
        return "Alloc of bits {0}".format(self.bitCode)

    @staticmethod
    def worstDayEver() -> Alloc:
        # to Breakup & Incident on same day; ignore other noise
        return Alloc(48, 0, 0, 0, 0, 0.25, 0.75)

    @staticmethod
    def emptyDefault(groupBitSum: int) -> Alloc:
        return Alloc(groupBitSum)


class AllocLookup(metaclass=Singleton):
    """
    singleton class to figure out weight distribution for multiple entries
    in a day or bucket
    """

    def __init__(self: AllocLookup) -> None:
        if self.init_completed:
            return
        self.weights: map[int, Alloc] = _hydrateLookup()

    def getAllocWeightsFor(self: AllocLookup, groupBitSum: int) -> Alloc:
        """use value of weightTyp to lookup distribution

        if weightMap == 48, give 50-50 to breakup & incident (probably moot)
        if weightMap > 31, give 100% of weight to incident
        if weightMap > 15, give 100% of weight to breakup
        if weightMap < 16, consult the table for score allocation
        """
        assert isinstance(groupBitSum, int), "Invalid arg"

        if groupBitSum < 17:
            # this will find breakup alloc
            return self.weights[groupBitSum]

        elif (groupBitSum & 48) >= 48:
            # incident & breakup on same day  (possible noise too)
            return Alloc.worstDayEver()

        elif groupBitSum > 31:
            # incident plus noise
            a = Alloc.emptyDefault(groupBitSum)
            a.incident = 1  # 100%
            return a

        elif groupBitSum > 16:
            # breakup plus noise
            # a = Alloc.emptyDefault(groupBitSum)
            # a.breakup = 1  # 100%
            # return a
            return self.weights[16]


def _hydrateLookup() -> map[int, Alloc]:
    """returns a dict of Alloc objects keyed by bitCode
    from 1 to 16
    above 16 is a special case handled in code
    """
    lstOfAlloc = getAlloc()
    weights: map[int, Alloc] = dict()
    for a in lstOfAlloc:
        weights[a.bitCode] = a
    return weights


def getAlloc() -> list[Alloc]:
    """p1 is bitCode
    remaining vals are float representing percent of
    the group (day or bucket) score that should be
    allocated per data-type
    keep values below in sync with gettingBetter spreadsheet (see Pierce)
    """
    return [
        Alloc(1, 1, 0, 0, 0, 0, 0),
        Alloc(2, 0, 1, 0, 0, 0, 0),
        Alloc(4, 0, 0, 1, 0, 0, 0),
        Alloc(8, 0, 0, 0, 1, 0, 0),
        Alloc(16, 0, 0, 0, 0, 1, 0),
        # Alloc(32, 0, 0, 0, 0, 0, 1),  # this row NIU
        Alloc(3, 0.3, 0.7, 0, 0, 0, 0),
        Alloc(5, 0.25, 0, 0.75, 0, 0, 0),
        Alloc(6, 0, 0.5, 0.5, 0, 0, 0),
        Alloc(7, 0.2, 0.4, 0.4, 0, 0, 0),
        Alloc(9, 0.1, 0, 0, 0.9, 0, 0),
        Alloc(10, 0, 0.3, 0, 0.7, 0, 0),
        Alloc(11, 0.1, 0.3, 0, 0.6, 0, 0),
        Alloc(12, 0, 0, 0.3, 0.7, 0, 0),
        Alloc(13, 0.2, 0, 0.2, 0.6, 0, 0),
        Alloc(14, 0, 0.2, 0.2, 0.6, 0, 0),
        Alloc(15, 0.05, 0.15, 0.15, 0.65, 0, 0),
        # Alloc.worstDayEver(),  # this row NIU
    ]
