from __future__ import annotations

from datetime import date, datetime
from typing import ClassVar, Type, Optional
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

#
from .base import *

"""Important Note:
    it is vital that you set the Schema.__model__
    equal to the Classname
    this will allow creation & return of actual Model instances
    inside our endpoints
"""


@dataclass(base_schema=DataClassBaseSchema)
class CommunityNewsDc(BaseApiData):
    surveyId: int = field(default=2)
    personId: int = field(default=0, metadata=dict(required=True))
    priorMonthsToLoad: int = field(
        default=3,
        metadata=dict(
            required=False,
            validate=validate.Range(min=1, max=12),
        ),
    )
    #
    Schema: ClassVar[Type[Schema]] = Schema


CommunityNewsDc.Schema.__model__ = CommunityNewsDc
