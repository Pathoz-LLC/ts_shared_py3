from datetime import date, datetime
from typing import ClassVar, Type
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ..schemas.base import NdbBaseSchema
from ..enums.sex import Sex

# FIXME


@dataclass(base_schema=NdbBaseSchema)
class PersonRowMsg(BaseApiData):
    id: str = field(default="")
    mobile: str = field(default="")
    first: str = field(default="")
    last: str = field(default="")
    email: str = field(default="")
    dob: date = field()
    sex: Sex = field(default=Sex.UNKNOWN, required=True)
    redFlagBits: int = field(default=0, required=False)
    city: str = field(default="")
    state: str = field(default="")
    zip: str = field(default="")
    addDateTime: date = field()

    #
    Schema: ClassVar[Type[Schema]] = Schema


# PersonLocalRowMsg = model_message(PersonLocal, exclude=('userKey', 'personKey', 'createReason') )
# PersonLocalRowMsg.field_by_name('nickname').required=False
# PersonLocalRowMsg.field_by_name('createReason').required=False
@dataclass(base_schema=NdbBaseSchema)
class PersonLocalRowMsg(BaseApiData):
    nickname: str = field(default="")
    devotionLevel: int = field(default=0, required=True)
    imagePath: str = field(default="")
    # overallScore: int = field(default=0, required=True)
    monitorStatus: str = field(default="ACTIVE")
    # redFlagBits: int = field(default=0, required=True)
    modDateTime: datetime = field()
    xtra: str = field(default="")
    addDateTime: datetime = field()
    # relStateOverview = BaseApiDataField(RelationshipStateOverviewMessage, 8, repeated=False)
    reminderFrequency: str = field(default="never")
    tsConfidenceScore: float = field(default=0.0)
    #
    Schema: ClassVar[Type[Schema]] = Schema


# Message types below are primary public classes
@dataclass(base_schema=NdbBaseSchema)
class PersonIdMessage(BaseApiData):
    # returned for create
    perId: int = field(default=0, required=True)
    requestOptions: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class PersonPhoneMessage(BaseApiData):
    phone: str = field(default="")
    # auth_token: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class PersonIdentifierMessage(BaseApiData):
    perId: int = field(default=0, required=True)
    idValue: str = field(default="")
    idType: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class PersonMockDataMsg(BaseApiData):
    perId: int = field(default=0, required=True)
    fileName: str = field(default="better")
    #
    Schema: ClassVar[Type[Schema]] = Schema


# for creating & updating people you follow
PersonLocalMessage = compose(PersonIdMessage, PersonLocalRowMsg)
# PersonLocalRowMsg contains full stats payload
PersonMessage = compose(PersonIdMessage, PersonRowMsg, PersonLocalRowMsg)

# list of active people you follow
PersonListMessage: list[PersonMessage]

# mostly hooks for testers
PersonIdMessageCollection: list[PersonIdMessage]
PersonPhoneMessageCollection: list[PersonPhoneMessage]


@dataclass(base_schema=NdbBaseSchema)
class IncidentUpdateOpinionMessage(BaseApiData):
    pass
    #
    Schema: ClassVar[Type[Schema]] = Schema


#     personId: int = field(default=0, required=True)
#     # either these vals
#     incidentId: int = field(default=0, required=True)
#     truthOpinion: str = field(default="")
#     # or these vals
#     # actually these are handled when user answers a question
#     # questionId: int = field(default=0, required=True)
#     # howOften: int = field(default=0, required=True)
#     # tellStrength: int = field(default=0, required=True)


@dataclass(base_schema=NdbBaseSchema)
class RedFlagReportMsg(BaseApiData):
    """ """

    personId: int = field(default=0, required=True)
    userId: str = field(default="")
    flagType: int = field(default=0, required=True)
    comment: str = field(default="")
    url: str = field(default="")
    beganDateTime: datetime = field()
    rescinded: int = field(default=0, required=True)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class RedFlagSummaryMsg(BaseApiData):
    personId: int = field(default=0, required=True)
    revengeCount: int = field(default=0, required=True)
    catfishCount: int = field(default=0, required=True)
    cheatedCount: int = field(default=0, required=True)
    daterapeCount: int = field(default=0, required=True)
    reports: list[RedFlagReportMsg] = []
    #
    Schema: ClassVar[Type[Schema]] = Schema
