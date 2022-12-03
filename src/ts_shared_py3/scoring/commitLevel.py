from ts_shared_py3.enums.commitLevel import DisplayCommitLvl

_ALL_AS_DICT = None


def getCommitLevelImpact(fromPhaseClValue: int, toPhaseClValue: int) -> float:
    global _ALL_AS_DICT
    if _ALL_AS_DICT is None:
        _setAllAsDict()

    clTransKey = CommitLvlWeight.keyFor(fromPhaseClValue, toPhaseClValue)
    clw: CommitLvlWeight = _ALL_AS_DICT.get(clTransKey)
    if clw is not None:
        return clw.weight

    print(
        "Error: getCommitLevelImpact {0}-{1}".format(fromPhaseClValue, toPhaseClValue)
    )
    return 0.0


class CommitLvlWeight(object):
    def __init__(self, frm: DisplayCommitLvl, to: DisplayCommitLvl, weight: float):
        assert isinstance(frm, DisplayCommitLvl)
        assert isinstance(to, DisplayCommitLvl)

        self.frm: DisplayCommitLvl = frm
        self.to: DisplayCommitLvl = to
        self.weight: float = float(weight)

    @property
    def key(self):
        return CommitLvlWeight.keyFor(self.frm.value, self.to.value)

    @staticmethod
    def keyFor(frm: int, to: int):
        # assert isinstance(frm, int)
        return "{0}-{1}".format(frm, to)


# document all weights for commitment level transitions from & to
_ALL_FROM_TO_CL_WEIGHTS = [
    CommitLvlWeight(DisplayCommitLvl.BROKENUP, DisplayCommitLvl.CASUAL, 0.25),
    CommitLvlWeight(DisplayCommitLvl.BROKENUP, DisplayCommitLvl.NONEXCLUSIVE, 0.45),
    CommitLvlWeight(DisplayCommitLvl.BROKENUP, DisplayCommitLvl.EXCLUSIVE_AS, 0.65),
    CommitLvlWeight(DisplayCommitLvl.BROKENUP, DisplayCommitLvl.EXCLUSIVE_MA, 0.85),
    # casual
    CommitLvlWeight(DisplayCommitLvl.CASUAL, DisplayCommitLvl.BROKENUP, -0.2),
    CommitLvlWeight(DisplayCommitLvl.CASUAL, DisplayCommitLvl.NONEXCLUSIVE, 0.2),
    CommitLvlWeight(DisplayCommitLvl.CASUAL, DisplayCommitLvl.EXCLUSIVE_AS, 0.6),
    CommitLvlWeight(DisplayCommitLvl.CASUAL, DisplayCommitLvl.EXCLUSIVE_MA, 0.8),
    # NONEXCLUSIVE
    CommitLvlWeight(DisplayCommitLvl.NONEXCLUSIVE, DisplayCommitLvl.BROKENUP, -0.4),
    CommitLvlWeight(DisplayCommitLvl.NONEXCLUSIVE, DisplayCommitLvl.CASUAL, -0.3),
    CommitLvlWeight(DisplayCommitLvl.NONEXCLUSIVE, DisplayCommitLvl.EXCLUSIVE_AS, 0.4),
    CommitLvlWeight(DisplayCommitLvl.NONEXCLUSIVE, DisplayCommitLvl.EXCLUSIVE_MA, 0.7),
    # EXCLUSIVE_AS
    CommitLvlWeight(DisplayCommitLvl.EXCLUSIVE_AS, DisplayCommitLvl.BROKENUP, -0.8),
    CommitLvlWeight(DisplayCommitLvl.EXCLUSIVE_AS, DisplayCommitLvl.CASUAL, -0.6),
    CommitLvlWeight(DisplayCommitLvl.EXCLUSIVE_AS, DisplayCommitLvl.NONEXCLUSIVE, -0.4),
    CommitLvlWeight(DisplayCommitLvl.EXCLUSIVE_AS, DisplayCommitLvl.EXCLUSIVE_MA, 0.85),
    # EXCLUSIVE_MA
    CommitLvlWeight(DisplayCommitLvl.EXCLUSIVE_MA, DisplayCommitLvl.BROKENUP, -0.9),
    CommitLvlWeight(DisplayCommitLvl.EXCLUSIVE_MA, DisplayCommitLvl.CASUAL, -0.7),
    CommitLvlWeight(DisplayCommitLvl.EXCLUSIVE_MA, DisplayCommitLvl.NONEXCLUSIVE, -0.6),
    CommitLvlWeight(DisplayCommitLvl.EXCLUSIVE_MA, DisplayCommitLvl.EXCLUSIVE_AS, 0.5),
]


def _setAllAsDict():
    global _ALL_AS_DICT, _ALL_FROM_TO_CL_WEIGHTS
    _ALL_AS_DICT = dict()
    for cl in _ALL_FROM_TO_CL_WEIGHTS:
        _ALL_AS_DICT[cl.key] = cl
