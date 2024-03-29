from __future__ import annotations
from enum import IntEnum, unique
import random

from google.cloud.ndb import model
from ..constants import VALUES_MAX_SLIDER_POSITION, BEH_MAX_SLIDER_POSITION


@unique
class VoteType(IntEnum):
    # used to scope count recs on BehGlobal.CountSummary.VoteCount
    NIU = 0  # behavior log entry  (3 slider positions)
    FEELING = 1  # behavior log entry (3 slider positions)
    CONCERN = 2  # global (community) feeling  (4 slider positions)
    FREQUENCY = 3  # how much it applies to each prospect (4 slider positions)

    @property
    def possibleVals(self) -> int:
        # how many vote-slots (slider positions) exist for each type
        if self.value < 2:
            return 3
        else:
            return 4

    @property
    def consensusWeights(self) -> list[float]:
        """does not apply to FEELING votes

        consensusWeights to interpret counts at each slider position
            for CONCERN, S1 means NO-CONCERN (ie NA)
            for FREQUENCY, S1 means "NEVER DOES THIS" (ie NA)
        """
        if self == VoteType.CONCERN:
            return [0.0, 0.33, 0.66, 1]
        else:
            return [0.25, 0.5, 0.75, 1]

    # for testing only concern and frequency
    @staticmethod
    def random() -> VoteType:
        return VoteType(random.randint(1, 3))


class NdbVoteTypeProp(model.IntegerProperty):
    def _validate(self, value):
        if isinstance(value, int):
            return VoteType(value)
        elif isinstance(value, str):
            return VoteType(int(value))
        elif not isinstance(value, VoteType):
            raise TypeError("expected VoteType or integer, got %s" % repr(value))

    def _to_base_type(self, vt: VoteType):
        if isinstance(vt, int):
            return vt
        return int(vt.value)  # Doesn't matter if it's an int or a long

    def _from_base_type(self, value: int):
        return VoteType(value)  # return VoteType


from marshmallow import fields, ValidationError


class VoteTypeSerializedMa(fields.Enum):
    """Field that serializes to a string of sex name"""

    def _serialize(
        self: VoteTypeSerializedMa, value: VoteType, attr, obj, **kwargs
    ) -> str:
        if value is None:
            return ""
        return value.name

    def _deserialize(
        self: VoteTypeSerializedMa, value: str, attr, data, **kwargs
    ) -> VoteType:
        try:
            return VoteType[value]
        except ValueError as error:
            raise ValidationError("Pin codes must contain only digits.") from error
