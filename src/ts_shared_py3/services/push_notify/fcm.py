from random import randint
from collections import namedtuple
import google.cloud.ndb as ndb

from ..models.user import User
from ..models.person import PersonLocal
from .pn_exceptions import UserNotFoundErr, MissingReqFieldErr

# FIXME
from ..firebase.admin import tsFirebaseApp

# firebase api
from firebase_admin.messaging import Message, send
from firebase_admin.messaging import ApsAlert, Aps, APNSConfig, APNSPayload
from firebase_admin.messaging import AndroidConfig, AndroidNotification
from firebase_admin.exceptions import FirebaseError, NotFoundError

from common.enums.niu_pushNotifyType import NotifyType

import logging

log = logging.getLogger("values")


""" Push Notification steps:
lookup user token & device type (ios/android/web)
select NotifyType
construct either APNSPayload or AndroidNotification
embed either in respective Config type
embed token & config type into a msg
send msg
"""

# user vals from the DB
UserPushConfig = namedtuple("UserPushConfig", ["userID", "token", "isIOS"])


class PushNotifyTasks:
    """interface for building and sending push notification msgs
    to IOS & Android
    """

    @staticmethod
    def constructAndSendNotification(userID, notifyType, dataVals):
        """the main push method"""
        try:
            user = _loadUser(userID)
            userVals = _loadUserVals(user)  # returns a UserPushConfig
        except UserNotFoundErr:  # handle UserNotFound exception
            # TODO: log an error
            # print("Err: UserNotFound: {0} might be missing or nil push token".format(userID))
            log.error(
                "Err: UserNotFound: {0} not found {1}".format(userID, notifyType.name)
            )
            return
        except MissingReqFieldErr:
            # this user has no push token; bail out
            log.error(
                "Err: User: {0} is missing push token {1}".format(
                    userID, notifyType.name
                )
            )
            return

        # verify api user sent all required data
        _validateRequiredVals(notifyType, dataVals)
        # add fields & structure for EVERY msg
        dataVals["userID"] = userID
        dataVals["type"] = notifyType.name
        customPayload = dict(custom=dataVals)
        # print("customPayload:")
        # print(customPayload)

        # _makePushPayload returns messaging.Message
        pushMsg = _makePushPayload(
            notifyType, userVals.token, userVals.isIOS, customPayload
        )

        # special handling; PG wants a different string for paid users
        # if notifyType == NotifyType.VALS_QUEST_AVAIL and user.accountLevel.value > 0:
        #     # different body string for paid users
        #     paidMsg = 'Answer more questions to improve prospect score accuracy.'
        #     if userVals.isIOS:
        #         pushMsg.apns.payload.aps.alert.body = paidMsg
        #     else:
        #         pushMsg.android.notification.body = paidMsg

        # now send msg thru FCM
        try:
            pnMsgId = send(pushMsg, app=tsFirebaseApp)
            log.info(
                "TsPn sent {0} to {1} as {2}".format(notifyType.name, userID, pnMsgId)
            )
        except FirebaseError as e:
            log.error("FCM pn err: {0}".format(e.code))
            if isinstance(e, NotFoundError):
                # APNS is reporting token invalid;  user may have uninstalled the app
                # but some on SO are reporting that PN's still get delivered sometimes
                # we probably should clear token from user record here
                pass

    # @staticmethod
    # def testBruteForceSend():
    #     registration_token = 'caCFTgz7ZWw:APA91bEovu8wRFOiYlxks3bzRivJItqgIdjNFY58MvGVIZN8yG8NPnnkRxnNWqvNBRRmxEjufZEZFkGZrcTdBVMY1MJThmx18vOPsfltMTnGgTTVDaewNlMrjIhMXScgOv6YGukqZSCc'
    #
    #     # See documentation on defining a message payload.
    #     message = Message(
    #         data={
    #             'score': '850',
    #             'time': '2:45',
    #         },
    #         token=registration_token,
    #     )
    #     response = send(message)
    #     # Response is a message ID string.
    #     print('Successfully sent message:', response)

    @staticmethod
    def updateUserToken(userID, token="", deviceType=0):
        """0==IOS; 1==Android; 2==Web"""
        u = _loadUser(userID)
        u.pushNotifyRegToken = token
        u.pushNotifyDeviceType = deviceType
        u.pushNotifyAuthorized = len(token) > 5
        u.put()

    @staticmethod
    def registerInChannel(userID, remove=False):
        pass


def _loadUser(userID):
    return User.loadByEmailOrId(None, userID)
    # return ndb.Key(User, userID).get()


def _loadUserVals(u):
    if u == None:
        raise UserNotFoundErr
    elif u.pushNotifyRegToken in ["", None]:
        raise MissingReqFieldErr

    return UserPushConfig(u.user_id, u.pushNotifyRegToken, u.isIOS)


def _makePushPayload(notifyType, token, isIOS, dataVals):
    """ """
    assert isinstance(notifyType, NotifyType), "Wrong arg passed"
    if isIOS:
        return _makeIOSPayload(notifyType, token, dataVals)
    else:
        return _makeAndroidPayload(notifyType, token, dataVals)


def _makeIOSPayload(notifyType, token, fullPayload):
    """construct custom APNS msg"""

    customBody = _makeCustomBody(notifyType, fullPayload)

    apsAlert = ApsAlert(
        title=notifyType.title, subtitle=notifyType.subtitle, body=customBody
    )
    aps = Aps(
        alert=apsAlert,
        badge=notifyType.badge,
        sound=notifyType.sound,
        content_available=notifyType.contentAvail,
        category=notifyType.category,
    )
    payload = APNSPayload(aps, **fullPayload)
    config = APNSConfig(payload=payload)
    # can only send ONE of either token, topic or condition
    return Message(apns=config, token=token)  # , topic=notifyType.topic


def _makeAndroidPayload(notifyType, token, fullPayload):

    # flutter requires this key
    fullPayload["click_action"] = "FLUTTER_NOTIFICATION_CLICK"
    customBody = _makeCustomBody(notifyType, fullPayload)

    notify = AndroidNotification(
        title=notifyType.title,
        body=customBody,
        icon=notifyType.icon,
        sound=notifyType.sound,
        color=notifyType.color,
        tag=notifyType.tag,
    )
    config = AndroidConfig(notification=notify, data=fullPayload)
    # can only send ONE of either token, topic or condition
    return Message(android=config, token=token)  # , topic=notifyType.topic


def _validateRequiredVals(notifyType, customPayload):
    """only in place for testing
    disable at call point after all push notifications verified
    """
    for dKey in notifyType.requiredFields:
        if dKey not in customPayload:
            log.error(
                "Err: {0} not found in customPayload for {1}".format(
                    dKey, notifyType.name
                )
            )
            raise MissingReqFieldErr


def _makeCustomBody(notifyType, fullPayload):
    """4 of the push bodies need user values inserted
    Args:
        notifyType:
        fullPayload:

    Returns: custom body for push
    """
    # assert isinstance(notifyType, NotifyType), "oops"
    bodyTempl = notifyType.body
    if notifyType.bodyIsConstant:
        return bodyTempl

    customDict = fullPayload.get("custom")
    assert isinstance(customDict, dict), "oops"

    tmplVal = "_"
    if notifyType.bodyIncludesProspectName:
        personLocal = _lookupProspectLocal(customDict)
        tmplVal = personLocal.nickname
        if notifyType == NotifyType.CHAT_MSG_RECEIVED:
            # display some bs user ID until I can look it up from the incident
            userID = randint(300, 12000)
            return bodyTempl.format(tmplVal, userID)

    return bodyTempl.format(tmplVal)


def _lookupProspectLocal(customDict):
    personID = customDict.get("personID")
    userID = customDict.get("userID")
    userKey = ndb.Key(User, userID)
    return PersonLocal.getById(userKey, personID)