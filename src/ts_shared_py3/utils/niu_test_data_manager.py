from __future__ import annotations

# import logging
# from datetime import timedelta
import google.cloud.ndb as ndb

#
# from common.models.behavior_model import PersonBehavior as BehOrFeelEntry
# from common.models.raw_day_scores_by_month import PersonMonthScoresRaw
# from common.models.tracking import Tracking
# from common.models.incident_table_only import Incident  # , IntervalRow
from common.models.valuesByBehCat import BehSummary, ProspectSummary
from common.models.entry_adapter import InputEntryAdapter, MapOccurDtToInputAdapterLst
from common.models.latest_scores import ProspectRecentScores

# code to read & structure test data from input files
from tests.helpers.trial_data_loader import (
    TestCsvFileParser,
    RecIdTypeAndNdbRecForEntryAdapter,
    TestCommitLvlChangeTup,
)
from tests.scoring.match_actual_expected import MatchActualToExpected

from ..config.test.constants_test import (
    GETTING_BETTER_FILENAME,
    VOLATILE_FILENAME,
    GETTING_WORSE_FILENAME,
)

""" THIS IS A TEST FILE    
"""


class OneDayScoreMsg(object):
    def __init__(self, pt, date, userScore=0.0, appScore=0.0, isEmpty=True):
        self.pointNum = pt
        self.date = date
        self.userScore = userScore
        self.appScore = appScore
        self.isEmptyPeriod = isEmpty

    def __repr__(self):
        # us = (self.userScore / 100 - 1) * 2
        us = self.userScore
        aps = self.appScore
        return "OneDayScoreMsg(date=date({0}, {1}, {2}), userScore={3}, appScore={4}, pointNum={5})".format(
            self.date.year,
            self.date.month,
            self.date.day,
            us,
            aps,
            self.pointNum,
        )


class TestDataManager(object):
    """
    supplies canonical test data to the scoring engine
    -- also the object to which the calculator sends row-scores as they are derived

    note that TestCsvFileParser changes the DB for UserValsByBehCat
    """

    @staticmethod
    def clearAdaptersLoadNewSaveToDisk(
        ndbClient: ndb.Client,
        userID: str,
        personID: int,
        fileName: str,
        calledFromWeb: bool = False,
    ) -> TestDataManager:
        #
        dataLoaderWithExpectedCalcs: TestDataManager = TestDataManager(
            userID, personID, fileName
        )
        # perform NDB operation;  duplicate code below
        if calledFromWeb:
            dataLoaderWithExpectedCalcs._deleteAllTestAdapterRecs()
            dataLoaderWithExpectedCalcs.convertTestNdbRecsToEntryAdaptersAndStoreOnDisk()
            # get rid of recently score vals to keep tests consistent
            priorRunData = ProspectRecentScores.loadOrCreate(userID, personID)
            priorRunData._clearAndSaveOnlyForTesting()

        else:
            with ndbClient.context():
                dataLoaderWithExpectedCalcs._deleteAllTestAdapterRecs()
                dataLoaderWithExpectedCalcs.convertTestNdbRecsToEntryAdaptersAndStoreOnDisk()
                # get rid of recently score vals to keep tests consistent
                priorRunData = ProspectRecentScores.loadOrCreate(userID, personID)
                priorRunData._clearAndSaveOnlyForTesting()

        return dataLoaderWithExpectedCalcs

    def __init__(self: TestDataManager, userID: str, personID: int, fileName: str):
        self.userID: str = userID
        self.personID: int = personID
        self.lstEntryAdapterRecs: list[InputEntryAdapter] = []

        # data from csv test file <fileName>
        self.testDataAsSourceNdbModelRecs: TestCsvFileParser = (
            TestCsvFileParser.loadTestFileAsDataSource(fileName, userID, personID)
        )

    def convertTestNdbRecsToEntryAdaptersAndStoreOnDisk(self: TestDataManager) -> None:

        """csv file parser will accumulate LISTS of
        both expected row-scores & expected day-scores
        test methods (below) should loop on those lists to confirm that
        this dataloader object received an actual score
        from the personScoreCollection for each point expected
        for both user and app scores
        """
        lstEntryAdapterRecs: list[InputEntryAdapter] = []
        ieaRec: InputEntryAdapter = None
        rtnea: RecIdTypeAndNdbRecForEntryAdapter = None
        # behavior and feelings
        for rtnea in self.testDataAsSourceNdbModelRecs.behAndFeelRecs:
            behOrFeel = rtnea.ndbRec
            ieaRec: InputEntryAdapter = InputEntryAdapter.fromBehavior(behOrFeel)
            ieaRec.recID = rtnea.recID
            lstEntryAdapterRecs.append(ieaRec)

        # commit level changes
        for rtnea in self.testDataAsSourceNdbModelRecs.commitLvlChangeRecs:
            clChangeTup: TestCommitLvlChangeTup = rtnea.ndbRec
            ieaRec: InputEntryAdapter = InputEntryAdapter.fromCommitLevelChange(
                clChangeTup.priorInvl, clChangeTup.nextInvl
            )
            ieaRec.recID = rtnea.recID
            lstEntryAdapterRecs.append(ieaRec)

        # value assesmt survey entries
        for rtnea in self.testDataAsSourceNdbModelRecs.lstBehSumRecs_ValsAssess:
            behSummary: BehSummary = rtnea.ndbRec
            # value assessment
            prospVals: ProspectSummary = behSummary.perProspect[0]
            assert (
                len(behSummary.perProspect) == 1
            ), "Err: more props freq votes than expected"
            ieaRec: InputEntryAdapter = InputEntryAdapter.fromValueAssessment(
                behCode=behSummary.behCode,
                concernVote=behSummary.concernVote,
                freqVote=prospVals.freqVote,
                changeDt=prospVals.changeDt,
            )
            ieaRec.recID = rtnea.recID
            lstEntryAdapterRecs.append(ieaRec)

        # incidents
        for rtnea in self.testDataAsSourceNdbModelRecs.incidents:
            incdt = rtnea.ndbRec
            ieaRec: InputEntryAdapter = InputEntryAdapter.fromIncident(incdt, 30)
            ieaRec.recID = rtnea.recID
            lstEntryAdapterRecs.append(ieaRec)

        # add key for all loaded InputEntryAdapter recs
        for ieaRec in lstEntryAdapterRecs:
            # put a valid key on every rec
            ieaRec.setKeyProperties(self.userID, self.personID)

        self.lstEntryAdapterRecs = lstEntryAdapterRecs
        try:
            ndb.put_multi(lstEntryAdapterRecs)
            print(
                "stored {0} InputEntryAdapter recs to ndb".format(
                    len(lstEntryAdapterRecs)
                )
            )
        except Exception as e:
            print(
                "Err in convertTestNdbRecsToEntryAdaptersAndStoreOnDisk. failed to store {0} recs;  {1}".format(
                    len(lstEntryAdapterRecs), e
                )
            )
            raise e

    def limit_rec_set_for_testing(self: TestDataManager) -> None:
        # reduce data for testing purposes
        l = []
        for iea in self.lstEntryAdapterRecs:
            behCd = iea.strArgs[0]
            if (
                iea.isValueAssessmentWithPositiveWeight
                and behCd != "cheatedOnMeWhenTempted"
            ):
                l.append(iea)
        self.lstEntryAdapterRecs = l[0:2]
        m = "Temp:  testing with {0} adapter recs".format(len(l))
        print(m)

    @property
    def dtMapOfEntryAdapterRecs(self: TestDataManager) -> MapOccurDtToInputAdapterLst:
        # returns dict{date, list[InputEntryAdapter]}
        d: MapOccurDtToInputAdapterLst = {}
        for iea in self.lstEntryAdapterRecs:
            l = d.setdefault(iea.occurDt, [])
            l.append(iea)
        print(
            "there were {0} entries accross {1} days".format(
                len(self.lstEntryAdapterRecs), len(d)
            )
        )
        return d

    @property
    def testResultsComparator(self: TestDataManager) -> MatchActualToExpected:
        return MatchActualToExpected(self.testDataAsSourceNdbModelRecs)

    # TODO
    # apply test data to prospect on the real system
    #
    def _deleteAllTestAdapterRecs(self: TestDataManager):
        # remove InputEntryAdapter (test) recs
        userPersonAncestorKey = InputEntryAdapter.makeAncestor(
            self.userID, self.personID
        )
        qry = InputEntryAdapter.query(ancestor=userPersonAncestorKey)
        # now run the query
        allRecKeys = qry.fetch(4000, keys_only=True)
        lk = ndb.delete_multi(allRecKeys)
        print(
            "\nInfo: deleted {0} InputEntryAdapter recs;  {1} stored days; forcing complete recalc of stored entries".format(
                len(lk), "n/a"
            )
        )
