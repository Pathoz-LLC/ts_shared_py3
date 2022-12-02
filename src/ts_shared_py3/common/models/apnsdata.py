# import json
# import logging
# import time
# import uuid
# from google.appengine.api import memcache

# usage:
# from common.models.apnsdata import ApnsToken, ApnsSandboxToken, ApnsTag, ApnsSandboxTag

import google.cloud.ndb as ndb
from .baseNdb_model import BaseNdbModel


class ApnsToken(BaseNdbModel):
    use_id = ndb.StringProperty(indexed=True, required=True)
    apns_token = ndb.StringProperty(indexed=True, default="")
    device_type = ndb.StringProperty(indexed=False)
    enabled = ndb.BooleanProperty(indexed=True, default=True)
    registration_date = ndb.DateTimeProperty(indexed=False, auto_now_add=True)


class ApnsSandboxToken(BaseNdbModel):
    use_id = ndb.StringProperty(indexed=True, required=True)
    apns_token = ndb.StringProperty(indexed=True, default="")
    device_type = ndb.StringProperty(indexed=False)
    enabled = ndb.BooleanProperty(indexed=True, default=True)
    registration_date = ndb.DateTimeProperty(indexed=False, auto_now_add=True)


class ApnsTag(BaseNdbModel):
    token = ndb.KeyProperty(kind=ApnsToken)
    tag = ndb.StringProperty(indexed=True, required=True)


class ApnsSandboxTag(BaseNdbModel):
    token = ndb.KeyProperty(kind=ApnsSandboxToken)
    tag = ndb.StringProperty(indexed=True, required=True)
