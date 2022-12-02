# import json
# import logging
# import time
# import uuid
# from google.appengine.api import memcache
import google.cloud.ndb as ndb

# Usage:
# from common.models.gcmdata import GcmToken, GcmTag


class GcmToken(ndb.Model):
    use_id = ndb.StringProperty(indexed=True, required=True)
    gcm_token = ndb.StringProperty(indexed=True, default="")
    device_type = ndb.StringProperty(indexed=False)
    enabled = ndb.BooleanProperty(indexed=True, default=True)
    registration_date = ndb.DateTimeProperty(indexed=False, auto_now_add=True)


class GcmTag(ndb.Model):
    token = ndb.KeyProperty(kind=GcmToken)
    tag = ndb.StringProperty(indexed=True, required=True)
