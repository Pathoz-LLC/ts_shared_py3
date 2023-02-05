from ts_shared_py3.enums.commitLevel import CommitLevel_Display

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
    def __init__(
        self, frm: CommitLevel_Display, to: CommitLevel_Display, weight: float
    ):
        assert isinstance(frm, CommitLevel_Display)
        assert isinstance(to, CommitLevel_Display)

        self.frm: CommitLevel_Display = frm
        self.to: CommitLevel_Display = to
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
    CommitLvlWeight(CommitLevel_Display.BROKENUP, CommitLevel_Display.CASUAL, 0.25),
    CommitLvlWeight(
        CommitLevel_Display.BROKENUP, CommitLevel_Display.NONEXCLUSIVE, 0.45
    ),
    CommitLvlWeight(
        CommitLevel_Display.BROKENUP, CommitLevel_Display.EXCLUSIVE_AS, 0.65
    ),
    CommitLvlWeight(
        CommitLevel_Display.BROKENUP, CommitLevel_Display.EXCLUSIVE_MA, 0.85
    ),
    # casual
    CommitLvlWeight(CommitLevel_Display.CASUAL, CommitLevel_Display.BROKENUP, -0.2),
    CommitLvlWeight(CommitLevel_Display.CASUAL, CommitLevel_Display.NONEXCLUSIVE, 0.2),
    CommitLvlWeight(CommitLevel_Display.CASUAL, CommitLevel_Display.EXCLUSIVE_AS, 0.6),
    CommitLvlWeight(CommitLevel_Display.CASUAL, CommitLevel_Display.EXCLUSIVE_MA, 0.8),
    # NONEXCLUSIVE
    CommitLvlWeight(
        CommitLevel_Display.NONEXCLUSIVE, CommitLevel_Display.BROKENUP, -0.4
    ),
    CommitLvlWeight(CommitLevel_Display.NONEXCLUSIVE, CommitLevel_Display.CASUAL, -0.3),
    CommitLvlWeight(
        CommitLevel_Display.NONEXCLUSIVE, CommitLevel_Display.EXCLUSIVE_AS, 0.4
    ),
    CommitLvlWeight(
        CommitLevel_Display.NONEXCLUSIVE, CommitLevel_Display.EXCLUSIVE_MA, 0.7
    ),
    # EXCLUSIVE_AS
    CommitLvlWeight(
        CommitLevel_Display.EXCLUSIVE_AS, CommitLevel_Display.BROKENUP, -0.8
    ),
    CommitLvlWeight(CommitLevel_Display.EXCLUSIVE_AS, CommitLevel_Display.CASUAL, -0.6),
    CommitLvlWeight(
        CommitLevel_Display.EXCLUSIVE_AS, CommitLevel_Display.NONEXCLUSIVE, -0.4
    ),
    CommitLvlWeight(
        CommitLevel_Display.EXCLUSIVE_AS, CommitLevel_Display.EXCLUSIVE_MA, 0.85
    ),
    # EXCLUSIVE_MA
    CommitLvlWeight(
        CommitLevel_Display.EXCLUSIVE_MA, CommitLevel_Display.BROKENUP, -0.9
    ),
    CommitLvlWeight(CommitLevel_Display.EXCLUSIVE_MA, CommitLevel_Display.CASUAL, -0.7),
    CommitLvlWeight(
        CommitLevel_Display.EXCLUSIVE_MA, CommitLevel_Display.NONEXCLUSIVE, -0.6
    ),
    CommitLvlWeight(
        CommitLevel_Display.EXCLUSIVE_MA, CommitLevel_Display.EXCLUSIVE_AS, 0.5
    ),
]


def _setAllAsDict():
    global _ALL_AS_DICT, _ALL_FROM_TO_CL_WEIGHTS
    _ALL_AS_DICT = dict()
    for cl in _ALL_FROM_TO_CL_WEIGHTS:
        _ALL_AS_DICT[cl.key] = cl
