from __future__ import annotations
from enum import IntEnum, unique
from google.cloud.ndb import model

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


class NdbScoreScopeProp(model.IntegerProperty):
    def _validate(self, value: int):
        if isinstance(value, (int)):
            return ScoreScope(value)
        elif isinstance(value, (bytes, str)):
            return ScoreScope(int(value))
        elif not isinstance(value, ScoreScope):
            raise TypeError(
                "expected ScoreScope, int, str or unicd, got %s" % repr(value)
            )

    def _to_base_type(self, sx: ScoreScope):
        # convert AccountType to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return ScoreScope(value)


from marshmallow import fields, ValidationError


class ScoreScopeSerialized(fields.Enum):
    """"""

    def _serialize(
        self: ScoreScopeSerialized, value: ScoreScope, attr, obj, **kwargs
    ) -> str:
        if value is None:
            return ""
        return value.name

    def _deserialize(
        self: ScoreScopeSerialized, value: str, attr, data, **kwargs
    ) -> ScoreScope:
        try:
            return ScoreScope[value]
        except ValueError as error:
            raise ValidationError("") from error
