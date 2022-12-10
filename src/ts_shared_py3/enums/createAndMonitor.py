from enum import IntEnum, unique


class CreateReason(IntEnum):
    RELATIONSHIP = 1  # with app user
    STALKING = 2  # crush or ex
    FRIEND = 3  # for a friend
    # TEST = 4


class MonitorStatus(IntEnum):
    """
    keep this Enum in sync w MON_STATUS_DICT below
        still tracking if < 4
        for Person.loadFollowed(), 'active' gets all except archive
        enums have MonitorStatus.lookup_by_name() & lookup_by_number

        TODO: move & restructure this to common/enums
    """

    ACTIVE = 1
    DOGHOUSE = 2
    SEPARATED = 3
    TRUSTMODE = 4
    ARCHIVE = 5
