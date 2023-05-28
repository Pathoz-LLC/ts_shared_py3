from __future__ import annotations
import re
import phonenumbers as phnum
from typing import Optional
import google.cloud.ndb as ndb

# next line causes circular import
# from .person import Person, PersonLocal, PersonKeys
from ..enums.keyType import KeyTypeEnum, NdbKeyTypeProp
from .baseNdb_model import BaseNdbModel

# phoneUtil = phnum.phonenumberutil.PhoneNumberUtil()

# # DELETE_CHARS is for regular string
# DELETE_CHARS = string.ascii_letters + string.punctuation + string.whitespace
# # NON_DIGITS_MAP is for unicode vals
# NON_DIGITS_MAP = dict(
#     (ord(char), None)
#     for char in string.ascii_letters + string.punctuation + string.whitespace
# )


def normToIntlPhone(num: str) -> str:
    try:
        intlPn: phnum.PhoneNumber = phnum.parse(num, None)
        if phnum.is_valid_number(intlPn):
            return phnum.format_number(intlPn, phnum.PhoneNumberFormat.INTERNATIONAL)
        return ""
    except:
        return ""


# def _stripNonDigits(value: str):
#     # remove non-digits
#     # # print('searching Person by phone on %s  (%s)' % (value, type(value)) )
#     # if isinstance(value, str):  # unicode string
#     #     return value.translate(DELETE_CHARS)  # NON_DIGITS_MAP
#     # # elif isinstance(value, str):  # regular string
#     # #     return value.translate(None, DELETE_CHARS)
#     # else:  # unknown type
#     #     return str(value).translate(None, DELETE_CHARS)
#     return re.sub(r"[^0-9]", "", value)


class PersonKeys(BaseNdbModel):
    """
    Person record is ancestor to this record so all vals grouped
            Use:  PersonKeys.storeNewMobilePhone(phone, person)
    """

    keyType = NdbKeyTypeProp(required=True, default=KeyTypeEnum.MBPHONE)
    value = ndb.StringProperty(required=True, indexed=True)
    # from .person import Person  # get Person class

    @staticmethod
    def storeMobileFor(person: Person, phone: str) -> None:
        PersonKeys.attachFor(person, phone)
        # return

    @staticmethod
    def attachFor(
        personAsParent: Person, value: str, keyType: KeyTypeEnum = KeyTypeEnum.MBPHONE
    ) -> None:
        #
        if len(value) < 1:
            return

        assert isinstance(
            keyType, KeyTypeEnum
        ), "implement cast from string to KeyTypeEnum.Int if you need that"
        if keyType.isPhone:
            value = normToIntlPhone(value)
        # assert isinstance(parent, Person)
        pkey = PersonKeys(keyType=keyType, value=value, parent=personAsParent.key)
        pkey.put()

    @staticmethod
    def searchByPhone(phoneString: str) -> Optional[Person]:  # ndb.AND
        phoneString = normToIntlPhone(phoneString)
        if len(phoneString) < 1:
            return
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
    def load(person: Person) -> list[PersonKeys]:  # : Person
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
