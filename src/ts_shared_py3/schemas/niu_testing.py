from __future__ import annotations
import marshmallow as ma
from marshmallow import Schema, fields, validate, ValidationError

#
from common.enums.scoreRuleType import ScoreRuleType
from common.schemas.base import NdbBaseSchemaWithKey
from common.models.entry_adapter import InputEntryAdapter


class TestArgsSchema(Schema):
    # http://127.0.0.1:8080/api/scoring/recalc?name=dewey&age=33&city=Austin
    name = fields.Str(required=True)
    age = fields.Int(validate=validate.Range(18, 40))
    city = fields.Str(required=True, validate=validate.OneOf(["Austin", "Houston"]))


class InputEntryAdapterSchema(NdbBaseSchemaWithKey):
    """
    InputEntryAdapter recs stored in NDB
    are not passed over the wire so this class is NIU
    except for testing

    schema for testing only
    also demonstrates custom serialization and deserialization methods

    """

    __model__ = InputEntryAdapter  # override base class

    ruleType = ma.fields.Method(
        "_serializeRuleType", deserialize="_deserializeRuleType", required=True
    )
    occurDt = ma.fields.Date(required=True)
    args = ma.fields.List(ma.fields.Int, required=True)
    unScored = ma.fields.Bool(required=True)

    def _serializeRuleType(
        self: InputEntryAdapterSchema, scoreAdapter: InputEntryAdapter, **kwargs
    ) -> int:
        # print("_serializeRuleType:")
        # print(type(scoreAdapter))
        # print(scoreAdapter)
        return scoreAdapter.ruleType.value

    def _deserializeRuleType(
        self: InputEntryAdapterSchema, ruleTypeAsInt: InputEntryAdapter, **kwargs
    ):
        return ScoreRuleType(ruleTypeAsInt)
