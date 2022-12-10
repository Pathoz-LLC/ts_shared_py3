from datetime import date
import google.cloud.ndb as ndb
from ..enums.accountType import AccountType, NdbAcctTypeProp

# from common.utils.date_conv import lastDayOfMonth


class Subscription(ndb.Model):
    """origTransID is used to look up userID
    if app store processes a renewal while app is offline

    from: https://medium.com/@AlexFaunt/auto-renewing-subscriptions-for-ios-apps-8d12b700a98f

    If the user logs out of their account for your auth system and logs into a different account.
    Then they wont have a subscription as the user_id doesnt match in your user_subscriptions
    table, but they will have paid for one with Apple.
    The solution to this is when you receive a receipt, you should always look in the user_subscriptions
    table for a match based on environment and original_transaction_id. Meaning if the user_id is
    different it will be patched too, thus moving the subscription in your database from one
    user to the one who restored the purchases. This is seems bonkers to me, my instinct would
    be to reject the request if the user_id doesnt match, but this advice comes from
    experienced App developers, and seems in line with Apples priorities.
    """

    userID = ndb.StringProperty(indexed=True, default="")
    origTransID = ndb.StringProperty(indexed=True, default="")
    accountLevel = NdbAcctTypeProp(indexed=False, default=AccountType.FREE)
    expiresDt = ndb.DateProperty(indexed=False)
    origTransDt = ndb.DateProperty(indexed=False)  # when purchase happened
    # when last renewal or cancel happened
    lastRenewOrCancelDt = ndb.DateProperty(indexed=False)

    @staticmethod
    def loadByTrans(transID):
        qry = Subscription.query(Subscription.origTransID == transID)
        return qry.get()

    @staticmethod
    def loadOrCreate(userID, transID, accountLevel, expiresDt):
        key = Subscription.makeKey(userID, transID)
        sub = key.get()
        if sub is not None:
            return sub

        sub = Subscription.loadByTrans(transID)
        if sub is not None:
            # same transID but different userID
            sub.userID = userID
            sub.key = Subscription.makeKey(userID, transID)
            return sub

        return Subscription(
            userID=userID,
            origTransID=transID,
            accountLevel=accountLevel,
            expiresDt=expiresDt,
            origTransDt=date.today(),
            lastRenewOrCancelDt=date.today(),
        )

    @staticmethod
    def storeHistoryForUser(userID, transID, accountLevel, expiresDt):
        # called when IOS client sends receipt to server
        sub = Subscription.loadOrCreate(userID, transID, accountLevel, expiresDt)
        sub.expiresDt = expiresDt
        sub.lastRenewOrCancelDt = date.today()
        sub.put()

    @staticmethod
    def recordAccountLvlChange(userID, transID, accountLevel, expiresDt):
        # called when Apple subscription calls our /subscription/callback web-hook
        sub = Subscription.loadOrCreate(userID, transID, accountLevel, expiresDt)
        sub.expiresDt = expiresDt
        sub.lastRenewOrCancelDt = date.today()
        sub.accountLevel = accountLevel
        sub.put()

    @staticmethod
    def makeKey(userID, transID):
        keyStr = "{0}-{1}".format(userID, transID)
        return ndb.Key(Subscription, keyStr)
