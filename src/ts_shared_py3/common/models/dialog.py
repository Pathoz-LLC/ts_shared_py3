import google.cloud.ndb as ndb
from .baseNdb_model import BaseNdbModel


class DialogCache(BaseNdbModel):
    # keep data from dialog.questions.RelHistory obj on disk in case memcache failes
    # key like:  "use_id:per_id"
    relHistAsJson = ndb.JsonProperty()
    # a periodic job will delete records older than 20 days
    addDateTime = ndb.DateTimeProperty(auto_now_add=True, indexed=True)
