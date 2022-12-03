from datetime import date, datetime
from typing import ClassVar, Type
from dataclasses import field  # , fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema, validate

from .base import BaseApiData
from ..schemas.base import NdbBaseSchema
from ..enums.sex import Sex

# from common.utils.date_conv import date_to_message
import logging

# usage:
# from common.messages.user import UserIdMessage, UserXmppCreds, UserAccountMessage

# for creating & updating users; user_id is the GITKit userID--not ours
# UserBioMessage = model_message(User, exclude=('user_id', 'token_model') )

# dateTimeConverter = default_converters["DateTimeProperty"]


@dataclass(base_schema=NdbBaseSchema)
class UserProfileMsg(BaseApiData):
    """for creating user & also for
    updating their profile
    """

    userId: str = field(default="", required=True)
    email: str = field(default="", required=True)
    fullNameOrHandle: str = field(default="", required=True)
    photoUrl: str = field(default="", required=True)
    dob: date = field(required=True)
    sex: Sex = field(default=Sex.UNKNOWN, required=True)
    city: str = field(default="", required=True)
    state: str = field(default="", required=True)
    zip: str = field(default="", required=True)

    first: str = field(default="", required=True)
    last: str = field(default="", required=True)

    # 0==IOS;  1==Android, 2==Web
    pushNotifyDeviceType: int = field(default=0, required=True)

    deviceModel: str = field(default="na", required=True)
    deviceID: str = field(default="", required=True)

    promoCode: str = field(default="", required=True)
    authProvider: str = field(default="email", required=True)

    jwt: str = field(default="", required=True)
    latitude: float = field(default=0.0)
    longitude: float = field(default=0.0)
    accountLevel: int = field(default=0, required=True)

    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class AppSettingsMsg(BaseApiData):
    # support for app settings & batch operations
    allowIncidentTracking: bool = field(default=True)  # not in trust mode
    allowPushNotifications: bool = field(default=True)
    breakupArchiveAllProspects: bool = field(default=False)

    autoLockAfterMinutes: int = field(default=0, required=True)
    clearFeelingCheckReminders: bool = field(default=False)  # remove all alerts

    blockedUserList: str = field(default="", required=True)
    unblockAllUsers: bool = field(default=False)  # clears blocks on specific users
    # after sign-up or log-in, this bearer token goes in the header for subsequent requests
    apiToken: str = field(default="", required=True)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class UserAccountChangeMsg(BaseApiData):
    # when user buys a subscription to Gold or Diamond
    userId: str = field(default="", required=True)
    accountLevel: int = field(default=0, required=True)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class UserIdMessage(BaseApiData):
    """used for login and for other cases described below

    current app userID always comes in the endpoint request header
        this msg is only useful when you need to reference a different user
        eg request chat or block user
    """

    userId: str = field(default="", required=True)
    jwt: str = field(default="", required=True)
    #
    Schema: ClassVar[Type[Schema]] = Schema


# old msg types below


@dataclass(base_schema=NdbBaseSchema)
class UserDemographicsMsg(BaseApiData):
    handle: str = field(default="", required=True)
    name: str = field(default="", required=True)
    email: str = field(default="", required=True)
    phone: str = field(default="", required=True)
    dob: date = field(required=True)
    sex: str = field(default="", required=True)
    preferredSex: str = field(default="", required=True)
    imageURL: str = field(default="", required=True)
    city: str = field(default="", required=True)
    state: str = field(default="", required=True)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class UserBioMessage(BaseApiData):
    """
    current app userID always comes in the endpoint request header
        this msg is only useful when you need to reference a different user
        eg request chat or block user
    """

    userId: str = field(default="", required=True)
    handle: str = field(default="", required=True)
    first: str = field(default="", required=True)
    last: str = field(default="", required=True)
    name: str = field(default="", required=True)
    email: str = field(default="", required=True)
    phone: str = field(default="", required=True)
    dob: date = field(required=True)
    sex: int = field(default=0, required=True)
    preferredSex: int = field(default=0, required=True)
    photoUrl: str = field(default="", required=True)
    accountLevel: int = field(default=0, required=True)
    provider_id: str = field(default="", required=True)
    authToken: str = field(default="", required=True)
    refreshToken: str = field(default="", required=True)
    expiresOn: date = field(required=True)
    lastLogin: date = field(required=True)
    promoCode: str = field(default="", required=True)
    city: str = field(default="", required=True)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=NdbBaseSchema)
class UserCommunicationDetailsMsg(BaseApiData):
    """any updates or notifications related to another user

    canContinueChat & isVerifiedSpam are
    READABLE values only (client settings not respected)
    """

    otherUserID: str = field(default="", required=True)
    prospectID: int = field(default=0, required=True)

    # client settable vals
    # user wants to talk
    requestStartChat: bool = field(default=False)
    # new chat msg sent
    notifyThreadUpdated: bool = field(default=False)
    # blocking & reporting users
    isBlocked: bool = field(default=False)
    reportAsSpam: bool = field(default=False)
    saveBlockedValChanges: bool = field(default=False)
    saveSpamValChanges: bool = field(default=False)
    # change notes over time
    comments: str = field(default="", required=True)

    # client readable values
    canContinueChat: bool = field(default=False)
    isVerifiedSpam: bool = field(default=False)
    #
    Schema: ClassVar[Type[Schema]] = Schema


# check if next msg is in use
UserAccountMessage = compose(UserBioMessage, AppSettingsMsg)


@dataclass(base_schema=NdbBaseSchema)
class UserLoginMsg(BaseApiData):
    # sent for login & create user acct
    userId: str = field(default="", required=True)
    email: str = field(default="", required=True)
    name: str = field(default="", required=True)
    phone: str = field(default="", required=True)
    imageURL: str = field(default="", required=True)
    provider: str = field(default="", required=True)
    jwt: str = field(default="", required=True)
    isNewUser: bool = field(default=False)
    #
    Schema: ClassVar[Type[Schema]] = Schema

    # # old_access_token is used to unify users who choose differet IDP's for login
    # # gitkit will handle it automatically if user has same email at each IDP
    # old_access_token: str = field(default="", required=True)
    # idpProfileAtts = BaseApiDataField(UserBioMessage, 4, repeated=False)


def castUserAndSettingsToAcctMsg(user, appSettings):
    # msg = protopigeon.to_message(user, UserAccountMessage)
    msg = UserAccountMessage()
    msg.userId = user.id_
    logging.info("User email is: %s" % (user.email))
    msg.email = user.email

    msg.handle = user.last
    msg.first = user.first
    msg.last = user.last
    msg.name = user.name
    msg.phone = user.phone
    dobAsDate = user.dob

    if not dobAsDate is None and isinstance(dobAsDate, date):
        msg.dob = dobAsDate
    else:
        msg.dob = date(1994, 1, 1)
        logging.error(
            "dob is a %s & holds %s; setting to 1994" % (type(dobAsDate), dobAsDate)
        )
    msg.sex = user.sex
    msg.preferredSex = user.preferredSex
    msg.photoUrl = user.photoUrl
    msg.accountLevel = user.accountLevel
    msg.provider_id = user.provider_id
    msg.authToken = user.authToken
    msg.expiresOn = user.expiresOn
    msg.lastLogin = user.lastLogin
    msg.promoCode = user.promoCode

    # msg.email = user.email  # being dropped above
    # msg.handle = "" # user.handle
    msg.defaultCountryCode = appSettings.defaultCountryCode
    msg.trustMode = appSettings.trustMode
    # msg.userPin = appSettings.userPin
    # msg.requirePinToOpenApp = appSettings.requirePinToOpenApp
    # msg.autoLockAfterMinutes = appSettings.autoLockAfterMinutes
    msg.allowChatRequests = appSettings.allowChatRequests
    msg.enablePushNotifications = appSettings.enablePushNotifications
    # msg.disableNotifyOnAdd = appSettings.disableNotifyOnAdd
    # msg.poseQuestionFrequency = appSettings.poseQuestionFrequency
    msg.userId = user.id_
    # logging.debug('User Acct msg: UID={0}'.format(user.id_))
    assert user.id_ == user.user_id, "TS UIDs should match Firebase Auth UIDs"
    return msg
