from datetime import date, datetime
from typing import ClassVar, Type
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ..enums.sex import Sex

# FIXME


@dataclass()
class PersonRowMsg(BaseApiData):
    dob: date = field()
    addDateTime: date = field()
    id: str = field()

    mobile: str = field(default="")
    first: str = field(default="")
    last: str = field(default="")
    email: str = field(default="")
    sex: Sex = field(default=Sex.UNKNOWN, metadata=dict(required=True))
    redFlagBits: int = field(default=0)
    city: str = field(default="")
    state: str = field(default="")
    zip: str = field(default="")

    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass()
class PersonListMsg(BaseApiData):
    items: list[PersonRowMsg] = field(default_factory=lambda: [])

    Schema: ClassVar[Type[Schema]] = Schema


# PersonLocalRowMsg = model_message(PersonLocal, exclude=('userKey', 'personKey', 'createReason') )
# PersonLocalRowMsg.field_by_name('nickname').required=False
# PersonLocalRowMsg.field_by_name('createReason').required=False
@dataclass()
class PersonLocalRowMsg(BaseApiData):
    modDateTime: datetime = field(default_factory=lambda: datetime.now())
    addDateTime: datetime = field(default_factory=lambda: datetime.now())

    nickname: str = field(default="")
    devotionLevel: int = field(default=0, metadata=dict(required=True))
    imagePath: str = field(default="")
    # overallScore: int = field(default=0, metadata=dict(required=True))
    monitorStatus: int = field(default=1)
    # redFlagBits: int = field(default=0, metadata=dict(required=True))
    xtra: str = field(default="")
    # relStateOverview = BaseApiDataField(RelationshipStateOverviewMessage, 8, repeated=False)
    reminderFrequency: int = field(default=0)
    tsConfidenceScore: float = field(default=50.0)
    #
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

    personId: int = field(default=0, metadata=dict(required=True))
    userId: str = field(default="")
    flagType: int = field(default=0, metadata=dict(required=True))
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
PersonLocalRowMsg.Schema.__model__ = PersonLocalRowMsg
PersonIdMessage.Schema.__model__ = PersonIdMessage
PersonPhoneMessage.Schema.__model__ = PersonPhoneMessage
PersonPhoneMessage.Schema.__model__ = PersonPhoneMessage
PersonIdentifierMessage.Schema.__model__ = PersonIdentifierMessage
PersonListMsg.Schema.__model__ = PersonListMsg

PersonMockDataMsg.Schema.__model__ = PersonMockDataMsg
IncidentUpdateOpinionMessage.Schema.__model__ = IncidentUpdateOpinionMessage
RedFlagReportMsg.Schema.__model__ = RedFlagReportMsg
RedFlagSummaryMsg.Schema.__model__ = RedFlagSummaryMsg
