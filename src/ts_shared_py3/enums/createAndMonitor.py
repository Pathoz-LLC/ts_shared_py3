from enum import IntEnum, unique

from google.cloud.ndb import model


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


class NdbCreateReasonProp(model.IntegerProperty):
    def _validate(self, value: int):
        if isinstance(value, (int)):
            return CreateReason(value)
        elif isinstance(value, (bytes, str)):
            return CreateReason(int(value))
        elif not isinstance(value, CreateReason):
            raise TypeError(
                "expected CreateReason, int, str or unicd, got %s" % repr(value)
            )

    def _to_base_type(self, sx: CreateReason):
        # convert AccountType to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return CreateReason(value)


class NdbMonitorStatusProp(model.IntegerProperty):
    def _validate(self, value: int):
        if isinstance(value, (int)):
            return MonitorStatus(value)
        elif isinstance(value, (bytes, str)):
            return MonitorStatus(int(value))
        elif not isinstance(value, MonitorStatus):
            raise TypeError(
                "expected MonitorStatus, int, str or unicd, got %s" % repr(value)
            )

    def _to_base_type(self, sx: MonitorStatus):
        # convert AccountType to int
        if isinstance(sx, int):
            return sx
        return int(sx.value)

    def _from_base_type(self, value: int):
        return MonitorStatus(value)
