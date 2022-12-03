# from datetime import date
# from common.enums.sex import Sex
from ..models.person import Person, PersonLocal, PersonKeys

# from common.messages.person import Person, PersonLocal


class PersonIO(object):
    """ """

    @staticmethod
    def loadByPhone(phoneStr):
        # Type: str, Person
        return PersonKeys.searchByPhone(phoneStr)

    @staticmethod
    def storePerson(person):
        key = person.put()
        person.key = key
