from datetime import date, datetime
from typing import ClassVar, Type
from dataclasses import field
from marshmallow_dataclass import dataclass, field_for_schema
from marshmallow import Schema, fields

from .base import BaseApiData
from ..enums.sex import Sex
from ..enums.commitLevel import CommitLvlSerializedMa, CommitLevel_Display
from ..enums.redFlag import RedFlagType, RedFlagTypeSerializedMa
from ..enums.remind_freq import RemindFreq, ReminderFreqSerializedMa
from ..enums.createAndMonitor import MonitorStatus, MonitorStatusSerialized
from ..api_data_classes.user import *


@dataclass(base_schema=DataClassBaseSchema)
class PersonRowMsg(BaseApiData):
    #
    # deweyG: RedFlagTypeSerializedMsg = field()
    # pierceG: SexSerializedMsg = field()
    id: int = field()
    dob: date = field()
    addDateTime: date = field()

    redFlagBits: int = field(default=0)
    sex: Sex = field(default=Sex.NEVERSET, metadata={"enum": Sex})

    mobile: str = field(default="")
    first: str = field(default="")
    last: str = field(default="")
    email: str = field(default="")
    city: str = field(default="")
    state: str = field(default="")
    zip: str = field(default="")

    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PersonLocalRowMsg(BaseApiData):
    id: int = field()
    commitLevel: CommitLevel_Display = field(
        default=CommitLevel_Display.CASUAL, metadata={"enum": CommitLevel_Display}
    )
    reminderFrequency: RemindFreq = field(
        default=RemindFreq.DAILY, metadata={"enum": RemindFreq}
    )

    modDateTime: datetime = field(default_factory=lambda: datetime.now())
    addDateTime: datetime = field(default_factory=lambda: datetime.now())

    nickname: str = field(default="")
    first: str = field(default="")
    last: str = field(default="")
    imagePath: str = field(default="")
    # overallScore: int = field(default=0, metadata=dict(required=True))
    monitorStatus: int = field(default=1)
    # redFlagBits: int = field(default=0, metadata=dict(required=True))
    xtra: str = field(default="")
    # relStateOverview = BaseApiDataField(RelationshipStateOverviewMessage, 8, repeated=False)
    tsConfidenceScore: float = field(default=50.0)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PersonFullWithLocal(BaseApiData):
    """combines atts from PersonRowMsg & PersonLocalRowMsg
    into one payload
    """

    id: int = field()
    dob: date = field()
    addDateTime: date = field()

    sex: Sex = field(default=Sex.NEVERSET, metadata={"enum": Sex})

    commitLevel: CommitLevel_Display = field(
        default=CommitLevel_Display.CASUAL, metadata={"enum": CommitLevel_Display}
    )
    monitorStatus: MonitorStatus = field(
        default=MonitorStatus.ACTIVE, metadata={"enum": MonitorStatus}
    )
    redFlagBits: int = field(default=0)

    mobile: str = field(default="")
    first: str = field(default="")
    last: str = field(default="")
    email: str = field(default="")
    city: str = field(default="")
    state: str = field(default="")
    zip: str = field(default="")

    modDateTime: datetime = field(default_factory=lambda: datetime.now())
    addDateTime: datetime = field(default_factory=lambda: datetime.now())

    nickname: str = field(default="")
    imagePath: str = field(default="")
    tsConfidenceScore: float = field(default=50.0)
    # overallScore: int = field(default=0, metadata=dict(required=True))

    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PersonListMsg(BaseApiData):
    items: list[PersonFullWithLocal] = field(default_factory=lambda: [])

    Schema: ClassVar[Type[Schema]] = Schema


# Message types below are primary public classes
@dataclass(base_schema=DataClassBaseSchema)
class PersonIdMessage(BaseApiData):
    # returned for create
    perId: int = field(default=0, metadata=dict(required=True))
    requestOptions: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PersonPhoneMessage(BaseApiData):
    phone: str = field(default="")
    # auth_token: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PersonIdentifierMessage(BaseApiData):
    perId: int = field(default=0, metadata=dict(required=True))
    idValue: str = field(default="")
    idType: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PersonMockDataMsg(BaseApiData):
    perId: int = field(default=0, metadata=dict(required=True))
    fileName: str = field(default="better")
    #
    Schema: ClassVar[Type[Schema]] = Schema


# FIXME
# for creating & updating people you follow
# PersonLocalMessage = compose(PersonIdMessage, PersonLocalRowMsg)
# # PersonLocalRowMsg contains full stats payload
# PersonMessage = compose(PersonIdMessage, PersonRowMsg, PersonLocalRowMsg)

# list of active people you follow
# PersonListMessage: list[PersonMessage]

# mostly hooks for testers
PersonIdMessageCollection: list[PersonIdMessage]
PersonPhoneMessageCollection: list[PersonPhoneMessage]


@dataclass(base_schema=DataClassBaseSchema)
class IncidentUpdateOpinionMessage(BaseApiData):
    pass
    #
    Schema: ClassVar[Type[Schema]] = Schema


#     personId: int = field(default=0, metadata=dict(required=True))
#     # either these vals
#     incidentId: int = field(default=0, metadata=dict(required=True))
#     truthOpinion: str = field(default="")
#     # or these vals
#     # actually these are handled when user answers a question
#     # questionId: int = field(default=0, metadata=dict(required=True))
#     # howOften: int = field(default=0, metadata=dict(required=True))
#     # tellStrength: int = field(default=0, metadata=dict(required=True))


@dataclass(base_schema=DataClassBaseSchema)
class RedFlagReportMsg(BaseApiData):
    """ """

    beganDateTime: datetime = field()
    flagType: RedFlagType = field(
        default=RedFlagType.NEVERSET, metadata=dict(required=True, enum=RedFlagType)
    )

    personId: int = field(default=0, metadata=dict(required=True))
    userId: str = field(default="")
    comment: str = field(default="")
    url: str = field(default="")
    rescinded: int = field(default=0, metadata=dict(required=True))
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class RedFlagSummaryMsg(BaseApiData):
    personId: int = field(default=0, metadata=dict(required=True))
    revengeCount: int = field(default=0, metadata=dict(required=True))
    catfishCount: int = field(default=0, metadata=dict(required=True))
    cheatedCount: int = field(default=0, metadata=dict(required=True))
    daterapeCount: int = field(default=0, metadata=dict(required=True))
    reports: list[RedFlagReportMsg] = field(default_factory=lambda x: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema


PersonRowMsg.Schema.__model__ = PersonRowMsg
PersonListMsg.Schema.__model__ = PersonListMsg
PersonLocalRowMsg.Schema.__model__ = PersonLocalRowMsg
PersonFullWithLocal.Schema.__model__ = PersonFullWithLocal

PersonIdMessage.Schema.__model__ = PersonIdMessage
PersonPhoneMessage.Schema.__model__ = PersonPhoneMessage
PersonPhoneMessage.Schema.__model__ = PersonPhoneMessage
PersonIdentifierMessage.Schema.__model__ = PersonIdentifierMessage

PersonMockDataMsg.Schema.__model__ = PersonMockDataMsg
IncidentUpdateOpinionMessage.Schema.__model__ = IncidentUpdateOpinionMessage
RedFlagReportMsg.Schema.__model__ = RedFlagReportMsg
RedFlagSummaryMsg.Schema.__model__ = RedFlagSummaryMsg
