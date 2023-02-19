from __future__ import annotations
import string
import google.cloud.ndb as ndb

#
from ..enums.keyType import KeyTypeEnum, NdbKeyTypeProp
from .baseNdb_model import BaseNdbModel


# DELETE_CHARS is for regular string
DELETE_CHARS = string.ascii_letters + string.punctuation + string.whitespace
# NON_DIGITS_MAP is for unicode vals
NON_DIGITS_MAP = dict(
    (ord(char), None)
    for char in string.ascii_letters + string.punctuation + string.whitespace
)


def stripNonDigits(value):
    # remove non-digits
    # print('searching Person by phone on %s  (%s)' % (value, type(value)) )
    if isinstance(value, str):  # unicode string
        return value.translate(NON_DIGITS_MAP)
    elif isinstance(value, str):  # regular string
        return value.translate(None, DELETE_CHARS)
    else:  # unknown type
        return str(value).translate(None, DELETE_CHARS)


class PersonKeys(BaseNdbModel):
    """
    Person record is ancestor to this record so all vals grouped
            Use:  PersonKeys.storeNewMobilePhone(phone, person)
    """

    keyType = NdbKeyTypeProp(required=True, default=KeyTypeEnum.MBPHONE)
    value = ndb.StringProperty(required=True, indexed=True)
    # from .person_model import Person     # get Person class

    @staticmethod
    def storeMobileFor(person, phone):
        phone = stripNonDigits(phone)
        PersonKeys.attachFor(person, phone)
        # return

    @staticmethod
    def attachFor(personAsParent, value, keyType=KeyTypeEnum.MBPHONE):
        # if not keyType.isdigit():
        #     keyType = KeyType.by_string(keyType)
        assert isinstance(
            keyType, KeyTypeEnum
        ), "implement cast from string to KeyTypeEnum.Int if you need that"
        # assert isinstance(parent, Person)
        pkey = PersonKeys(keyType=keyType, value=value, parent=personAsParent.key)
        pkey.put()

    @staticmethod
    def searchByPhone(phoneString: str):  # ndb.AND
        phoneString = stripNonDigits(phoneString)
        pkRec = PersonKeys.query(
            PersonKeys.value == phoneString, PersonKeys.keyType == KeyTypeEnum.MBPHONE
        ).get()

        # print('searchByPhone on "{0}" {1}'.format(phoneString, 'found someone' if pkRec else 'DID NOT find anyone'))
        # print(pkRec)

        if pkRec and isinstance(pkRec, PersonKeys):
            person = pkRec.key.parent().get()
            return person
        else:
            return None

    @staticmethod
    def load(person) -> list[PersonKeys]:  # : Person
        return PersonKeys.query(ancestor=person.key).fetch()


# class Mobile(Model):
#     # all unique mobile #'s
#     # does not even have to be stored
#     # @classmethod
#     # def getNew(cls, intlNumber):
#     #     return cls.get_or_insert( Mobile.makeKey(intlNumber) )
#     #
#     # @classmethod
#     # def load(cls, intlNumber):
#     #     return Mobile.makeKey(intlNumber).get()
#
#     @staticmethod
#     def makeKey(intlNumber):
#         # intl number looks like:  +15127853885
#         # so area/parent would be:  '512785'
#         assert intlNumber != None, 'empty # sent to Mobile.makeKey'
#         area = intlNumber[2:8]
#         # ar stands for area
#         return ndb.Key('ar', area, 'Mobile', intlNumber)
