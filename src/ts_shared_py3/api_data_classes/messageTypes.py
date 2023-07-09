from __future__ import annotations
from datetime import date
from typing import ClassVar, Type, List
from dataclasses import field, make_dataclass

from marshmallow_dataclass import dataclass, field_for_schema
from marshmallow import Schema, fields
import marshmallow as ma

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

    Schema: ClassVar[Type[Schema]] = DataClassBaseSchema


@dataclass(base_schema=DataClassBaseSchema)
class JsonMessage(BaseApiData):
    # used when Void msg is too uninformative
    json: str = field(default="")

    Schema: ClassVar[Type[Schema]] = DataClassBaseSchema


@dataclass(base_schema=DataClassBaseSchema)
class FilterMessage(BaseApiData):
    entityType: str = field(default="person")
    propertyName: str = field(default="monitorStatus")
    propertyValue: str = field(default="active")
    queryOp: str = field(default="==")

    Schema: ClassVar[Type[Schema]] = DataClassBaseSchema


@dataclass(base_schema=DataClassBaseSchema)
class FilterMessageCollectionMsg(BaseApiData):  # default_factory=lambda: [],
    #
    # throwing an error when used on person/loadFollowed
    # so iv'e stopped using it on server side
    items: list[FilterMessage] = field(
        metadata=dict(
            default_factory=lambda: [],
            marshmallow_field=fields.Nested(FilterMessage.Schema, many=True),
        ),
    )

    # def bs():
    #     a = ma.fields.List(fields.Nested(FilterMessage.Schema))
    #     return FilterMessageCollectionMsg(items=[])

    Schema: ClassVar[Type[Schema]] = DataClassBaseSchema


StatusMessage.Schema.__model__ = StatusMessage
JsonMessage.Schema.__model__ = JsonMessage
FilterMessage.Schema.__model__ = FilterMessage
FilterMessageCollectionMsg.Schema.__model__ = FilterMessageCollectionMsg
