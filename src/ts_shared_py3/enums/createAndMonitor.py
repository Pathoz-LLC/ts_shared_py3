from __future__ import annotations
from enum import IntEnum, unique
from marshmallow import fields, ValidationError
from marshmallow_dataclass import NewType
from google.cloud.ndb import model


class CreateReason(IntEnum):
    RELATIONSHIP = 1  # with app user
    STALKING = 2  # crush or ex
    FRIEND = 3  # for a friend
    # TEST = 4


class CreateReasonSerializedMa(fields.Enum):
    """Serialize sex to/from enum/string
    a marshmallow data-type
    SexSerializedDc (below) is a marshmallow_dataclass type
    """

    def _serialize(
        self: CreateReasonSerializedMa, value: CreateReason, attr, obj, **kwargs
    ) -> str:
        if value is None:
            return CreateReason.RELATIONSHIP.name
        # print("SexSerialized:")
        # print(value.name, type(value))
        return value.name

    def _deserialize(
        self: CreateReasonSerializedMa, value: str, attr, data, **kwargs
    ) -> CreateReason:
        try:
            return CreateReason[value]
        except ValueError as error:
            return CreateReason.RELATIONSHIP


class MonitorStatus(IntEnum):
    """
    keep this Enum in sync w MON_STATUS_DICT below
        still tracking if < 4
        for Person.loadFollowed(), 'active' gets all except archive
        enums have MonitorStatus.lookup_by_name() & lookup_by_number

        TODO: move & restructure this to common/enums
    """

    ARCHIVE = 0
    ACTIVE = 1
    DOGHOUSE = 2
    SEPARATED = 3
    TRUSTMODE = 4
    DELETED = 5


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
            # hack for testing
            return MonitorStatus.ACTIVE
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


class MonitorStatusSerialized(fields.Enum):
    """"""

    def _serialize(
        self: MonitorStatusSerialized, value: MonitorStatus, attr, obj, **kwargs
    ) -> str:
        if value is None:
            return MonitorStatus.ACTIVE.name
        return value.name

    def _deserialize(
        self: MonitorStatusSerialized, value: str, attr, data, **kwargs
    ) -> MonitorStatus:
        try:
            return MonitorStatus[value]
        except ValueError as error:
            raise ValidationError("") from error

    # def dump_default(self: MonitorStatusSerialized) -> MonitorStatus:
    #     return MonitorStatus


# MonitorStatusSerializedMsg = NewType(
#     "MonitorStatusSerialized", str, field=_MonitorStatusSerialized
# )
