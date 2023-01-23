from datetime import date, datetime
from typing import ClassVar, Type
from dataclasses import field
from marshmallow_dataclass import dataclass, field_for_schema
from marshmallow import Schema, fields

from .base import BaseApiData
from ..enums.sex import SexSerializedMsg, Sex
from ..enums.commitLevel import CommitLvlSerializedMsg, DisplayCommitLvl
from ..enums.redFlag import RedFlagTypeSerializedMsg, RedFlagType
from ..enums.remind_freq import ReminderFreqSerializedMsg, RemindFreq
from ..enums.createAndMonitor import (
    MonitorStatusSerializedMsg,
    MonitorStatus,
    CreateReason,
)


@dataclass()
class PersonRowMsg(BaseApiData):
    #
    # deweyG: RedFlagTypeSerializedMsg = field()
    # pierceG: SexSerializedMsg = field()
    id: int = field()
    dob: date = field()
    addDateTime: date = field()
    redFlagBits: RedFlagType
    sex: Sex = field(default=Sex.UNKNOWN)

    mobile: str = field(default="")
    first: str = field(default="")
    last: str = field(default="")
    email: str = field(default="")
    city: str = field(default="")
    state: str = field(default="")
    zip: str = field(default="")

    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class PersonLocalRowMsg(BaseApiData):
    id: int = field()
    commitLevel: DisplayCommitLvl = field()
    reminderFrequency: RemindFreq = field()

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


@dataclass()
class PersonFullWithLocal(BaseApiData):
    """combines atts from PersonRowMsg & PersonLocalRowMsg
    into one payload
    """

    sex: Sex
    redFlagBits: RedFlagType = field()
    commitLevel: DisplayCommitLvl = field()
    monitorStatus: MonitorStatus = field()
    id: int = field()
    dob: date = field()
    addDateTime: date = field()

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


@dataclass()
class PersonListMsg(BaseApiData):
    items: list[PersonFullWithLocal] = field(default_factory=lambda: [])

    Schema: ClassVar[Type[Schema]] = Schema


# Message types below are primary public classes
@dataclass()
class PersonIdMessage(BaseApiData):
    # returned for create
    perId: int = field(default=0, metadata=dict(required=True))
    requestOptions: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class PersonPhoneMessage(BaseApiData):
    phone: str = field(default="")
    # auth_token: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class PersonIdentifierMessage(BaseApiData):
    perId: int = field(default=0, metadata=dict(required=True))
    idValue: str = field(default="")
    idType: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
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


@dataclass()
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


@dataclass()
class RedFlagReportMsg(BaseApiData):
    """ """

    beganDateTime: datetime = field()
    flagType: RedFlagTypeSerializedMsg

    personId: int = field(default=0, metadata=dict(required=True))
    userId: str = field(default="")
    comment: str = field(default="")
    url: str = field(default="")
    rescinded: int = field(default=0, metadata=dict(required=True))
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
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
