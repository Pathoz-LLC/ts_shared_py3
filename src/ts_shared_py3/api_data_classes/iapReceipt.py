from datetime import date
from typing import ClassVar, Type
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ..schemas.base import NdbBaseSchema

# usage:
# from common.messages.iapReceipt import IapReceipt


@dataclass(base_schema=NdbBaseSchema)
class IapReceipt(BaseApiData):
    """raw data from apple receipts"""

    receiptAsB64EncStr: str = field(required=True)
    origTransID: str = field(required=True)


@dataclass(base_schema=NdbBaseSchema)
class IapVerify(BaseApiData):
    """ """

    status: int = field(default=0, required=True)
    oldAccountLevel: int = field(default=0, required=True)
    newAccountLevel: int = field(default=1, required=True)
