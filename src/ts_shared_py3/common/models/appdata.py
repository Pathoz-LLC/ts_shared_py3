import google.cloud.ndb as ndb
from .baseNdb_model import BaseNdbModel


class AppConfig(BaseNdbModel):
    """singleton -- 1 row in table
    these values stored from the form at
        http://admin.api.touchstone.pathoz.com/config
        http://admin.playerbusterapi.appspot.com/config

    loaded by get_or_insert() with 'config' as the key value"""

    gcm_api_key = ndb.StringProperty()
    gcm_multicast_limit = ndb.IntegerProperty()
    apns_multicast_limit = ndb.IntegerProperty()
    apns_test_mode = ndb.BooleanProperty()
    apns_sandbox_cert = ndb.TextProperty()
    apns_sandbox_key = ndb.TextProperty()
    apns_cert = ndb.TextProperty()
    apns_key = ndb.TextProperty()
    update = ndb.DateTimeProperty(indexed=False, auto_now_add=True)

    @staticmethod
    def load():
        """niu  but could put in memcache under load"""
        return AppConfig.get_or_insert("config")

    @staticmethod
    def createWithInitalDefaults(onlyIfMissing=True):
        ac = AppConfig.load()
        if ac and onlyIfMissing:
            return
        else:
            ac = AppConfig()

        ac.gcm_api_key = "bcc23e065d055bcd111146bd24d53e004d93d0c0"
        ac.apns_test_mode = True
        with open("common/push/apns_sandbox.cert") as f:
            s = f.read()
            ac.apns_sandbox_cert = s
        with open("common/push/apns_sandbox.key") as f:
            s = f.read()
            ac.apns_sandbox_key = s

        ac.put()
