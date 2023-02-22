from __future__ import annotations
from datetime import datetime, date, timedelta

import google.cloud.ndb as ndb

#
from ..enums.createAndMonitor import (
    CreateReason,
    MonitorStatus,
    NdbCreateReasonProp,
    NdbMonitorStatusProp,
)
from ..enums.remind_freq import NdbRemindProp, RemindFreq, ReminderFreqSerializedMa
from ..enums.sex import Sex, NdbSexProp
from .baseNdb_model import BaseNdbModel
from .values_beh_cat import UserAnswerStats


# might set the 1st 5 vals of appUnique (mobile phone) as
# parent/ancestor to group similar vals and keep ACID within that space
from ..enums.sex import Sex
from ..enums.commitLevel import CommitLevel_Display, NdbCommitLvlProp
from ..api_data_classes.person import PersonFullLocalRowDc, PersonLocalRowDc
from .person_keys import PersonKeys, KeyTypeEnum
from .user import DbUser

# advanced filter building and usage
# field = "city"
# operator = "="
# value = "London"
# f = ndb.query.FilterNode(field, operator, value)
# q = q.filter(f)


# from google.appengine.api import app_identity
# from google.appengine.api import urlfetch

# previous_namespace = namespace_manager.get_namespace()
# namespace_manager.set_namespace('default')


# MON_STATUS_DICT = MonitorStatus.to_dict()


class Person(BaseNdbModel):
    # used to store people followed by app users
    # key is Int64
    # our actual "user" model is an abstraction more closely related to the
    # authorization and entitlements entity  (oauth; gitkit, etc)
    # id will be long-int generated by app-engine

    # mobileKey = ndb.KeyProperty(Mobile)   #  niu
    # loginToken = ndb.StringProperty(default='') # niu
    # privs = ndb.StringProperty(indexed=False)   # niu

    mobile = ndb.TextProperty(
        indexed=False
    )  # INTERNATIONAL MOBILE stored in case fail in personKeys.put()
    first = ndb.TextProperty(indexed=False)
    last = ndb.StringProperty()
    alias = ndb.TextProperty(indexed=False)  # anon handle for chatting
    email = ndb.StringProperty(indexed=True)
    dob = ndb.DateProperty(indexed=False)
    sex = NdbSexProp(indexed=False, default=Sex.UNKNOWN)
    # 0 means no RedFlags; bits 1,2,4,8 mean convicted of:
    # REVENGE, CATFISH, CHEATED, DATERAPE
    redFlagBits = ndb.IntegerProperty(default=0, indexed=False)

    # street = ndb.StringProperty()
    city = ndb.TextProperty(indexed=False)
    state = ndb.TextProperty(indexed=False)
    zip = ndb.StringProperty()
    # zip_4 = ndb.StringProperty()
    tags = ndb.TextProperty(indexed=False)  # available for any use
    xtra = ndb.TextProperty(indexed=False)

    # auto vals
    addDateTime = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    modDateTime = ndb.DateTimeProperty(auto_now=True, indexed=False)

    # special cache overrides
    # _use_cache = True       # in context cache
    # _use_memcache = True
    # _use_datastore = False
    @staticmethod
    def searchByPhone(phoneString: str):
        from ..models.person_keys import PersonKeys

        # print('searching Person by phone on %s  (%s)' % (phoneString, type(phoneString)) )
        return PersonKeys.searchByPhone(phoneString)

    @staticmethod
    def appendRequiredToMsg(msg):
        if msg.is_initialized():
            return
        # msg.nickname = msg.get_assigned_value('nickname') or ''
        # msg.devotionLevel = msg.get_assigned_value('devotionLevel') or ''

    # def _save(person, isNew=False):
    #     # enforce model itegrity here
    #     # called by all below storage methods
    #     # could also be done on the pre-post-hook
    #     if isNew:
    #         assert person.key == None, 'trying to create new but actually replacing'
    #     person.put()
    #     return person

    def asFullLocDc(
        self: Person, perId: int, personLocalRec: PersonLocal
    ) -> PersonFullLocalRowDc:
        selfProps = self.to_dict()
        selfProps["id"] = perId
        # remove fields not on the msg
        del selfProps["tags"]
        del selfProps["xtra"]
        pf = PersonFullLocalRowDc(**selfProps)
        pf.nickname = personLocalRec.nickname
        pf.commitLevel = personLocalRec.commitLevel
        pf.reminderFrequency = personLocalRec.reminderFrequency
        pf.tsConfidenceScore = personLocalRec.recentTsConfidenceScore
        pf.imagePath = personLocalRec.imagePath
        pf.monitorStatus = personLocalRec.monitorStatus
        return pf

    def add_identifier(self, value, keyType):
        # actually stores the value
        assert isinstance(keyType, KeyTypeEnum), "must be a KeyTypeEnum"
        PersonKeys.attachFor(self, value, keyType)
        # remove cache to force reload from DB
        self._idents = None

    @property
    def identifiers(self):
        if self._idents == None:
            self._idents = PersonKeys.load(self)
        return self._idents

    @property
    def id(self):
        if self.key is None:
            return 0
        return self.key.id()

    # @staticmethod
    # def getByPhone(intlNumber ):
    #     mobileKey = Mobile.makeKey(intlNumber)
    #     person = Person.query(Person.mobileKey == mobileKey).get()
    #     return person      # [0] if len(person) > 0 else None

    # @staticmethod
    # def addNew(person):
    #     return person._save( True)

    @staticmethod
    def updateExisting(person):
        # add person as user
        # validateNewPerson(person)
        return person.put()

    # @classmethod
    # def _get_kind(cls):
    #     return "per"

    # sample async process (returns a future)
    # @ndb.tasklet
    # def someAsyncTasklet():
    #     boo = yield model.get_async()
    #     raise ndb.Return(boo)

    def _pre_put_hook(self):
        """runs at each put operation"""
        self.modDateTime = datetime.now()
        if self.alias == None:
            self.alias = self.first

        # user added or updated

    # @classmethod
    # def _post_delete_hook(cls, key, future):
    #     pass    # user deleted

    # def __repr__(self):
    #     '''  '''
    #     return 'Person obj: Name:{0}  Ph#:({1})  Email:{2}'.format(self.first + self.last, self.mobile, self.email)


class PersonLocal(BaseNdbModel):
    """per app-user values;  merged with Person for return to client"""

    # UI vals
    nickname = ndb.TextProperty(indexed=False, required=True)
    # store literal vals from:  common.models.devotion_level.DevotionLevel
    # devotionLevel= ndb.StringProperty(indexed=False, default='CASUAL')
    commitLevel = NdbCommitLvlProp(
        required=True, default=CommitLevel_Display.CASUAL, indexed=False
    )
    imagePath = ndb.TextProperty(indexed=False, default="")
    # default to mid-range score of 50 for new prospects
    # this is the ImpactCommunity.APP score converted to range 0-100
    recentTsConfidenceScore = ndb.FloatProperty(indexed=False, default=50.0)

    # overallScore = ndb.IntegerProperty(indexed=False, default=0)  #  avg of the incident truth ratings plus math on quiz answers
    # # breachesTrust = ndb.BooleanProperty( default=False, indexed=False ) # niu
    # redFlagBits = ndb.IntegerProperty( default=0, indexed=False )

    # housekeeping vals
    monitorStatus = NdbMonitorStatusProp(default=MonitorStatus.ACTIVE)
    reminderFrequency = NdbRemindProp(indexed=False, default=RemindFreq.NEVER)
    createReason = NdbCreateReasonProp(
        required=True, default=CreateReason.RELATIONSHIP, indexed=False
    )
    addDateTime = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    modDateTime = ndb.DateTimeProperty(
        indexed=True
    )  # most recent Prospect/SO at top of all lists

    @property
    def userId(self):
        # return user ID
        return self.key.parent().string_id()

    @property
    def personId(self):
        # return prospect ID
        return self.key.integer_id()

    @property
    def userKey(self):
        # return user key
        return ndb.Key("User", self.userId)

    @property
    def personKey(self):
        # return prospect Key
        return ndb.Key("Person", self.personId)

    def getRelatedTrackingRec(self):
        from .tracking import Tracking

        return Tracking.loadByKeys(self.userKey, self.personKey)

    def _updateFromMsg(self, msg: PersonLocalRowDc) -> None:
        self.nickname = msg.nickname
        self.commitLevel = msg.commitLevel
        self.imagePath = msg.imagePath
        self.monitorStatus = msg.monitorStatus
        self.reminderFrequency = msg.reminderFrequency
        self.recentTsConfidenceScore = msg.tsConfidenceScore

    @staticmethod
    def _makeKey(userIdStr: str, personIdInt: int) -> ndb.Key:
        return ndb.Key(DbUser, userIdStr, PersonLocal, personIdInt)

    @staticmethod
    def fromFullMsg(pfwl: PersonFullLocalRowDc) -> PersonLocal:
        """convert msg into a PersonLocalRowMsg instance"""
        pl = PersonLocal()
        pl._updateFromMsg(pfwl.asLocalDc)
        return pl

    @staticmethod
    def createAndStore(
        userKey: ndb.Key, personKey: ndb.Key, persFullLocalMsg: PersonFullLocalRowDc
    ) -> ndb.Key:
        """app user could delete Prospect, then add them again later..
        check if he exists and update monitor status if he does
        """
        plKey = PersonLocal._makeKey(userKey.string_id(), personKey.integer_id())
        rec = plKey.get()
        if rec:
            rec._updateFromMsg(persFullLocalMsg)
            rec.put()
            return plKey

        pl = PersonLocal.fromFullMsg(persFullLocalMsg)
        pl.key = plKey
        pl.put()

        # clear user counts on values questions
        # dont want to zero answer counts;  pg 20/10/2
        # UserAnswerStats.zeroAllCatAnswerCounts(pl.userId)

        # add rec for by-prospect, activity date tracking
        from ..models.person_activity import PersonActivity

        PersonActivity.bumpFeeling(userKey.string_id(), personKey.integer_id(), True)
        return pl.key

    @staticmethod
    def appendRequiredToMsg(msg: PersonRowDc) -> None:
        """provides default vals for messages"""
        # if msg.is_initialized():
        #     return
        # msg.nickname = msg.get_assigned_value("nickname") or "notfound"
        # msg.co = msg.get_assigned_value("devotionLevel") or "na"
        pass

    @staticmethod
    def loadByUserKey(userKey: ndb.Key, asnc: bool = False):
        """loads all (even deleted or trust mode) for this user
        and then caller can filter based on value of monitorStatus
        return newest to oldest
        """
        q = PersonLocal.query(ancestor=userKey)
        q.order(
            -PersonLocal.modDateTime
        )  # should be descending sort so newest SO's at top
        if asnc:
            return q.fetch_async()
        else:
            return q.fetch()

    @staticmethod
    def getById(userKey: ndb.Key, personId: int) -> PersonLocal:
        """ """
        plKey = PersonLocal._makeKey(userKey.string_id(), personId)
        return plKey.get()

    @classmethod
    def getByPhone(cls, user: DbUser, phone: str) -> Person:
        # find specific phone #, then compare its parent (People) key to those followed by cur user

        personByPhone = Person.searchByPhone(phone)
        followedRecs = cls.loadByUserKey(user.key)
        # print("personByPhone:")
        # print(personByPhone)
        # print("\nfollowed people:")
        # print(followedRecs)
        if len([r for r in followedRecs if r.personKey == personByPhone.key]) < 1:
            return
        return personByPhone

        # personKeyRecs = PersonKeys.query(PersonKeys.value == phone, PersonKeys.keyType == KeyTypeEnum.MBPHONE).fetch()
        # personKeys = [ndb.Key("Person", p.key.parent().string_id()) for p in personKeyRecs]

    def appendToMsg(self, msg):
        msg.nickname = self.nickname
        msg.commitLevel = self.commitLevel.value
        msg.imagePath = self.imagePath
        # msg.overallScore = self.overallScore
        # msg.redFlagBits = self.redFlagBits
        msg.monitorStatus = str(self.monitorStatus)
        msg.modDateTime = self.modDateTime
        msg.reminderFrequency = self.reminderFrequency

    def to_dict(self):
        result = super(PersonLocal, self).to_dict()
        result["perId"] = self.personId
        return result

    # def updateFidelityScoreFromQuiz(self, howOftenBehavior, howTellingBehavior):
    #     ''' fidelity score calculated by users:
    #         "truth opinion" about incidents, and also
    #         votes on specific "deception tell" questions  (how often he does this & how strong a tell it is)
    #     '''
    #     print('FIXME:  updateFidelityScoreFromQuiz is not yet implemented')
    #     self.overallScore = howOftenBehavior
    #
    # def updateFidelityScoreFromIncident(self, truthString, incidentId):
    #     '''
    #     '''
    #     print('FIXME:  updateFidelityScoreFromIncident is not yet implemented')
    #     self.overallScore = 0

    def _pre_put_hook(self):
        self.modDateTime = datetime.now()

    @staticmethod
    def updateDevotionLevel(user, personKey, displayCommitLvlEnum):
        """keep person record and Tracking incidents in sync
        called by updateCurrentCommitmentFromTracker below
        """
        # q = PersonLocal.query(PersonLocal.userKey == user.key, PersonLocal.personKey == personKey)
        personLoc = PersonLocal.getById(user.key, personKey.integer_id())
        if personLoc:
            personLoc.devotionLevel = displayCommitLvlEnum
            personLoc.put()


if __name__ == "__main__":
    pass

    # print(MonitorStatus)
    # print(MonitorStatus.__dict__)
    # if not person:
    #     raise f3.NotFoundException()
    # if not person.key.kind() == 'per':
    #     raise f3.InvalidRequestException()
