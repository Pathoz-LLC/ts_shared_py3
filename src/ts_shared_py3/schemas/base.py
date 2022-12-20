from __future__ import annotations
import marshmallow as ma

from marshmallow import SchemaOpts  # validates_schema, ValidationError
from typing import Any, AnyStr

#
from .ndbkey_jwt import NdbKeyField
from ..constants import (
    ISO_8601_DATE_FORMAT,
    ISO_8601_DATETIME_FORMAT,
    ISO_8601_TIME_FORMAT,
)


class _ReplaceWithRealDataClass:
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


class DataClassBaseSchema(ma.Schema):
    """use this superclass for dataclass objects
    make sure you set the __model__ property
    in all subclasses

    __model__ is a class variable

    _makeModelObj causes schema deserialization to return
    an instance of the model class
    """

    # OPTIONS_CLASS = SchemaCfgOpts

    __model__ = _ReplaceWithRealDataClass

    class Meta:
        dateformat = ISO_8601_DATE_FORMAT  # "%Y-%m-%d"
        datetimeformat = ISO_8601_DATETIME_FORMAT
        timeformat = ISO_8601_TIME_FORMAT

    @ma.post_load
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
