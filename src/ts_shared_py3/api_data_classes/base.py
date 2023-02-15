from __future__ import annotations
from typing import Any

from marshmallow_dataclass import dataclass, NewType

from marshmallow import validate

# from dataclasses import dataclass, Field  # , field, fields, make_dataclass
# from dataclass_wizard import JSONWizard
from ..schemas.base import DataClassBaseSchema

# IPv4 = NewType('IPv4', str, validate=validate.Regexp(r'^([0-9]{1,3}\.){3}[0-9]{1,3}$'))


@dataclass(base_schema=DataClassBaseSchema)
class BaseApiData:
    """simple dict of data-types from JSON payload"""

    def __init__(self: BaseApiData, **kwargs: dict[str, Any]) -> None:
        print("Dewey 3344:")
        print(type(kwargs))
        print(len(kwargs))
        if len(kwargs) > 0:
            self._updateAttsFromDict(kwargs)

    def _updateAttsFromDict(self: BaseApiData, kwargs: dict[str, Any]) -> None:  #
        for key, value in kwargs.items():
            setattr(self, key, value)

    # def __post_init__(self):
    #     # std way of validating required fields
    #     pass

    # def updateViaDictOrSchema(self, dictOrSchema):
    #     if isinstance(dictOrSchema, Schema):
    #         assert (dictOrSchema.many in [False, None], "one instance only")
    #         self._updateAtts(dictOrSchema.dump(many=False))
    #     elif isinstance(dictOrSchema, dict):
    #         self._updateAtts(dictOrSchema)
    #     else:
    #         raise Exception("invalid argument")
