from datetime import date
from typing import ClassVar, Type
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ..schemas.base import DataClassBaseSchema


def buildStatusMsg(code: str, msg: str, detail: str):
    dtl = detail or ""
    return StatusMessage(code=code, msg=msg, detail=dtl)


@dataclass(base_schema=DataClassBaseSchema)
class StatusMessage(BaseApiData):
    # used when Void msg is too uninformative
    code: str = field(default="")
    msg: str = field(default="")
    detail: str = field(default="")

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class JsonMessage(BaseApiData):
    # used when Void msg is too uninformative
    json: str = field(default="")

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class FilterMessage(BaseApiData):
    entityType: str = field(default="person")
    propertyName: str = field(default="monitorStatus")
    propertyValue: str = field(default="active")
    queryOp: str = field(default="==")

    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class FilterMessageCollectionMsg(BaseApiData):
    items: list[FilterMessage] = field(default_factory=lambda: [])

    Schema: ClassVar[Type[Schema]] = Schema


StatusMessage.Schema.__model__ = StatusMessage
JsonMessage.Schema.__model__ = JsonMessage
FilterMessage.Schema.__model__ = FilterMessage
FilterMessageCollectionMsg.Schema.__model__ = FilterMessageCollectionMsg
