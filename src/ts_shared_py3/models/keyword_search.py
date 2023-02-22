from __future__ import annotations
import google.cloud.ndb as ndb

#
from ts_shared_py3.api_data_classes.behavior import BehaviorSearchTermMsg


class KeywordSearch(ndb.Model):
    # store each user search phrase & increment count
    searchPhrase = ndb.TextProperty(indexed=False, required=True)
    # user did not tap on results & tried a new search instead
    failed = ndb.BooleanProperty(indexed=False, default=False)
    count = ndb.IntegerProperty(indexed=False, default=0)
    useIDs = ndb.TextProperty(indexed=False, repeated=True)

    @staticmethod
    def load(key):
        return key.get()

    @staticmethod
    def loadOrCreateFromMsg(msg: BehaviorSearchTermMsg) -> KeywordSearch:
        # should remember which users reported term
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
        # rec.useIDs.append(msg.userID)
        return rec

    def save(self: KeywordSearch):
        #
        self.put()
