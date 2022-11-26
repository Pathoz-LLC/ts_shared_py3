from __future__ import annotations
from enum import IntEnum, unique

""" 

"""


@unique
class ScoreScope(IntEnum):
    """way to describe which score is being calcd/set
    we currently only calculate user & app scores
    """

    APP_AND_USER = 0  # from PG & user perspective
    FLOCK = 1  # NIU
    NIU = 2  # NIU
    COMMUNICATION = 3  # NIU
    COMMUNITY_HYBRID = 4  # from community & hybrid (30% PG) perspective
    AVG = 5  # NIU

    @staticmethod
    def appAndCommunity() -> list[ScoreScope]:
        # change this to regulate which type of calculations are run below
        # Flock & communication are not yet in use;  ScoreScope.COMMUNITY,
        return [ScoreScope.APP_AND_USER, ScoreScope.COMMUNITY_HYBRID]

    @staticmethod
    def all() -> list[ScoreScope]:
        # change this to regulate which type of calculations are run below
        # Flock & communication are not yet in use;  ScoreScope.COMMUNITY,
        return [ScoreScope.APP_AND_USER, ScoreScope.COMMUNITY_HYBRID]
