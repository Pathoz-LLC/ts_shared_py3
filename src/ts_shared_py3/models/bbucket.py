import google.cloud.ndb as ndb
from .baseNdb_model import BaseNdbModel


class BitBucket(BaseNdbModel):
    """
    convenience table to keep data from anywhere
    string key's preferred
    you must set & track your own keys
    """

    json = ndb.JsonProperty()
    bucket = ndb.BlobProperty()

    addDateTime = ndb.DateTimeProperty(auto_now_add=True, indexed=True)

    @staticmethod
    def storeBlobAtKey(keyStr, data):
        # FIXME:  DataStore entity max size is 1024 (1mb)

        # assert(len(data.encode('utf-8')) < 1024, "blob (receipt) data too big for table")
        # UnicodeDecodeError: 'ascii' codec can't decode byte 0x82 in position 1: ordinal not in range(128)

        # print("storing data:")
        # print(data)

        rec = BitBucket(key=ndb.Key(BitBucket, keyStr))
        rec.bucket = data
        return rec.put()

    @staticmethod
    def getBlobAtKey(keyStr):
        key = ndb.Key(BitBucket, keyStr)
        rec = key.get()
        if rec:
            return rec.bucket

    @staticmethod
    def storeJsonAtKey(keyStr, json):
        rec = BitBucket(key=ndb.Key(BitBucket, keyStr))
        rec.json = json
        return rec.put()

    @staticmethod
    def getJsonAtKey(keyStr):
        key = ndb.Key(BitBucket, keyStr)
        rec = key.get()
        if rec:
            return rec.json
