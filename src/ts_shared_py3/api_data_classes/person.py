from __future__ import annotations
from datetime import date, datetime
from typing import ClassVar, Type
from dataclasses import field
from marshmallow_dataclass import dataclass, field_for_schema
from marshmallow import Schema, fields

#
from .base import BaseApiData, DataClassBaseSchema
from ..enums.sex import Sex
from ..enums.commitLevel import CommitLvlSerializedMa, CommitLevel_Display
from ..enums.redFlag import RedFlagType, RedFlagTypeSerializedMa
from ..enums.remind_freq import RemindFreq, ReminderFreqSerializedMa
from ..enums.createAndMonitor import MonitorStatus, MonitorStatusSerialized
from ..api_data_classes.user import *


@dataclass(base_schema=DataClassBaseSchema)
class PersonRowDc(BaseApiData):
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
class PersonLocalRowDc(BaseApiData):
    id: int = field()
    commitLevel: CommitLevel_Display = field(
        default=CommitLevel_Display.CASUAL, metadata={"enum": CommitLevel_Display}
    )
    reminderFrequency: RemindFreq = field(
        default=RemindFreq.DAILY, metadata={"enum": RemindFreq}
    )
    monitorStatus: MonitorStatus = field(
        default=MonitorStatus.ACTIVE, metadata={"enum": MonitorStatus}
    )

    modDateTime: datetime = field(default_factory=lambda: datetime.now())
    addDateTime: datetime = field(default_factory=lambda: datetime.now())

    nickname: str = field(default="")
    first: str = field(default="")
    last: str = field(default="")
    imagePath: str = field(default="")
    # overallScore: int = field(default=0, metadata=dict(required=True))

    # redFlagBits: int = field(default=0, metadata=dict(required=True))
    xtra: str = field(default="")
    # relStateOverview = BaseApiDataField(RelationshipStateOverviewMessage, 8, repeated=False)
    tsConfidenceScore: float = field(default=50.0)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PersonFullLocalRowDc(BaseApiData):
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
    reminderFrequency: RemindFreq = field(
        default=RemindFreq.DAILY, metadata={"enum": RemindFreq}
    )
    redFlagBits: int = field(default=0)

    mobile: str = field(default="")
    first: str = field(default="")
    last: str = field(default="")
    alias: str = field(default="")
    email: str = field(default="")
    city: str = field(default="")
    state: str = field(default="")
    zip: str = field(default="")

    modDateTime: datetime = field(default_factory=lambda: datetime.now())
    addDateTime: datetime = field(default_factory=lambda: datetime.now())

    nickname: str = field(default="")
    imagePath: str = field(default="")
    #
    tsConfidenceScore: float = field(default=50.0)  # aka userScore
    communityScore: float = field(default=50.0)
    # recent changes to score
    userScoreDelta: float = field(default=0)
    communityScoreDelta: float = field(default=0)

    #
    Schema: ClassVar[Type[Schema]] = Schema

    @property
    def asLocalDc(self: PersonFullLocalRowDc) -> PersonLocalRowDc:
        return PersonLocalRowDc(
            id=self.id,
            first=self.first,
            last=self.last,
            nickname=self.nickname,
            commitLevel=self.commitLevel,
            reminderFrequency=self.reminderFrequency,
            monitorStatus=self.monitorStatus,
            imagePath=self.imagePath,
            tsConfidenceScore=self.tsConfidenceScore,
        )

    @property
    def asLocalDbRec(self: PersonFullLocalRowDc):  # -> PersonLocal
        from ..models.person import PersonLocal

        return PersonLocal.fromFullMsg(self)


@dataclass(base_schema=DataClassBaseSchema)
class PersonListDc(BaseApiData):
    items: list[PersonFullLocalRowDc] = field(default_factory=lambda: [])

    Schema: ClassVar[Type[Schema]] = Schema


# Message types below are primary public classes
@dataclass(base_schema=DataClassBaseSchema)
class PersonIdDc(BaseApiData):
    # returned for create
    perId: int = field(default=0, metadata=dict(required=True))
    requestOptions: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PersonPhoneDc(BaseApiData):
    phone: str = field(default="")
    # auth_token: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PersonIdDescriptorDc(BaseApiData):
    perId: int = field(default=0, metadata=dict(required=True))
    idValue: str = field(default="")
    idType: str = field(default="")
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class PersonMockDataDc(BaseApiData):
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
PersonIdMessageCollection: list[PersonIdDc]
PersonPhoneMessageCollection: list[PersonPhoneDc]


@dataclass(base_schema=DataClassBaseSchema)
class IncidentUpdateOpinionDc(BaseApiData):
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
class RedFlagReportDc(BaseApiData):
    """ """

    beganDateTime: datetime = field()
    flagType: RedFlagType = field(
        default=RedFlagType.NEVERSET, metadata=dict(required=True, enum=RedFlagType)
    )

    personId: int = field(default=0, metadata=dict(required=True))
    userId: str = field(default="")
    comment: str = field(default="")
    url: str = field(default="")
    rescinded: int = field(default=0, metadata=dict(required=False))
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class RedFlagSummaryDc(BaseApiData):
    personId: int = field(default=0, metadata=dict(required=True))
    revengeCount: int = field(default=0, metadata=dict(required=True))
    catfishCount: int = field(default=0, metadata=dict(required=True))
    cheatedCount: int = field(default=0, metadata=dict(required=True))
    daterapeCount: int = field(default=0, metadata=dict(required=True))
    reports: list[RedFlagReportDc] = field(default_factory=lambda x: [])
    #
    Schema: ClassVar[Type[Schema]] = Schema


PersonRowDc.Schema.__model__ = PersonRowDc
PersonListDc.Schema.__model__ = PersonListDc
PersonLocalRowDc.Schema.__model__ = PersonLocalRowDc
PersonFullLocalRowDc.Schema.__model__ = PersonFullLocalRowDc

PersonIdDc.Schema.__model__ = PersonIdDc
PersonPhoneDc.Schema.__model__ = PersonPhoneDc
PersonPhoneDc.Schema.__model__ = PersonPhoneDc
PersonIdDescriptorDc.Schema.__model__ = PersonIdDescriptorDc

PersonMockDataDc.Schema.__model__ = PersonMockDataDc
IncidentUpdateOpinionDc.Schema.__model__ = IncidentUpdateOpinionDc
RedFlagReportDc.Schema.__model__ = RedFlagReportDc
RedFlagSummaryDc.Schema.__model__ = RedFlagSummaryDc
