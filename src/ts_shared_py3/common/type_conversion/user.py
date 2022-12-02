# from google.appengine.ext import ndb

# from common.enums.sex import Sex, NdbSexProp
# from common.enums.accountType import AccountType, NdbAcctTypeProp
# from google.appengine.ext.ndb import Query
import random
import constants
from ..models.user import User, UserToken
from ..api_data_classes.user import UserLoginMsg


class UserIO(object):
    """ """

    @staticmethod
    def loadUserByUniqueVal(searchMsg):
        # type: (UserLoginMsg) -> User
        """
        can search by email, phone, ID or token (in jwt field)
        but we don't have phone # for users
        Args:
            searchMsg:

        Returns: User rec or None if not found

        """
        if len(searchMsg.userId) > 0 or len(searchMsg.email) > 0:
            return User.loadByEmailOrId(
                email=searchMsg.email, firAuthUserId=searchMsg.userId
            )
        elif len(searchMsg.jwt) > 0:
            user, tokTimestmp = User.get_by_bearer_token(token=searchMsg.jwt)
            return user

        if len(searchMsg.phone) > 0:
            qry = User.query().filter(User.phone, "=", searchMsg.phone)

        return qry.get()  ## type: User

    @staticmethod
    def loadUserByID(userID):
        return User.loadByEmailOrId(firAuthUserId=userID)

    @staticmethod
    def getXRandUsers(count):
        if constants.IS_DEV_SERVER:
            offst = 0
        else:
            offst = random.randint(0, 300)
        qry = User.query()
        return qry.fetch(count, offset=offst)
