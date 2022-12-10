# from .baseNdb_model import BaseNdbModel
import google.cloud.ndb as ndb


class KeywordSearch(ndb.Model):
    # store each user search phrase & increment count
    searchPhrase = ndb.StringProperty(indexed=False, required=True)
    # user did not tap on results & tried a new search instead
    failed = ndb.BooleanProperty(indexed=False, default=False)
    count = ndb.IntegerProperty(indexed=False, default=0)
    useIDs = ndb.StringProperty(indexed=False, repeated=True)

    @staticmethod
    def load(key):
        return key.get()

    @staticmethod
    def loadOrCreateFromMsg(msg):
        key = ndb.Key(KeywordSearch, msg.searchPhrase)
        rec = KeywordSearch.load(key)
        if rec == None:
            rec = KeywordSearch(
                key=key,
                searchPhrase=msg.searchPhrase,
                failed=msg.failed,
                count=0,
                useIDs=[],
            )

        rec.count += 1
        rec.useIDs.append(msg.userID)
        return rec

    def save(self):
        #
        self.key.put()
