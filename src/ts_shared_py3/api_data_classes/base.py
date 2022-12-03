from __future__ import annotations

# from datetime import datetime, date, time

from dataclasses import dataclass, Field  # , field, fields, make_dataclass

# from marshmallow_dataclass import NewType, field_for_schema
# from dataclass_wizard import JSONWizard


# IPv4 = NewType('IPv4', str, validate=marshmallow.validate.Regexp(r'^([0-9]{1,3}\.){3}[0-9]{1,3}$'))


@dataclass
class BaseApiData:
    """simple dict of data-types from JSON payload"""

    def __init__(self, /, **kwargs) -> None:
        if len(kwargs) > 0:
            self.updateAttsFromDict(kwargs)

    def updateAttsFromDict(self: BaseApiData, kwArgsDict: dict[str, str]) -> None:
        for key, value in kwArgsDict.items():
            setattr(self, key, value)

    # def updateViaDictOrSchema(self, dictOrSchema):
    #     if isinstance(dictOrSchema, Schema):
    #         assert (dictOrSchema.many in [False, None], "one instance only")
    #         self._updateAtts(dictOrSchema.dump(many=False))
    #     elif isinstance(dictOrSchema, dict):
    #         self._updateAtts(dictOrSchema)
    #     else:
    #         raise Exception("invalid argument")

    # def blah(self: BaseApiData) -> None:
    #     # demo
    #     fld: Field = field_for_schema(date, metadata=dict(blah=123))
