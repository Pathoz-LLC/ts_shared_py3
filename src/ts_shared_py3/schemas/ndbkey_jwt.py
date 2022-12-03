import marshmallow as ma
import google.cloud.ndb as ndb
from marshmallow import EXCLUDE
from marshmallow.validate import Length


class NdbKeyField(ma.fields.Field):
    """Field that serializes and deserializes part of a NdbKey"""

    def _serialize(self, ndbKey, attr, obj, **kwargs):
        return ndbKey.urlsafe().decode("utf-8")

    def _deserialize(self, urlSafeValAsStr, attr, data, **kwargs):
        # print("urlSafeValAsStr:")
        # print(urlSafeValAsStr)
        # assert (isinstance(urlSafeValAsStr, str), "")
        encoded = bytes(urlSafeValAsStr, "utf8")
        try:
            return ndb.Key(urlsafe=encoded)
        except ValueError as error:
            raise ma.ValidationError("invalid bytestr") from error


class NdbKeySchema(ma.Schema):
    """ """

    # __model__ = ndb.Key
    key = NdbKeyField(required=True)


class JWTSchema(ma.Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    access_token = ma.fields.Str()
    token_type = ma.fields.Str()
    expires = ma.fields.Str()


class AuthArgsSchema(ma.Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    user = ma.fields.Str(required=True, validate=Length(min=10, max=60))
    bearerToken = ma.fields.Nested(JWTSchema)
