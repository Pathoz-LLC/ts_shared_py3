from enum import Enum, unique, auto


class AutoName(Enum):
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list
    ) -> str:
        return name


@unique  # applies to int value, not the name
class QueuedWorkType(AutoName):
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
