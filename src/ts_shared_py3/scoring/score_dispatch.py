import logging
from random import randint
from typing import Type
from datetime import datetime, timedelta

# from google.cloud.tasks_v2 import HttpMethod
#
from ..models.beh_entry import Entry as BehEntry
from ..models.input_entry_adapter import InputEntryAdapter
from ..services.taskq_dispatch import do_background_work, do_background_work_get

from ..constants import (
    IS_RUNNING_LOCAL,
    LOCAL_PUBLIC_URL_SCORING,
    GAEQ_FOR_SCORING,
    # SCORING_SERVICE_NAME,
)


class ScoreDispatchHelper(object):
    """
    stores recent user entry as InputEntryAdapter
    record and then sends a named task to the queue
    to spawn rescore
    free users get rescored at midnight
    paid users get rescored 4 mins after last data entry
    """

    @classmethod
    def _dispatchScoreTask(cls: Type, userId: str, prospectId: int, dtTmEta: datetime):
        taskName = "rescore-{0}-{1}".format(userId, prospectId)
        scoreSvcOrRelUrl = LOCAL_PUBLIC_URL_SCORING if IS_RUNNING_LOCAL else ""
        url = scoreSvcOrRelUrl + "scoring/recalc/{0}/{1}".format(userId, prospectId)
        do_background_work_get(url, GAEQ_FOR_SCORING, None, taskName)

    @classmethod
    def storeFeelingOrBehavior(
        cls: Type, userId: str, prospectId: int, beh: BehEntry, isFreeUser: bool = True
    ):
        iea = InputEntryAdapter.fromBehavior(beh)
        iea.setKeyProperties(userId, prospectId)
        iea.save()
        eta = _deriveRescoreTime(isFreeUser)
        cls._dispatchScoreTask(userId, prospectId, eta)

    @classmethod
    def storeValueAssessment(
        cls: Type,
        userId: str,
        prospectId: int,
        behCode: str,
        concernVote: int,
        freqVote: int,
        changeDt: datetime,
        isFreeUser: bool = True,
    ):
        iea = InputEntryAdapter.fromValueAssessment(
            behCode, concernVote, freqVote, changeDt
        )
        iea.setKeyProperties(userId, prospectId)
        iea.save()
        eta = _deriveRescoreTime(isFreeUser)
        cls._dispatchScoreTask(userId, prospectId, eta)

    @classmethod
    def storeCommitLevelChange(
        cls, userId, prospectId, priorPhase, mostRecentPhase, isFreeUser=True
    ):
        iea = InputEntryAdapter.fromCommitLevelChange(priorPhase, mostRecentPhase)
        iea.setKeyProperties(userId, prospectId)
        iea.save()
        eta = _deriveRescoreTime(isFreeUser)
        cls._dispatchScoreTask(userId, prospectId, eta)

    @classmethod
    def storeIncident(cls, userId, prospectId, incdt, relLength, isFreeUser=True):
        # incidents created on another server
        iea = InputEntryAdapter.fromIncident(incdt, relLength)
        iea.setKeyProperties(userId, prospectId)
        iea.save()
        eta = _deriveRescoreTime(isFreeUser)
        cls._dispatchScoreTask(userId, prospectId, eta)


def _deriveRescoreTime(isFreeUser: bool) -> datetime:
    # returns datetime for when rescore task should execute
    if isFreeUser:
        mins = randint(0, 59)
        return datetime.now().replace(hour=12, minute=mins)
    else:
        now = datetime.now()
        now += timedelta(minutes=3)
        return now


# TODO: delete below

# # try:
# #     scoreQueue = taskqueue.Queue(name=GAEQ_FOR_SCORING)
# #     scoreQueue.delete_tasks_by_name(taskName)
# # except:
# #     pass
# # Construct the fully qualified queue name.
# task_queue_name = getFullQueuePath(GAEQ_FOR_SCORING)

# # Construct the request body.
# task = {
#     "name": taskName,
#     "app_engine_http_request": {  # Specify the type of request.
#         "http_method": HttpMethod.GET,
#         "relative_uri": url,
#         # "body": encoded_payload,
#     },
# }

# try:
#     # _ = ts_task_client.create_task(parent=task_queue_name, task=task)
#     do_background_work_get(url, GAEQ_FOR_SCORING, None, taskName)
#     # _ = taskqueue.add(
#     #     queue_name=GAEQ_FOR_SCORING,
#     #     target=SCORING_SERVICE_NAME,
#     #     name=taskName,
#     #     url=url,
#     #     eta=dtTmEta,
#     #     retry_options=scoringRetryConfig,
#     # )
# # except taskqueue.TaskAlreadyExistsError as e:
# #     logging.error("Err...task {0} couldnt be deleted".format(taskName))
# # except taskqueue.DuplicateTaskNameError as e:
# #     logging.warning(
# #         "scoringQueue.DuplicateTaskNameError on {0} & {1}".format(e, taskName)
# #     )
# except Exception as e:
#     logging.error("scoringQueue.Error: %s (FIXME)" % e)
#     if False:
#         raise
