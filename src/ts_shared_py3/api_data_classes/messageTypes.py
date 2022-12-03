from datetime import date
from typing import ClassVar, Type
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ...common.schemas.base import NdbBaseSchema


def buildStatusMsg(code, msg, detail):
    dtl = detail or ""
    return StatusMessage(code=code, msg=msg, detail=dtl)


@dataclass(base_schema=NdbBaseSchema)
class StatusMessage(BaseApiData):
    # used when Void msg is too uninformative
    code: str = field(default="")
    msg: str = field(default="")
    detail: str = field(default="")

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class JsonMessage(BaseApiData):
    # used when Void msg is too uninformative
    json: str = field(default="")

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class FilterMessage(BaseApiData):
    entityType: str = field(default="person")
    propertyName: str = field(default="monitorStatus")
    propertyValue: str = field(default="active")
    queryOp: str = field(default="==")

    Schema: ClassVar[Type[Schema]] = Schema


FilterMessageCollection: list[FilterMessage] = []
