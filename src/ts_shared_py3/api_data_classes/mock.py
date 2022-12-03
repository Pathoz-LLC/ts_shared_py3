from datetime import date
from typing import ClassVar, Type
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ...common.schemas.base import NdbBaseSchema

# NOT SURE IF THIS FILE IS USED/NEEDED


@dataclass(base_schema=NdbBaseSchema)
class ForgeNewsMsg(BaseApiData):
    newsPerMinute: int = field(default=6, required=True)
    runTimeSecs: int = field(default=40, required=True)
    eventTypeIdList: str = field(required=True)


@dataclass(base_schema=NdbBaseSchema)
class ForgeDailyStatsMsg(BaseApiData):
    runTimeSecs: int = field(default=60, required=True)
    votesPerMinute: int = field(default=10, required=True)
