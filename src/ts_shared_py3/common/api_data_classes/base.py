from __future__ import annotations
from dataclasses import dataclass

# from dataclass_wizard import JSONWizard


@dataclass
class BaseApiData(JSONWizard):
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
