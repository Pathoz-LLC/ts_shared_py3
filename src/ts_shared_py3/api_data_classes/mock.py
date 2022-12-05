from datetime import date
from typing import ClassVar, Type
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ..schemas.base import DataClassBaseSchema

# NOT SURE IF THIS FILE IS USED/NEEDED


@dataclass(base_schema=DataClassBaseSchema)
class ForgeNewsMsg(BaseApiData):
    eventTypeIdList: str = field(metadata=dict(required=True))
    newsPerMinute: int = field(default=6, metadata=dict(required=True))
    runTimeSecs: int = field(default=40, metadata=dict(required=True))


@dataclass(base_schema=DataClassBaseSchema)
class ForgeDailyStatsMsg(BaseApiData):
    runTimeSecs: int = field(default=60, metadata=dict(required=True))
    votesPerMinute: int = field(default=10, metadata=dict(required=True))


ForgeNewsMsg.Schema.__model__ = ForgeNewsMsg
ForgeDailyStatsMsg.Schema.__model__ = ForgeDailyStatsMsg
