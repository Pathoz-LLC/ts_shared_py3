from __future__ import annotations
import decimal
from typing import Any, AnyStr, Dict, Optional, Union
from datetime import datetime, date, time, timedelta

#
from marshmallow_dataclass import dataclass
import marshmallow.fields as ma_fields
from marshmallow import (
    Schema,
    post_load,
    SchemaOpts,
    validates_schema,
    ValidationError,
    EXCLUDE,
    INCLUDE,
)

#
from ..enums.sex import Sex, SexSerializedMa
from ..enums.accountType import AccountType, AcctTypeSerialized
from ..enums.activityType import ActivityType, ActivTypeSerialized
from ..enums.commitLevel import CommitLevel_Display, CommitLvlSerializedMa
from ..enums.pushNotifyType import NotifyType, NotifyTypeSerializedMa
from ..enums.queued_work import QueuedWorkTyp, QwTypeSerialized
from ..enums.redFlag import RedFlagType, RedFlagTypeSerializedMa
from ..enums.remind_freq import RemindFreq, ReminderFreqSerializedMa
from ..enums.voteType import VoteType, VoteTypeSerializedMa
from ..enums.createAndMonitor import (
    CreateReason,
    CreateReasonSerializedMa,
    MonitorStatus,
    MonitorStatusSerialized,
)


from ..constants import (
    ISO_8601_DATE_FORMAT,
    ISO_8601_DATETIME_FORMAT,
    ISO_8601_TIME_FORMAT,
)


class SchemaMetaOpts(SchemaOpts):
    """Same as the default class Meta options, but adds "name" and
    "plural_name" options for enveloping.
    """

    def __init__(self: SchemaMetaOpts, meta, **kwargs):
        # print("SchemaMetaOpts")
        # print(meta.__name__)
        SchemaOpts.__init__(self, meta, **kwargs)
        self.dateformat = ISO_8601_DATE_FORMAT  # "%Y-%m-%d"
        self.datetimeformat = ISO_8601_DATETIME_FORMAT
        self.timeformat = ISO_8601_TIME_FORMAT
        # self.name = getattr(meta, "name", None)
        # self.plural_name = getattr(meta, "plural_name", self.name)


@dataclass
class _ReplaceWithRealDataClass:
    # niu: str = field(default="", metadata=dict(required=False))
    pass


class DataClassBaseSchema(Schema):
    """use this superclass for dataclass objects
    make sure you set the __model__ property
    in all subclasses

    __model__ is a class variable

    _makeModelObj causes schema deserialization to return
    an instance of the model class
    """

    # class Meta:
    #     # omit unknown schema fields
    #     unknown = EXCLUDE

    __model__ = _ReplaceWithRealDataClass
    OPTIONS_CLASS = SchemaMetaOpts
    TYPE_MAPPING = {
        str: ma_fields.String,
        bytes: ma_fields.String,
        float: ma_fields.Float,
        bool: ma_fields.Boolean,
        tuple: ma_fields.Raw,
        list: ma_fields.Raw,
        set: ma_fields.Raw,
        int: ma_fields.Integer,
        # uuid.UUID: ma_fields.UUID,
        datetime: ma_fields.DateTime,
        date: ma_fields.Date,
        time: ma_fields.Time,
        timedelta: ma_fields.TimeDelta,
        decimal.Decimal: ma_fields.Decimal,
        # custom ENUMS below
        Sex: SexSerializedMa,
        AccountType: AcctTypeSerialized,
        ActivityType: ActivTypeSerialized,
        CommitLevel_Display: CommitLvlSerializedMa,
        CreateReason: CreateReasonSerializedMa,
        MonitorStatus: MonitorStatusSerialized,
        NotifyType: NotifyTypeSerializedMa,
        QueuedWorkTyp: QwTypeSerialized,
        RedFlagType: RedFlagTypeSerializedMa,
        RemindFreq: ReminderFreqSerializedMa,
        VoteType: VoteTypeSerializedMa,
    }

    # @post_load
    # def _makeModelObj(
    #     self: DataClassBaseSchema, loadedDataAsDict: dict[AnyStr, Any], **kwargs
    # ):
    #     print("called post_load on {0}".format(__class__.__name__))
    #     print("dataTyp: ".format(type(loadedDataAsDict)))
    #     print("creating a {0}".format(self.__model__.__name))
    #     dc = self.__model__(**loadedDataAsDict)
    #     print("created a: {0}".format(type(dc)))
    #     return dc
    #     # if isinstance(loadedDataAsDict, dict):
    #     #     return self.__model__(loadedDataAsDict)
    #     # else:
    #     #     return self.__model__(loadedDataAsDict)

    # @validates_schema(pass_original=False, skip_on_field_errors=True)
    # def validate_whole_schema(
    #     self: DataClassBaseSchema, mapFromStrViaSchemaLoads: dict[str, Any], **kwargs
    # ):
    #     # runs after all fields have been validated
    #     print("payload being validated for {0}".format(__class__.__name__))

    def handle_error(
        self: DataClassBaseSchema,
        error: ValidationError,
        mapFromStrViaSchemaLoads: dict[AnyStr, Any],
        *,
        many: bool,
        **kwargs,
    ):
        """Log and raise our custom exception when (de)serialization fails."""
        # logging.error(exc.messages)
        # raise AppError("An error occurred with input: {0}".format(data))
        print("{0} had parse error {1} on:".format(__class__.__name__, error.messages))
        print(mapFromStrViaSchemaLoads)
        raise error


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
