from __future__ import annotations
from enum import Enum, unique, auto
from marshmallow import fields, ValidationError

#
class AutoName(Enum):
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list
    ) -> str:
        return name


@unique  # applies to int value, not the name
class QueuedWorkTyp(AutoName):
    TRACK_CHECKFORINCIDENTS = auto()
    COMMUNITY_NEWS = auto()
    # initiate RedFlag recalc
    PERSON_REDFLAGUPDATE = auto()
    # Notify if no data entered on prospect after x days
    PERSON_AUTOBREAKUP_WARN = auto()
    PERSON_AUTOBREAKUP_DONE = auto()

    # Notify abt value assess counts
    VALUES_QUESTIONSAVAILABLE = auto()
    # stats

    # roll up the deception tell frequencies into memcache
    STATS_CACHETRUSTTELL = auto()
    STATS_DAILY = auto()
    STATS_COMMITLEVEL = auto()
    STATS_DAILYFORGE = auto()

    # testing
    # Route('personscoresrecalc', handler='service_task.tracking_handlers.RescoreProspectsForUser', name='RescoreProspectsForUser'), = 1
    # fake data tasks too long to execute on as endpoint response pushed to queue.
    COMMUNITY_NEWSFORGE = auto()
    TESTDEPLOY = auto()
    STATS_MAKEFAKE = auto()

    @classmethod
    def from_name(cls: QueuedWorkTyp, name: str) -> QueuedWorkTyp:
        # cls here is the enumeration
        return cls[name]

    @property
    def handlerRoute(self: QueuedWorkTyp) -> str:
        """_summary_

        Args:
            self (QueuedWorkTyp): _description_

        Returns:
            str: _description_
        """
        if self is QueuedWorkTyp.TRACK_CHECKFORINCIDENTS:
            return "track/checkForIncidents"
        elif self is QueuedWorkTyp.COMMUNITY_NEWS:
            return "comm/news"
        elif self is QueuedWorkTyp.PERSON_REDFLAGUPDATE:
            return "pers/redFlagUpdate"
        elif self is QueuedWorkTyp.PERSON_AUTOBREAKUP_WARN:
            return "pers/breakupWarn"
        elif self is QueuedWorkTyp.PERSON_AUTOBREAKUP_DONE:
            return "pers/breakupDone"
        elif self is QueuedWorkTyp.VALUES_QUESTIONSAVAILABLE:
            return "vals/questAvail"
        elif self is QueuedWorkTyp.STATS_CACHETRUSTTELL:
            return "stats/cacheTrustTell"
        elif self is QueuedWorkTyp.STATS_DAILY:
            return "stats/daily"
        elif self is QueuedWorkTyp.STATS_COMMITLEVEL:
            return "stats/commitLevel"

        # test methods below
        elif self is QueuedWorkTyp.STATS_DAILYFORGE:
            return "test/stats/dailyForge"
        elif self is QueuedWorkTyp.COMMUNITY_NEWSFORGE:
            return "test/comm/newsForge"
        elif self is QueuedWorkTyp.TESTDEPLOY:
            return "test/comm/deploy"
        elif self is QueuedWorkTyp.STATS_MAKEFAKE:
            return "test/stats/fake"
        else:
            return "undefined"


class QwTypeSerialized(fields.Enum):
    """serialization"""

    def _serialize(
        self: QwTypeSerialized, value: QueuedWorkTyp, attr, obj, **kwargs
    ) -> str:
        if value is None:
            return ""
        return value.name

    def _deserialize(
        self: QwTypeSerialized, value: str, attr, data, **kwargs
    ) -> QueuedWorkTyp:
        try:
            return QueuedWorkTyp[value]
        except ValueError as error:
            raise ValidationError("") from error

    def dump_default(self: QwTypeSerialized) -> QueuedWorkTyp:
        return QueuedWorkTyp.COMMUNITY_NEWS
