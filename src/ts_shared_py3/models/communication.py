from datetime import date, timedelta, datetime
from typing import Union, TypeVar

import google.cloud.ndb as ndb
from .baseNdb_model import BaseNdbModel

# from common.messages.communication import CommunicationEventMsg, CommunicationRawTranscriptMsg

import constants


class Window:
    """
    strictly for creating keys for stored models; not stored to DB
    """

    @staticmethod
    def getWeekStr(startDtTm):
        # returns "17:12"  (12th week in year 2017)
        yrWkNumWkDay = startDtTm.isocalendar()
        yr = str(yrWkNumWkDay[0])[2:4]  # last 2 digits of year
        wk = yrWkNumWkDay[1]  # returns int in 1-52
        return "{0}:{1}".format(yr, wk)

    @staticmethod
    def getKey(userKey, persId, weekInt):
        # make composite data key based on the week of the data
        userPersKey = ndb.Key("Person", persId, parent=userKey)
        weekIdStr = Window.getWeekStr()
        return ndb.Key(CommunicationStats, weekIdStr, parent=userPersKey)

    @staticmethod
    def nearestPeriodStartDate(startDttm):
        """
        rounds start back to beginning of some week window
        so when we recalc stats; we have a complete set of recs

        Returns: date same or earlier than startDttm

        """
        if startDttm is None:
            startDttm = datetime.now() - timedelta(days=21)

        yrWkNumWkDay = startDttm.isocalendar()
        daysBackToFirstOfWeek = yrWkNumWkDay[2] - 1
        startDttm = startDttm - timedelta(days=daysBackToFirstOfWeek)
        return startDttm


class CommunicationStats(BaseNdbModel):
    """stats by period (cur week) for chats between two ppl

    key is composite:  userId, personId, 2DigYear:weekInt (0-52)
    because of that key, any updates will auto-overwrite prior data
    """

    myScore = ndb.IntegerProperty(indexed=False)  # theirScore = 100 - myScore
    personId = ndb.IntegerProperty(indexed=True)
    transcriptsAvailable = ndb.BooleanProperty(indexed=False, default=True)

    startDtTm = ndb.DateTimeProperty(indexed=True)
    endDtTm = ndb.DateTimeProperty(indexed=False)
    # count of total msgs I've sent in this period
    myMsgCount = ndb.IntegerProperty(indexed=False, default=0)
    theirMsgCount = ndb.IntegerProperty(indexed=False, default=0)
    # Wpm == avg words per msg
    myAvgWpmCount = ndb.IntegerProperty(indexed=False, default=0)
    theirAvgWpmCount = ndb.IntegerProperty(indexed=False, default=0)
    # LTR length time (or latency) to respond
    myAvgLtr = ndb.IntegerProperty(indexed=False, default=0)
    theirAvgLtr = ndb.IntegerProperty(indexed=False, default=0)
    # initiate communication
    myInitiateCount = ndb.IntegerProperty(indexed=False, default=0)
    theirInitiateCount = ndb.IntegerProperty(indexed=False, default=0)
    # ended communication
    myEndedCount = ndb.IntegerProperty(indexed=False, default=0)
    theirEndedCount = ndb.IntegerProperty(indexed=False, default=0)
    # drinkHrsStart communication
    myDrinkHrsStartCount = ndb.IntegerProperty(indexed=False, default=0)
    theirDrinkHrsStartCount = ndb.IntegerProperty(indexed=False, default=0)

    # def toMsg(self):
    #     # CommStatsByPeriodMsg is designed to cary MANY of these CommunicationStats recs
    #     # not just one
    #
    #     # msg =
    #     # msg.windows.append( self.toWindow() )
    #     # return msg
    #     pass

    # def appendMsg(self, msg):
    #     msg.windows.append( self.toWindow() )

    def toCommStatsMsg(self):
        from api_data_classes.communication import CommStatsMsg

        win = CommStatsMsg()
        win.myOverallScore = self.myScore
        win.theirOverallScore = 100 - self.myScore

        win.startDtTm = self.startDtTm
        win.endDtTm = self.endDtTm
        win.myMsgCount = self.myMsgCount
        win.theirMsgCount = self.theirMsgCount
        win.myAvgWpmCount = self.myAvgWpmCount
        win.theirAvgWpmCount = self.theirAvgWpmCount
        win.myAvgLtr = self.myAvgLtr
        win.theirAvgLtr = self.theirAvgLtr
        win.myInitiateCount = self.myInitiateCount
        win.theirInitiateCount = self.theirInitiateCount
        win.myEndedCount = self.myEndedCount
        win.theirEndedCount = self.theirEndedCount
        win.myDrinkHrsStartCount = self.myDrinkHrsStartCount
        win.theirDrinkHrsStartCount = self.theirDrinkHrsStartCount
        win.transcriptsAvailable = self.transcriptsAvailable
        return win

    def _pre_put_hook(self):
        self.calcScoreFromThisPeriod()

    def calcScoreFromThisPeriod(self):
        """
        called by pre-put hook
        also works on a rollup of multiple windows

        FIXME: implement calcs sent by Erica
        """
        self.myScore = 50

    @staticmethod
    def ceRecArrayTo1CommStat(weekIdStr, arrayCeRecs4Week):
        """
        Args:
            weekIdStr:
            arrayCeRecs4Week:

        Returns: a CommunicationStats rec
        """
        SECS_DEFINING_NEW_CONVO = 8 * 60 * 60  # 8 hours

        rowCount = len(arrayCeRecs4Week)
        if rowCount < 1:
            return CommunicationStats()

        myMsgCount = 0
        myTotalWordCount = 0
        theirTotalWordCount = 0
        myTotalTimeToRespond = 0
        theirTotalTimeToRespond = 0
        myInitiateCount = 0
        theirInitiateCount = 0
        myEndedCount = 0
        theirEndedCount = 0
        senderReversalCount = 0
        # FIXME: drink hrs not yet handled
        myDrinkHrsStartCount = 0
        theirDrinkHrsStartCount = 0

        # need sorted to measure time-lag between msgs
        arrayCeRecs4Week.sort(key=lambda ce: ce.sentDttm)  # from oldest to recent
        priorCeRec = arrayCeRecs4Week[0]  # first rec to compare to next
        transcrAvail = len(priorCeRec.text) > 3  # what if 1st msg is just 1 emoji?

        # arrayCeRecs4Week should already be sorted by sentDttm
        minDttm = priorCeRec.sentDttm
        maxDttm = arrayCeRecs4Week[len(arrayCeRecs4Week) - 1].sentDttm

        # priorMsgFromMe = priorCeRec.fromUser
        if priorCeRec.fromUser:
            myMsgCount = 1
            myTotalWordCount = priorCeRec.wordCount
        else:
            theirTotalWordCount = priorCeRec.wordCount

        for i, ceRec in enumerate(arrayCeRecs4Week):
            myMsgCount += 1 if ceRec.fromUser else 0

            # justSwitchedUsers is true if we have just switched users
            justSwitchedUsers = priorCeRec.fromUser != ceRec.fromUser
            timeLagBetweenMessages = (ceRec.sentDttm - priorCeRec.sentDttm).seconds

            if ceRec.fromUser:
                myTotalWordCount += ceRec.wordCount

                if justSwitchedUsers:
                    senderReversalCount += 1
                    myTotalTimeToRespond += timeLagBetweenMessages
                    if timeLagBetweenMessages >= SECS_DEFINING_NEW_CONVO:
                        myInitiateCount += 1
                        theirEndedCount += 1
            else:
                theirTotalWordCount += ceRec.wordCount

                if justSwitchedUsers:
                    senderReversalCount += 1
                    theirTotalTimeToRespond += timeLagBetweenMessages
                    if timeLagBetweenMessages >= SECS_DEFINING_NEW_CONVO:
                        theirInitiateCount += 1
                        myEndedCount += 1

            priorCeRec = ceRec
            # priorMsgFromMe = priorCeRec.fromUser
            # continue the loop

        newCsRec = CommunicationStats()
        newCsRec.transcriptsAvailable = transcrAvail
        newCsRec.startDtTm = minDttm
        newCsRec.endDtTm = maxDttm
        newCsRec.myMsgCount = myMsgCount
        newCsRec.theirMsgCount = rowCount - myMsgCount

        newCsRec.myAvgWpmCount = int(myTotalWordCount / myMsgCount)
        newCsRec.theirAvgWpmCount = int(theirTotalWordCount / newCsRec.theirMsgCount)

        newCsRec.myAvgLtr = int(myTotalTimeToRespond / myMsgCount)
        newCsRec.theirAvgLtr = int(theirTotalTimeToRespond / myMsgCount)

        newCsRec.myInitiateCount = myInitiateCount
        newCsRec.theirInitiateCount = theirInitiateCount

        newCsRec.myEndedCount = myEndedCount
        newCsRec.theirEndedCount = theirEndedCount

        newCsRec.myDrinkHrsStartCount = myDrinkHrsStartCount
        newCsRec.theirDrinkHrsStartCount = theirDrinkHrsStartCount

        return newCsRec

    @staticmethod
    def calcAndStorePeriodStats(
        userKey, personId, bucketedDictOfCommunicationEventRecs
    ):
        """
        loop thru each set of recs in a bucket & write one CommunicationStats rec
        for each bucket (currently a week num as key)
        since we have hierarchical key, must add all recs at once (or 1 second)
        """
        listCsRecs = []
        for (
            weekIdStr,
            arrayCeRecs4Week,
        ) in bucketedDictOfCommunicationEventRecs.iteritems():
            # callCalcCode should return a new CommunicationStats rec
            newCommunicationStatsForPeriod = CommunicationStats.ceRecArrayTo1CommStat(
                weekIdStr, arrayCeRecs4Week
            )
            newCommunicationStatsForPeriod.personId = personId
            # unique key will overwrite previous stats if they exist
            newCommunicationStatsForPeriod.key = Window.getKey(
                userKey, personId, weekIdStr
            )
            listCsRecs.append(newCommunicationStatsForPeriod)
            # newCommunicationStatsForPeriod.put()  # store to ndb

        ndb.put_multi(listCsRecs)

    # begin methods for returning 2 levels of aggregate stats
    # 1 stats rec per week
    # or 1 single rollup rec

    @staticmethod
    def getStatsForPeriod(userKey, personId, daysBack=30):
        """

        Args:
            userKey:
            personId:
            daysBack:

        Returns: [CommStatsListMsg]

        """
        from api_data_classes.communication import CommStatsListMsg

        userPersKey = ndb.Key("Person", personId, parent=userKey)
        q = CommunicationStats.query(ancestor=userPersKey)
        queryStartDttm = datetime.now() - timedelta(days=daysBack)
        q.filter("sentDttm >=", queryStartDttm)
        # now run query
        statsAllWindows = q.fetch()

        cslm = CommStatsListMsg()
        cslm.periodStats = [cs.toCommStatsMsg() for cs in statsAllWindows]
        return cslm

    @staticmethod
    def rollupListOfStatWindows(userKey, personId, daysBack=30):
        """
        consolidate all weekly CommunicationStats score summary windows
        into one set of scores for return to the client
        Args:
            userKey:
            personId:
            daysBack:

        Returns: CommStatsListMsg  (rollup of [CommStatsListMsg] from getStatsForPeriod)

        """
        commStatsListMsg = CommunicationStats.getStatsForPeriod(
            userKey, personId, daysBack
        )
        listOfCsRecs = commStatsListMsg.periodStats

        # FIXME:  need to finish below
        newCsRec = CommunicationStats()
        if len(listOfCsRecs) < 1:
            return newCsRec

        firstRec = listOfCsRecs[0]
        newCsRec.personId = firstRec.personId
        newCsRec.transcriptsAvailable = firstRec.transcriptsAvailable
        newCsRec.week = firstRec.week

        ROW_COUNT = len(listOfCsRecs)
        newCsRec.myMsgCount = sum([r.myMsgCount for r in listOfCsRecs]) / ROW_COUNT
        newCsRec.theirMsgCount = (
            sum([r.theirMsgCount for r in listOfCsRecs]) / ROW_COUNT
        )
        newCsRec.myAvgWpmCount = (
            sum([r.myAvgWpmCount for r in listOfCsRecs]) / ROW_COUNT
        )
        newCsRec.theirAvgWpmCount = (
            sum([r.theirAvgWpmCount for r in listOfCsRecs]) / ROW_COUNT
        )

        newCsRec.myAvgLtr = sum([r.myAvgLtr for r in listOfCsRecs]) / ROW_COUNT
        newCsRec.theirAvgLtr = sum([r.theirAvgLtr for r in listOfCsRecs]) / ROW_COUNT

        newCsRec.myInitiateCount = (
            sum([r.myInitiateCount for r in listOfCsRecs]) / ROW_COUNT
        )
        newCsRec.theirInitiateCount = (
            sum([r.theirInitiateCount for r in listOfCsRecs]) / ROW_COUNT
        )
        newCsRec.myEndedCount = sum([r.myEndedCount for r in listOfCsRecs]) / ROW_COUNT
        newCsRec.theirEndedCount = (
            sum([r.theirEndedCount for r in listOfCsRecs]) / ROW_COUNT
        )

        newCsRec.myDrinkHrsStartCount = (
            sum([r.myDrinkHrsStartCount for r in listOfCsRecs]) / ROW_COUNT
        )
        newCsRec.theirDrinkHrsStartCount = (
            sum([r.theirDrinkHrsStartCount for r in listOfCsRecs]) / ROW_COUNT
        )

        newCsRec.startDtTm = min([r.startDtTm for r in listOfCsRecs])
        newCsRec.endDtTm = max([r.endDtTm for r in listOfCsRecs])
        return newCsRec

    # @staticmethod
    # def fromMsg(userKey, msg, persId, transcriptsAvailable):
    #     startDtTm = msg.startDtTm
    #     cs = CommunicationStats(key=Window.getKey(userKey,persId,0), personId=persId)
    #     cs.transcriptsAvailable = transcriptsAvailable
    #     cs.week = Window.getWeek(startDtTm)
    #     cs.startDtTm = startDtTm
    #     cs.endDtTm = msg.endDtTm
    #     cs.myMsgCount = msg.myMsgCount
    #     cs.theirMsgCount = msg.theirMsgCount
    #     cs.myAvgWpmCount = msg.myAvgWpmCount
    #     cs.theirAvgWpmCount = msg.theirAvgWpmCount
    #     cs.myAvgLtr = msg.myAvgLtr
    #     cs.theirAvgLtr = msg.theirAvgLtr
    #     cs.myInitiateCount = msg.myInitiateCount
    #     cs.theirInitiateCount = msg.theirInitiateCount
    #     cs.myEndedCount = msg.myEndedCount
    #     cs.theirEndedCount = msg.theirEndedCount
    #     cs.myDrinkHrsStartCount = msg.myDrinkHrsStartCount
    #     cs.theirDrinkHrsStartCount = msg.theirDrinkHrsStartCount
    #     # FIXME: rect not saved yet?
    #     return cs


class CommunicationEvent(BaseNdbModel):
    """
    raw data from chat logs stored in datastore
    need to be rolled up into totals (with score) on a week over week basis
    """

    fromUser = ndb.BooleanProperty(indexed=False, default=False)
    sentDttm = ndb.DateTimeProperty(indexed=True)
    wordCount = ndb.IntegerProperty(indexed=False, default=0)
    text = ndb.StringProperty(indexed=False)  # , default=''

    @staticmethod
    def fromMsg(msg, parentKey):
        return CommunicationEvent(
            parent=parentKey,
            fromUser=msg.fromUser,
            sentDttm=msg.sentDttm,
            wordCount=msg.wordCount,
            text=msg.text,
        )

    @staticmethod
    def storeLatestRows(user, msg):
        # since they have ancestor, use only 1 write per second
        # aka use put_multi to write in bulk
        userPersKey = ndb.Key("Person", msg.persId, parent=user.key)
        allComEv = [CommunicationEvent.fromMsg(m, userPersKey) for m in msg.messages]
        ndb.put_multi(allComEv)

    @staticmethod
    def rollupToPeriodCount(userPersKey, startOnDtTm):
        """load all recs & sum stats
        called by task queue to work in background
        calls Dolphs stat calc code (CommunicationStats.calcPeriodStats) above

        need to start query at beginning of a week (0-52; not Sun/Mon)
        """
        startOnDtTm = Window.nearestPeriodStartDate(startOnDtTm)

        query = CommunicationEvent.all().ancestor(userPersKey)
        query = query.filter("sentDttm >=", startOnDtTm)
        # no point sorting because bucket dicts will destroy order
        allNewRecs = query.fetch()
        weekBuckets = CommunicationEvent.splitIntoPeriodBuckets(allNewRecs)

        personId = userPersKey.parent().id()
        userKey = userPersKey.parent().parent()
        # call Dolphs code to write weekly summary stat recs
        CommunicationStats.calcAndStorePeriodStats(userKey, personId, weekBuckets)

        # no return
        # job queue func that called this method will return 200 success

    @staticmethod
    def splitIntoPeriodBuckets(allNewRecs):
        """allNewRecs is within date range recently saved
        for simplicity we assume full range of allNewRecs is less than 1 year
        so we can use 1-52 as indexes to build our period buckets
        week index is key in dict to group array of proximate recs
        """
        buckets = dict()
        for r in allNewRecs:
            weekIdStr = Window.getWeekStr(r.sentDttm)
            thisWeek = buckets.setdefault(weekIdStr, [])
            thisWeek.append(r)

        return buckets


# class CommunicationHistoryHeader(Model):
#     ''' CommunicationHistoryHeader of chat communication
#
#         not stored... just the parent
#     '''


class CommunicationPrefs(BaseNdbModel):
    """user prefs for how the communication logic should work

    not currently used
    """

    userId = ndb.IntegerProperty(indexed=True)
    # personId = ndb.IntegerProperty(indexed=True )
    # dataWindowSizeDays = ndb.IntegerProperty(indexed=False, default=7)
    allowTextAnalyss = ndb.BooleanProperty(indexed=False, default=False)
    makeTextAnnon = ndb.BooleanProperty(indexed=False, default=False)

    pathToMsgDb = ndb.StringProperty(indexed=False)
    dataHarvestSchedule = ndb.StringProperty(indexed=False)
    modifyDtTm = ndb.DateTimeProperty(indexed=False)
    lastSubmitDataDtTm = ndb.DateTimeProperty(indexed=False)

    @staticmethod
    def fromMsg(user, msg):
        cp = CommunicationPrefs(userId=user.id_)
        cp.allowTextAnalyss = msg.allowTextAnalyss

        return cp
