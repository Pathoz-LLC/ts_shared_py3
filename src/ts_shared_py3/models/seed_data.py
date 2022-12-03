import google.cloud.ndb as ndb
from .baseNdb_model import BaseNdbModel


class SeedDataConfig(BaseNdbModel):
    # tracks population of seed data when instances start
    # empty DB will always create this record with "create" flags below set to true

    createSurveys = ndb.BooleanProperty(default=True)
    createSurveyQuestions = ndb.BooleanProperty(
        default=True
    )  # initially only the deception tell questions
    loadBehaviors = ndb.BooleanProperty(
        default=True
    )  # niu because this data is loaded from yaml on very instance startup
    loadUsers = ndb.BooleanProperty(default=True)  # only one test user

    @staticmethod
    def load():
        # creates record if not exists
        sdc = SeedDataConfig.get_by_id(1)
        if sdc == None:
            sdc = SeedDataConfig(id=1)
            sdc.put()

        return sdc

    @staticmethod
    def reloadIsRequired():
        # returns True if SOME seed data should be updated at next instance startup
        sdc = SeedDataConfig.load()
        return sdc.createSurveys or sdc.createSurveyQuestions or sdc.loadUsers

    @staticmethod
    def setAsInvalid():
        # running this causes the system to REPLACE all seed data at next instance startup
        sdc = SeedDataConfig.load()
        sdc.createSurveys = True
        sdc.createSurveyQuestions = True
        sdc.loadUsers = True
        sdc.put()

    @staticmethod
    def setAsCurrent():
        # running this causes the system to ASSUME all seed data is current at next instance startup
        sdc = SeedDataConfig.load()
        sdc.createSurveys = False
        sdc.createSurveyQuestions = False
        sdc.loadUsers = False
        sdc.put()
