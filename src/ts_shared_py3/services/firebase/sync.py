# from common.utils.singleton import Singleton
# from common.firebase.community import CommunityFeedEvent, CommUserInfo
from .readWrite import firebase_post, firebase_put

# used in task service to respond to async work
class CommNewsClient(object):
    # __metaclass__ = Singleton
    @staticmethod
    def pushUserActivity(commFeedEvent):
        # send a new row to firebase
        # print("partitionPath: {0}".format(commFeedEvent.partitionPath))
        firebase_post(commFeedEvent.partitionPath, commFeedEvent.toDict)


# used in task service to respond to async work
class DailyStatsClient(object):
    @staticmethod
    def putDailyStats(path, stats):
        if path is None or stats is None:
            print("NONE STATS")
            return
        elif len(path) < 0 or len(stats) < 0:
            print("EMPTY STATS")
            return

        # print("putDailyStats %s %s" % (path, stats))

        # send a new row to firebase
        firebase_put(path, stats)
