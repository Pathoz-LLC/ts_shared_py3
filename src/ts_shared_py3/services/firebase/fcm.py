from firebase_admin import messaging
from .admin import tsFirebaseApp

# docs: https://github.com/firebase/firebase-admin-python/blob/master/firebase_admin/messaging.py
# https://firebase.google.com/docs/reference/admin/python/firebase_admin.messaging.html#send


# alertForAps = messaging.ApsAlert    # used to construct Aps
# stdDataPayload = messaging.Aps  # used to construct APNSPayload
# fullCustomPayload = messaging.APNSPayload   # used to construct a msg

# configForMsg = messaging.APNSConfig
# whatToInclude = messaging.Notification
# whatToSend = messaging.Message


def sendPushMsg(msg):
    """dispatch msg to FCM"""
    return messaging.send(msg, app=tsFirebaseApp)
