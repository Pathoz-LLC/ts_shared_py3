from datetime import date
from typing import ClassVar, Type
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ..schemas.base import DataClassBaseSchema
from ..schemas.tracking import TrackingPayloadMessage


@dataclass(base_schema=DataClassBaseSchema)
class RelationshipPhaseSetupMessage(BaseApiData):
    # to set up a dialog object
    use_id: str = field(default="", metadata=dict(required=True))
    per_id: int = field(default=0, metadata=dict(required=True))
    personName: str = field(default="", metadata=dict(required=True))
    curCommitLevel: str = field(default="", metadata=dict(required=True))
    startTrackingDate: date = field(metadata=dict(required=True))
    breakupCount: int = field(default=0, metadata=dict(required=True))


@dataclass(base_schema=DataClassBaseSchema)
class DialogAnswerMessage(BaseApiData):
    # to request the next question
    use_id: str = field(default="")
    per_id: int = field(default=0, metadata=dict(required=True))
    que_id: int = field(
        default=0, metadata=dict(required=True)
    )  # only needed if revising a prior answer;  otherwise, its curIdx
    last_answer: str = field(default="")


@dataclass(base_schema=DataClassBaseSchema)
class ResponseChoiceMessage(BaseApiData):
    # values from which the user can chose
    toShow: str = field(default="")
    toReturn: str = field(default="")
    isDefault: bool = field(default=False)


@dataclass(base_schema=DataClassBaseSchema)
class QuestionAsMessage(BaseApiData):
    # each question to ask user;  client receives list of these (usually only 1)
    question: str = field(default="")
    responseType: str = field(default="")
    responseChoices: list[ResponseChoiceMessage] = []
    que_id: str = field(default="")  # to use if you need to revise a prior answer


@dataclass(base_schema=DataClassBaseSchema)
class PendingRelPhaseQuestions(BaseApiData):
    # allows returning multiple questions at once
    # but typically sends one at a time
    noMoreQuestions: bool = field(default=False)
    questions: list[QuestionAsMessage] = []
    # when items.count == 0, then use phases as the final result
    # now the server builds the phases / intervals & so next value is not needed
    # phases = BaseApiDataField(IntervalMessage, 3, repeated=True)
    # userMsgKey: str = field(default="")(4, default="")  # to tell them why no more questions
    # use:  dailyLimitExceeded or noMoreQuestions


RelationshipPhaseSetupMessage.Schema.__model__ = RelationshipPhaseSetupMessage
DialogAnswerMessage.Schema.__model__ = DialogAnswerMessage
ResponseChoiceMessage.Schema.__model__ = ResponseChoiceMessage
QuestionAsMessage.Schema.__model__ = QuestionAsMessage
PendingRelPhaseQuestions.Schema.__model__ = PendingRelPhaseQuestions
