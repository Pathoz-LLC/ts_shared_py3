from __future__ import annotations
import decimal
from datetime import datetime, date, time, timedelta
from marshmallow_dataclass import dataclass
from marshmallow import Schema, post_load
import marshmallow.fields as ma_fields
from typing import Any, AnyStr

#
from .ndbkey_jwt import NdbKeyField
from ..constants import (
    ISO_8601_DATE_FORMAT,
    ISO_8601_DATETIME_FORMAT,
    ISO_8601_TIME_FORMAT,
)
from ..enums.sex import Sex, SexSerializedMa
from ..enums.accountType import AccountType, AcctTypeSerializedMsg


@dataclass
class _ReplaceWithRealDataClass:
    # niu = ma_fields.Enum(Sex.UNKNOWN)
    pass


# class SchemaCfgOpts(SchemaOpts):
#     """Same as the default class Meta options, but adds "name" and
#     "plural_name" options for enveloping.
#     """

#     def __init__(self, meta, **kwargs):
#         SchemaOpts.__init__(self, meta, **kwargs)
#         self.dateformat = getattr(meta, "dateformat", None)
#         self.datetimeformat = getattr(meta, "datetimeformat", None)
#         self.timeformat = getattr(meta, "timeformat", None)


class DataClassBaseSchema(Schema):
    """use this superclass for dataclass objects
    make sure you set the __model__ property
    in all subclasses

    __model__ is a class variable

    _makeModelObj causes schema deserialization to return
    an instance of the model class
    """

    __model__ = _ReplaceWithRealDataClass
    TYPE_MAPPING = {
        str: ma_fields.String,
        bytes: ma_fields.String,
        datetime: ma_fields.DateTime,
        float: ma_fields.Float,
        bool: ma_fields.Boolean,
        tuple: ma_fields.Raw,
        list: ma_fields.Raw,
        set: ma_fields.Raw,
        int: ma_fields.Integer,
        # uuid.UUID: ma_fields.UUID,
        time: ma_fields.Time,
        date: ma_fields.Date,
        timedelta: ma_fields.TimeDelta,
        decimal.Decimal: ma_fields.Decimal,
        # custom below
        Sex: SexSerializedMa,
        AccountType: AcctTypeSerializedMsg,
    }
    # OPTIONS_CLASS = SchemaCfgOpts

    class Meta:
        dateformat = ISO_8601_DATE_FORMAT  # "%Y-%m-%d"
        datetimeformat = ISO_8601_DATETIME_FORMAT
        timeformat = ISO_8601_TIME_FORMAT

    @post_load
    def _makeModelObj(
        self: DataClassBaseSchema, loadedDataAsDict: dict[AnyStr, Any], **kwargs
    ):
        return self.__model__(**loadedDataAsDict)

    # def handle_error(self: DataClassBaseSchema, exc, data: dict[AnyStr, Any], **kwargs):
    #     """Log and raise our custom exception when (de)serialization fails."""
    #     # logging.error(exc.messages)
    #     # raise AppError("An error occurred with input: {0}".format(data))
    #     print("{0} received:".format(__class__.__name__))
    #     print(data)

    # @validates_schema
    # def print_incoming(self: DataClassBaseSchema, data: dict[str, Any], **kwargs):
    #     print("{0} received:".format(__class__.__name__))
    #     print(data)


#
#
#
#
#


# class NdbBaseSchemaWithKey(DataClassBaseSchema):
#     """use this superclass for NDB model objects"""

#     key = NdbKeyField(required=True)


# to generate a class
# def make_schema_for_dc(datacls: type) -> DataClassBaseSchema:

#     return type(
#         "DCSFor{0}".format(datacls.__name__),
#         (DataClassBaseSchema,),
#         {
#             "__model__": datacls,
#         },
#     )
