from datetime import datetime
import google.cloud.ndb as ndb

# from .baseNdb_model import BaseNdbModel
from ..api_data_classes.user import UserCommunicationDetailsMsg


class UserInteractions(ndb.Model):
    """tracks chat history between TS users
        allows a FREE user to respond to chat initiated by a paid user
    Key is myUserID-->otherUserID
    """

    otherUserID = ndb.StringProperty(default=0, indexed=True)
    isBlocked = ndb.BooleanProperty(indexed=False, default=False)
    reportAsSpam = ndb.BooleanProperty(indexed=True, default=False)
    isVerifiedSpam = ndb.BooleanProperty(indexed=False, default=False)
    # when chat thread started
    chatStartDtTm = ndb.DateTimeProperty(indexed=False)
    # when other user last send push about msg
    lastChatNotifyDtTm = ndb.DateTimeProperty(indexed=False)
    canContinueChat = ndb.BooleanProperty(indexed=False, default=False)

    comments = ndb.StringProperty(indexed=False, default="")
    commonProspects = ndb.IntegerProperty(repeated=True, indexed=False)

    def updateFromMsg(self, msg: UserCommunicationDetailsMsg):
        assert isinstance(msg, UserCommunicationDetailsMsg), "wrong type"
        if msg.saveBlockedValChanges:
            self.isBlocked = msg.isBlocked
        if msg.saveSpamValChanges:
            self.reportAsSpam = msg.reportAsSpam

        self.comments += msg.comments

        if msg.prospectID > 0 and msg.prospectID not in self.commonProspects:
            self.commonProspects.append(msg.prospectID)

    @property
    def toMsg(self):
        canContinueChat = self.canContinueChat and self.otherUserHasNotBlockedMe
        return UserCommunicationDetailsMsg(
            otherUserID=self.otherUserID,
            prospectID=222333,  # required field
            isBlocked=self.isBlocked,
            reportAsSpam=self.reportAsSpam,
            saveBlockedValChanges=False,
            saveSpamValChanges=False,
            isVerifiedSpam=self.isVerifiedSpam,
            canContinueChat=canContinueChat,
            comments=self.comments,
        )

    @property
    def chatNotStarted(self):
        return self.chatStartDtTm is None

    @property
    def otherUserHasNotBlockedMe(self):
        return not self.otherUserRec.isBlocked

    @property
    def userID(self):
        return self.key.parent().string_id()

    @property
    def otherUserRec(self):
        # mirrored rec for the user you are chatting with
        return UserInteractions.loadOrCreate(self.otherUserID, self.userID)

    @property
    def shouldNotifyAboutChatMsgUpdate(self):
        #
        if self.lastChatNotifyDtTm is None:
            return True
        else:
            return (datetime.now() - self.lastChatNotifyDtTm).seconds > (20 * 60)

    def markOtherUserChatable(self, user):
        # only paid users can start conversations;  other users can continue them
        if user.isPaidUser:
            our = self.otherUserRec
            our.canContinueChat = True
            our.save()

    def updateChatDates(self, start=False, update=False):
        # chat details
        if start and self.chatStartDtTm is None:
            self.canContinueChat = True
            self.chatStartDtTm = datetime.now()

        if update:
            self.lastChatNotifyDtTm = datetime.now()

    def save(self):
        self.put()

    @staticmethod
    def loadOrCreate(myUserID, otherUserID):
        # reversing two args above will get the mirrored rec
        key = UserInteractions._makeKey(myUserID, otherUserID)
        rec = key.get()
        if rec is None:
            rec = UserInteractions(otherUserID=otherUserID, commonProspects=[])
            rec.key = key
        return rec

    @staticmethod
    def loadAllForUser(myUserID: str):
        userKey = ndb.Key("User", myUserID)
        qry = UserInteractions.query(ancestor=userKey)
        return qry.fetch(40)

    @staticmethod
    def _makeKey(myUserID: str, otherUserID: str):
        userKey = ndb.Key("User", myUserID)
        return ndb.Key("UserInteractions", otherUserID, parent=userKey)
