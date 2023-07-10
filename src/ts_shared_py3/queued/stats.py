import logging, json
from typing import Dict, Any

#
# from constants import GAEQ_FOR_DEFAULT, TASK_QUEUE_SERVICE_NAME, GAEQ_FOR_DEFAULT
from enums.queued_work import QueuedWorkTyp
from services.taskq_dispatch import (
    do_background_work,
    do_background_work_get,
)


# statsRetryConfig = ts_client.TaskRetryOptions(task_retry_limit=2)


class StatsTasks:
    """pass args for background jobs to the tasks service"""

    @staticmethod
    def updateDailyStatsTask(stats: Dict[str, Any]):
        # put arguements into json format for queue.

        do_background_work(QueuedWorkTyp.STATS_DAILY, json.dumps(stats))

        # try:
        #     _ = ts_task_client.create_task(
        #         queue_name=GAEQ_FOR_DEFAULT,
        #         target=TASK_QUEUE_SERVICE_NAME,
        #         url="/stats/daily",
        #         params={"path": json.dumps(path), "stats": json.dumps(stats)},
        #         # retry_options=statsRetryConfig,
        #     )
        # # except taskqueue.DuplicateTaskNameError as e:
        # #     logging.warning("updateDailyStatsTask.DuplicateTaskNameError for %s" % e)
        # except Exception as e:
        #     logging.error("Err: {0} {1}".format("updateDailyStatsTask", e))
        #     raise
        #     # assert False, "catch me"

    @staticmethod
    def postForgeDailyStatsTask(forgeStatsMsg):
        # put arguements into json format for queue.

        args = {
            "runTimeSecs": forgeStatsMsg.runTimeSecs,
            "votesPerMinute": forgeStatsMsg.votesPerMinute,
        }

        do_background_work(QueuedWorkTyp.STATS_DAILYFORGE, json.dumps(args))

        # data = json.dumps(args)

        # # print("forging stats with params %s" % data)

        # try:
        #     _ = ts_task_client.create_task(
        #         queue_name=GAEQ_FOR_DEFAULT,
        #         target=TASK_QUEUE_SERVICE_NAME,
        #         url="/stats/daily/forge",
        #         params={"data": data},
        #         retry_options=statsRetryConfig,
        #     )
        # except taskqueue.DuplicateTaskNameError as e:
        #     logging.warning("forgeDailyStatsTask.DuplicateTaskNameError for %s" % e)
        # except Exception as e:
        #     logging.error("Err: {0} {1}".format("forgeDailyStatsTask", e))
        #     raise
        #     # assert False, "catch me"

    # @staticmethod
    # def pushCommitStatsTask(path, stats):
    #     # put arguements into json format for queue.
    #
    #     try:
    #         _ = taskqueue.add(queue_name=GAEQ_FOR_DEFAULT, target=TASK_QUEUE_SERVICE_NAME, url='/stats/commitLevel', params={"path": json.dumps(path), "stats": json.dumps(stats)}, retry_options=statsRetryConfig)
    #     except taskqueue.DuplicateTaskNameError as e:
    #         logging.warning("updateDailyStatsTask.DuplicateTaskNameError for %s" % e)
    #     except Exception as e:
    #         logging.error("Err: {0} {1}".format("updateDailyStatsTask", e))
    #         raise
