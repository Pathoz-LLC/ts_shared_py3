from datetime import date, timedelta
from enum import Enum, unique
from random import randint


@unique
class StabilityProgressionStyle(Enum):
    LOW_TO_HIGH = 0
    HIGH_TO_LOW = 1
    RANDOM = 2
    VOLATILE = 3


class TestConfig(object):
    def __init__(self, days=90, sps=StabilityProgressionStyle.LOW_TO_HIGH):
        self.startDt = date.today() - timedelta(days=days)
        self.endDt = date.today()
        self.totalFeelingCount = 5
        self.totalBehCount = 5
        self.clIncreaseCount = 2
        self.clDecreaseCount = 3
        self.incidentCount = 1
        #
        self.sps = sps
        # since this obj is a data generator, it progresses day by day each time called
        self._currentDt = self.startDt
        self.mockRecsToStore = []

    @property
    def bla(self):
        return 77

    def feelingsToday(self):
        return 2

    def bumpDay(self):
        """after creating recs into xxx"""
