from datetime import date
from typing import ClassVar, Type
from dataclasses import field  # , fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ...common.schemas.base import NdbBaseSchema


# from common.messages.values import ValueOrStatsReqMsg, ValueRateMsg, ValuesCollectionMsg


# ask for next behavior to rate (assess your values)
@dataclass(base_schema=NdbBaseSchema)
class ValueOrStatsReqMsg(BaseApiData):
    """obj used to construct a values client for reading
    (getting next questions, prior answers or global stats)

    ask server for a ValuesCollectionMsg (1-n behaviors) to assess/vote upon
        also used to request stats or prior answer for a specific behCode

        leave categoryCode blank to load ALL prior answers when calling values.loadPriorAnswers
    """

    categoryCode: str = field(required=True)
    behCode: str = field(default="", required=True)  # optional only sent to load stats
    count: int = field(default=0, required=True)
    # randomizeCat: bool = field(default=False)
    #
    Schema: ClassVar[Type[Schema]] = Schema


# user answers/votes on the question
@dataclass(base_schema=NdbBaseSchema)
class PersonFrequencyMsg(BaseApiData):
    """used to set how often each prospect does a deception tell"""

    personID: int = field(default=0, required=True)
    frequency: int = field(default=0, required=True)
    # must send old answer so stats can be adjusted upon change; > 0 means rec-update
    origFrequency: int = field(default=-1, required=True)  # range 1 <= xx <= 4
    #
    Schema: ClassVar[Type[Schema]] = Schema


# value assess answer user sends back from client
@dataclass(base_schema=NdbBaseSchema)
class ValueRateMsg(BaseApiData):
    """obj used to construct a values client for writing

    payload to add or update both global & per-prospect answers
    also used to send prior answers back to the client for revision

    NOTE:  whenever origConcernVote is sent > 0
            you should also receive isEditDontBumpCount == True
    """

    behCode: str = field(required=True)
    categoryCode: str = field(required=True)  # required to find proper storage shard
    concernVote: int = field(default=2, required=True)
    # send old answer so stats can be adjusted upon change (not yet implemented)
    origConcernVote: int = field(default=-1, required=True)
    frequencies: list[PersonFrequencyMsg] = []
    changeDt: date = None
    # decrementQuota=False tells server that this is a catch-up frequency answer
    # not to count against daily quota
    decrementQuota: bool = field(default=True)
    isEditDontBumpCount: bool = field(default=False)
    #
    Schema: ClassVar[Type[Schema]] = Schema


# a single behavior to rate
@dataclass(base_schema=NdbBaseSchema)
class BehaviorAssessMsg(BaseApiData):
    """a behavior in category
    with optional prior answers attached

    """

    behCode: str = field(required=True)
    catCode: str = field(default="", required=True)
    subCat: str = field(default="", required=True)
    text: str = field(default="")
    # prior answer
    hasPriorAnswer: bool = field(default=False)
    priorAnswer: ValueRateMsg = None
    categoryName: str = field(default="", required=True)
    filterKeywords: str = field(required=False)
    #
    Schema: ClassVar[Type[Schema]] = Schema


# response from request is 1-n questions
@dataclass(base_schema=NdbBaseSchema)
class ValuesCollectionMsg(BaseApiData):
    """payload to add or update both global & per-prospect answers"""

    availQuestCount: int = field(default=5, required=True)
    # should be an entry in items for each behCode
    items: list[BehaviorAssessMsg] = []
    #
    Schema: ClassVar[Type[Schema]] = Schema


# ValuesCollectionMsg = list_message(BehaviorAssessMsg)
