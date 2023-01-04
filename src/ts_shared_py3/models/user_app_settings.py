import google.cloud.ndb as ndb
from .baseNdb_model import BaseNdbModel
from ts_shared_py3.api_data_classes.user import AppSettingsMsg


class UserAppSettings(BaseNdbModel):
    """
    key is set same as userId to make it fast to retrieve
        per app-user values;  merged w User for return to client
        userKey = ndb.KeyProperty(User, required=True)
        defaults & config
    """

    # prefs & security
    allowIncidentTracking = ndb.BooleanProperty(default=True)  # global vs per-prospect
    # interruptions
    # user ID's to not show incidents or allow chat
    blockedUserList = ndb.StringProperty(repeated=True)
    autoLockAfterMinutes = ndb.IntegerProperty(default=0)

    def asMsg(self):
        msg = AppSettingsMsg()
        msg.allowIncidentTracking = self.allowIncidentTracking
        msg.allowPushNotifications = True
        msg.blockedUserList = self.blockedUserList
        msg.autoLockAfterMinutes = self.autoLockAfterMinutes
        return msg

    @staticmethod
    def get_or_create_by_user_id(userId):
        #
        q = UserAppSettings.get_by_id(userId)
        if not q:
            q = UserAppSettings(id=userId)
            q.put()
        return q  # found or none

    def updateFromAppSettingsMsg(self, msg):
        self.allowIncidentTracking = msg.allowIncidentTracking
        self.autoLockAfterMinutes = msg.autoLockAfterMinutes
        if msg.unblockAllUsers:
            self.blockedUserList = []
        self.put()
