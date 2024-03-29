from datetime import date
from typing import ClassVar, Type
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ..schemas.base import DataClassBaseSchema

# from ..enums.commitLevel import CommitLevel_Display
# from ..api_data_classes.tracking import TrackingPayloadMsgDc


@dataclass(base_schema=DataClassBaseSchema)
class ForgeIncidentMessage(BaseApiData):
    # to Forge an Incident
    use_id: str = field(default="", metadata=dict(required=True))
    per_id: int = field(default=0, metadata=dict(required=True))
    startTrackingDate: date = field(metadata=dict(required=False))
    other_per_id: int = field(default=0, metadata=dict(required=False))


ForgeIncidentMessage.Schema.__model__ = ForgeIncidentMessage
