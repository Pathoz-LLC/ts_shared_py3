import marshmallow as ma

#
from .ndbkey_jwt import NdbKeyField
from ..constants import ISO_8601_DATE_FORMAT


class _ReplaceWithRealDataClass:
    pass


class DataClassBaseSchema(ma.Schema):
    """use this superclass for dataclass objects
    make sure you set the __model__ property
    in all subclasses

    __model__ is a class variable
    """

    __model__ = _ReplaceWithRealDataClass

    class Meta:
        # fields = ('id', 'start_time', 'end_time')
        dateformat = ISO_8601_DATE_FORMAT  # "%Y-%m-%dT%H:%M:%S%z"

    @ma.post_load
    def _makeModelObj(self, loadedDataAsDict, **kwargs):
        return self.__model__(**loadedDataAsDict)


class NdbBaseSchemaWithKey(DataClassBaseSchema):
    """use this superclass for NDB model objects"""

    key = NdbKeyField(required=True)


# to generate a class
# def make_schema_for_dc(datacls: type) -> DataClassBaseSchema:

#     return type(
#         "DCSFor{0}".format(datacls.__name__),
#         (DataClassBaseSchema,),
#         {
#             "__model__": datacls,
#         },
#     )
