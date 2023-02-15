from __future__ import annotations
import time
from datetime import date, datetime, timedelta
import logging

#
import google.cloud.ndb as ndb

# from google.cloud.ndb.utils import logging_debug
#
# from firebase_admin import auth
# from google.auth.credentials import Credentials, CredentialsWithTokenUri

from user_webapp import WaUserToken, WaUser
from .baseNdb_model import BaseNdbModel
from ..enums.sex import Sex, NdbSexProp
from ..enums.accountType import AccountType, NdbAcctTypeProp


class UserToken(WaUserToken):  # BaseUserToken
    """tracks multi tokens for each user
    they can be logged in with several devices?
    """

    SUBJECT_BEARER = "bearer"

    # unique_model = Unique
    bearer_token_timedelta = timedelta(days=365)

    refresh_token = ndb.StringProperty()

    @classmethod
    def create(cls, user, subject, token=None):
        if subject == cls.SUBJECT_BEARER:
            user = str(user)
            token = token or security.generate_random_string(entropy=128)

            # Bearer tokens must be unique on their own, without a user scope.
            key = cls.get_key(user, subject, token)
            entity = cls(
                key=key,
                user=user,
                subject=subject,
                token=token,
                refresh_token=security.generate_random_string(entropy=128),
            )

            # Refresh tokens must be unique
            ok = cls.unique_model.create(
                "%s.refresh_token:%s" % (cls.__name__, entity.refresh_token)
            )
            if ok:
                entity.put()
                print("just wrote new token {0} for user {1}".format(token, user))
            else:
                logging.warning(
                    "Unable to create a unique user token for user %s", user
                )
                entity = None
        else:
            if len(token) > 499:
                # # ndb key ids limited to 500
                # print("Token:")
                # print(token)
                token = cls._extractSignatureFromJwt(token)
            entity = super(UserToken, cls).create(user, subject, token)

        return entity

    @classmethod
    def _extractSignatureFromJwt(cls, jwt):
        return jwt.split(".")[2]

    def expires_at(self):
        """Returns the datetime after which this token is no longer valid

        :returns:
            A datetime object after which this token is no longer valid.
        """
        if self.subject == self.SUBJECT_BEARER:
            return self.created + self.bearer_token_timedelta

        return None

    def is_expired(self):
        """Whether the token is past its expiry time

        :returns:
            True if the token has expired
        """
        return self.expires_at() <= datetime.now()


# user_id is the gitkit global id for this user
# fields available are listed here:
# https://developers.google.com/identity/toolkit/web/reference/relyingparty/verifyAssertion#response
SOCIAL_FIELDNAMES_TO_STORE = {
    "localId": True,
    "user_id": True,
    "gender": True,
    "displayName": True,
    "fullName": True,
    "nickName": True,
    "lastName": True,
    "firstName": True,
    "email": True,
    "city": True,
    "zip": True,
    "dob": True,
    "birthdate": True,
    "dateOfBirth": True,
    "age": True,
    "photo": True,
    "photoUrl": True,
    "language": True,
    "timeZone": True,
    "providerId": True,
    "federatedId": True,
}

# revised for Firebase auth
FIRAUTH_FIELDNAMES_TO_STORE = {
    "email": True,
    "user_id": True,
    "name": True,
    "picture": True,
}


class DbUser(WaUser):  # BaseUserExpando
    """
    user rec; includes data from social profile
        as an expando table, it will store whatever fields you attach
        below are the defaults
    """

    token_model = UserToken
    # Firebase fields:  should be same as user.id_ property
    # the Firebase user ID; must be indexed
    # bio fields
    handle = ndb.StringProperty(default="")
    name = ndb.StringProperty(indexed=True, default="")
    first = ndb.TextProperty(indexed=False, default="")
    last = ndb.StringProperty(indexed=True, default="")
    email = ndb.StringProperty(indexed=True, default="")
    phone = ndb.StringProperty(indexed=True)
    dob = ndb.DateProperty(indexed=False)
    #
    #  FIXME props below
    sex = NdbSexProp(required=True, default=Sex.NEVERSET, indexed=False)
    preferredSex = NdbSexProp(required=True, default=Sex.NEVERSET, indexed=False)
    photoUrl = ndb.TextProperty(indexed=False)
    # #  account info & security;  Free; Pro; Premium
    accountLevel = NdbAcctTypeProp(indexed=True, default=AccountType.FREE)
    # next field only applies to premium users
    premiumExpireDt = ndb.DateProperty(indexed=False, default=datetime.now())
    #  who they logged in with; eg facebook.com; fieldname governed by gitkit
    provider_id = ndb.TextProperty(indexed=False, default="Facebook")

    # # I dont think we need next 3 fields on this model
    # authToken = ndb.StringProperty(indexed=False)
    # refreshToken = ndb.StringProperty(indexed=False)   #  to get a new authToken later
    # expiresOn = ndb.DateTimeProperty(indexed=True)

    signUpDtTm = ndb.DateTimeProperty(auto_now=True, indexed=False)
    lastLogin = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    promoCode = ndb.TextProperty(indexed=False, default="")
    city = ndb.TextProperty(indexed=False, default="")
    state = ndb.TextProperty(indexed=False, default="")
    zip = ndb.TextProperty(indexed=False, default="")

    #  setup for push notify
    # only most recent token is stored here; older in ndb.ApnsToken
    # this field is only used to detect token change on the client
    pushNotifyRegToken = ndb.TextProperty(indexed=False, default="")
    pushNotifyAuthorized = ndb.BooleanProperty(default=False, indexed=False)
    # 0==IOS;  1==Android, 2==Web
    pushNotifyDeviceType = ndb.IntegerProperty(indexed=False, default=0)

    @classmethod
    def createFromProfileMsg(cls, msg, firUserAsDict):
        # sign-up (create account)

        user = cls.loadByEmailOrId(firAuthUserId=msg.userId)
        if user is not None:
            # client has called wrong API (user exists in DB from prior testing)
            # but the jwt was still validated so
            # go ahead & return a decent bearer token for ongoing API calls
            bearerToken = cls.create_bearer_token(msg.userId)
            return user, bearerToken

        authToken = cls.token_model.create(msg.userId, "auth", msg.jwt)
        bearerToken = cls.create_bearer_token(msg.userId)

        user = cls()
        # user.auth_ids.extend([authToken, bearerToken])
        user.accountLevel = (
            AccountType.ADMIN if msg.email.endswith("@pathoz.com") else AccountType.FREE
        )

        user.email = msg.email
        user.handle = msg.fullNameOrHandle
        user.name = msg.fullNameOrHandle

        user.first = ""
        user.last = ""
        # derive first & last name if possible
        if msg.first not in ["", None]:
            user.first = msg.first
            user.last = msg.last

        elif len(msg.fullNameOrHandle) > 3:
            parts = msg.fullNameOrHandle.split(" ")
            user.first = parts[0] if len(parts) > 0 else ""
            if len(parts) > 1:
                user.last = parts[1] if len(parts) == 2 else parts[len(parts) - 1]

        user.photoUrl = msg.photoUrl
        user.dob = msg.dob
        user.sex = msg.sex
        user.city = msg.city
        user.state = msg.state
        # user.zip = msg.zip

        user.promoCode = msg.promoCode
        user.signUpDtTm = datetime.now()
        user.lastLogin = datetime.now()
        user.provider_id = msg.authProvider
        user.pushNotifyDeviceType = msg.pushNotifyDeviceType

        # user.latitude = msg.latitude
        # user.longitude = msg.longitude
        # user.deviceID = msg.deviceID
        # user.deviceModel = msg.deviceModel

        # values extracted from the jwt (firebase auth) are in firUserAsDict
        # user.handle = firUserAsDict.get("handle", displayName)
        # user.name = firUserAsDict.get("displayName", displayName)
        # user.email = firUserAsDict.get("email", loginMsg.email)
        # user.phone = firUserAsDict.get("phoneNumber", loginMsg.phone)
        # user.photoUrl = firUserAsDict.get("photoURL", loginMsg.imageURL)

        user.key = ndb.Key(cls, msg.userId)
        user.put()
        return user, bearerToken

    @staticmethod
    def updateFromProfileMsg(msg):
        # user edited profile
        user = DbUser.loadByEmailOrId(firAuthUserId=msg.userId)
        if user is None:
            return DbUser()

        user.email = msg.email
        user.handle = msg.fullNameOrHandle
        user.name = msg.fullNameOrHandle
        user.first = msg.first
        user.last = msg.last

        user.photoUrl = msg.photoUrl
        user.dob = msg.dob
        user.sex = msg.sex
        user.city = msg.city
        # user.state = msg.state
        # user.zip = msg.zip
        # user.pushNotifyDeviceType = msg.pushNotifyDeviceType

        # user.latitude = msg.latitude
        # user.longitude = msg.longitude
        # user.deviceID = msg.deviceID
        # user.deviceModel = msg.deviceModel
        user.put()
        return user

    @staticmethod
    def updateLastLogin(userId, jwt):
        # refresh token & store login date

        authToken = DbUser.token_model.create(userId, "auth", jwt)
        user = ndb.Key(DbUser, userId).get()
        if user is None:
            print("This user does not exist!!")
            return None, None
        bearerToken = DbUser.create_bearer_token(userId)
        user.lastLogin = datetime.now()
        user.put()
        return user, bearerToken

    def asMsg(self):
        from ..api_data_classes.user import UserProfileMsg

        msg = UserProfileMsg()
        msg.userId = self.user_id
        msg.email = self.email
        msg.fullNameOrHandle = self.name
        msg.photoUrl = self.photoUrl
        msg.dob = self.dob
        msg.sex = "{0}".format(self.sex.value)
        msg.city = self.city
        msg.state = self.state
        msg.zip = self.zip

        msg.first = self.first
        msg.last = self.last
        msg.accountLevel = self.accountLevel.value

        # 0==IOS;  1==Android, 2==Web
        msg.pushNotifyDeviceType = self.pushNotifyDeviceType
        msg.deviceModel = "na"
        msg.deviceID = "na"
        msg.jwt = "na"

        msg.promoCode = "na"
        msg.authProvider = self.provider_id
        # print(msg)
        return msg

    @property
    def appPrefs(self):
        from ..models.user_app_settings import UserAppSettings

        return UserAppSettings.get_or_create_by_user_id(self.user_id)

    @property
    def isEntitledUser(self):
        # special users who have privs without paying
        return 3 <= self.accountLevel.value <= 6

    @property
    def subscriptionIsFullyPaid(self):
        # applys only to normal customers (not entitled)
        return self.accountLevel.value == 0 or self.premiumExpireDt > date.today()

    @property
    def isPaidUser(self):
        # applies to both normal customers and entitled users
        return (
            1 <= self.accountLevel.value <= 2 and self.subscriptionIsFullyPaid
        ) or self.isEntitledUser

    @property
    def isFreeUser(self):
        return not self.isPaidUser

    @property
    def isIOS(self):
        return self.pushNotifyDeviceType == 0

    # TODO consolidate user_id properties to just one below
    @property
    def user_id(self):
        return self.key.string_id()

    @property
    def id_(self):  # added 04/08 by DG;
        """firebase auth uid & User.id_
        are equivalent and both strings
        """
        return self.key.string_id()

    @property
    def name_(self):  # added 04/30 by DG
        l_name = "?"
        if self.first and self.last:
            l_name = self.first + " " + self.last
        elif self.first:
            l_name = self.first
        if len(l_name) < 3 and self.handle:
            l_name = self.handle
        if len(l_name) < 3 and self.email:
            l_name = self.email.split("@")[0]
        return l_name

    def _pre_put_hook(self):
        """runs at each put operation
        adds defaults to first, last & handle fields
        """
        pass
        # print('name:{0};  first:{1};  last:{2}'.format(self.name, self.first, self.last))
        # if self.first == '' and self.name != '':
        #     parts = self.name.split(' ')
        #     self.first = parts[0]
        #     if self.last == '':
        #         if len(parts) > 1:
        #             self.last = parts[1]
        #         else:
        #             self.last = 'unknown'
        # if self.handle == '' and self.first != '':
        #     firstStr = self.first
        #     self.handle = firstStr[:2] + self.last

    # def updateFromToken(self, token):
    #     self.authToken = token.token
    #     self.refreshToken = token.refresh_token
    #     epochSeconds = token.bearer_token_timedelta.total_seconds()
    #     now = datetime.now()
    #     self.expiresOn = now + timedelta(seconds=epochSeconds)
    #
    #     self.lastLogin = now
    #     # save_future = self.put_async()
    #     # return save_future

    @classmethod
    def get_by_bearer_token(cls, userId, token):
        """Returns a user object based on a user ID and oauth bearer token.

        :param token:
            The token string to be verified.
        :returns:
            A tuple ``(User, timestamp)``, with a user object and
            the token timestamp, or ``(None, None)`` if both were not found.
        """
        if not token:
            print("attempted search on empty token")
            return None, None

        # print("searching for user by token {0}".format(token))
        token_obj = cls.token_model.get(userId, "bearer", token)
        if token_obj:
            if not token_obj.is_expired():
                # print("found unexpired token")
                user = cls.get_by_id(token_obj.user)
                if user:
                    # print("found user for token")
                    return user, token_obj.created
            else:
                print(
                    "ERR in get_by_bearer_token: found EXPIRED token {0}".format(token)
                )
        else:
            print("ERR in get_by_bearer_token: no token found {0}".format(token))

        return None, None

    @classmethod
    def create_bearer_token(cls, user_id):
        """Creates a new oauth bearer token for a given user ID.

        :param user_id:
            User unique ID.
        :returns:
            A token object, or None if one could not be created.
        """
        return cls.token_model.create(user_id, "bearer")

    @classmethod
    def get_by_auth_token(cls, user_id, token):
        """Returns a user object based on a user ID and token.

        :param user_id:
            The user_id of the requesting user.
        :param token:
            The token string to be verified.
        :returns:
            A tuple ``(User, timestamp)``, with a user object and
            the token timestamp, or ``(None, None)`` if both were not found.
        """
        tokenSignature = cls.token_model._extractSignatureFromJwt(token)
        token_key = cls.token_model.get_key(user_id, "auth", tokenSignature)
        user_key = ndb.Key(cls, user_id)
        # Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
            timestamp = int(time.mktime(valid_token.created.timetuple()))
            return user, timestamp

        return None, None

    # def propertyByName(self):
    #     ''' from:    https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/appengine/ndb/entities/snippets.py
    #         def get_properties_defined_on_expando(e):
    #             return e._properties
    #             # {
    #             #     'foo': GenericProperty('foo'),
    #             #     'bar': GenericProperty('bar'),
    #             #     'tags': GenericProperty('tags', repeated=True)
    #             # }
    #
    #     def demonstrate_right_way_to_query_expando():
    #         # for expando properties only
    #         User.query(ndb.GenericProperty('location') == 'SF')
    #     '''
    #     pass

    @staticmethod
    def loadByEmailOrId(email="", firAuthUserId=""):
        if len(firAuthUserId) > 2:
            user = ndb.Key(DbUser, firAuthUserId).get()
        else:
            userQuery = DbUser.query(DbUser.email == email)
            user = userQuery.get()
        return user

    @classmethod
    def makeNewAuthorizedUser(cls: DbUser, uid: str, email: str, token: str) -> DbUser:
        uKey = ndb.Key(DbUser, uid)
        u = uKey.get()
        # print("user:{0}".format(u))
        if u == None:
            u = DbUser()
            u.key = uKey
            u.email = email
            u.authToken = token
            u.refreshToken = token
            u.first = "gen by"
            u.last = "admin console"
            u.handle = "testUserOnly"
            u.expiresOn = datetime.now() + timedelta(weeks=4)
            u.pushNotifyAuthorized = True
            u.sex = Sex.UNKNOWN
            u.put()
        # cls.token_model.create(uid, "bearer", token)
        return u
