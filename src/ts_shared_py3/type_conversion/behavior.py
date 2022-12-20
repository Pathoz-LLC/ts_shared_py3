# from datetime import datetime
import google.cloud.ndb as ndb

#
from ..models.beh_entry import Entry
from ..utils.date_conv import dateTime_from_epoch
from ts_shared_py3.api_data_classes.behavior import BehaviorRowMsg


class BehaviorIO(object):
    """ """

    @staticmethod
    def castMsgToEntry(msg: BehaviorRowMsg) -> Entry:
        # msg.feelingStrength arrives 1 <= fs <= 3
        # should make it abs() ??
        assert (
            1 <= msg.feelingStrength <= 3
        ), "err: feel val {0} is out of range 1-3".format(msg.feelingStrength)
        behEntry = Entry(
            behaviorCode=msg.behaviorCode, feelingStrength=msg.feelingStrength
        )
        behEntry.coords = ndb.GeoPt(msg.lat, msg.lon)
        behEntry.shareDetails = msg.shareDetails
        behEntry.comments = msg.comments
        behEntry.positive = msg.positive
        behEntry.occurDateTime = msg.occurDateTime
        # below added 11/5/19 by dg
        behEntry.categoryCode = msg.categoryCode
        behEntry.shareDetails = msg.shareDetails
        return behEntry
