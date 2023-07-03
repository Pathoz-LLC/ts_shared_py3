import os
import base64
from typing import Any, Union, Dict
import logging
import datetime
from json import dumps
from google.auth import default as authDefault
from google.protobuf import timestamp_pb2
from google.cloud.tasks_v2 import (
    Task,
    CloudTasksClient,
    CloudTasksAsyncClient,
    RetryConfig,
)

#
from ..config.all import GcpSvcsCfg
from ..constants import IS_RUNNING_LOCAL, LOCAL_PUBLIC_URL
from ..enums.queued_work import QueuedWorkTyp

log = logging.getLogger("queue_dispatch")

REGION_ID: str = "us-central1"
PROJECT_ID: str = None
gcpCfg: GcpSvcsCfg = GcpSvcsCfg()
_ts_task_client: CloudTasksClient = None
# _retryConfig: RetryConfig = RetryConfig(dict(max_attempts=2))


# main export;  primary funciton
def do_background_work(
    workType: QueuedWorkTyp,
    payload: map = None,
    in_seconds: int = None,
    taskName: str = None,
):
    # uses POST
    queue = workType.queueName
    non_gae_web_host = LOCAL_PUBLIC_URL if IS_RUNNING_LOCAL else None
    handlerUri = workType.postHandlerFullUri(non_gae_web_host=non_gae_web_host)

    _create_task(queue, handlerUri, payload, in_seconds, taskName)


def do_background_work_get(
    handlerUri: str,
    queueName: str = "default",
    in_seconds: int = None,
    taskName: str = None,
):
    # uses GET
    _create_task_get(queueName, handlerUri, in_seconds, taskName)


def _getProjId() -> str:
    global PROJECT_ID
    if PROJECT_ID is None:
        # _, PROJECT_ID = authDefault()
        PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "tsapi-stage2")
    return PROJECT_ID


def _getTaskClient() -> CloudTasksClient:  # CloudTasksAsyncClient
    global _ts_task_client
    if _ts_task_client is None:
        _ts_task_client = CloudTasksClient()
        # _ts_task_client = CloudTasksClient(
        #     credentials=gcpCfg.GOOGLE_APPLICATION_CREDENTIALS
        # )
        # _ts_task_client = CloudTasksAsyncClient()
        # _ts_task_client = CloudTasksAsyncClient(
        #     credentials=gcpCfg.GOOGLE_APPLICATION_CREDENTIALS
        # )
    return _ts_task_client


def _getQueuePath(queueName: str, *, regionId: str = REGION_ID) -> str:
    ctc = _getTaskClient()
    projId: str = _getProjId()
    return ctc.queue_path(projId, regionId, queueName)


def _getPathPrefix(qPath: str) -> str:
    return qPath.rsplit("/", 2)[0]


def _createTaskPayload(
    handlerUri: str, payload: Union[Dict[str, Any], str, None], taskName: str = None
) -> dict[str, str]:
    #
    # request_type = "app_engine_http_request"
    request_type: str = (
        "http_request" if IS_RUNNING_LOCAL else "app_engine_http_request"
    )
    uri_key: str = "url" if IS_RUNNING_LOCAL else "relative_uri"

    converted_payload: str = payload  # Union[Dict[str, Any], str, None]
    if isinstance(payload, dict):
        converted_payload = dumps(payload)
    elif isinstance(payload, object):
        converted_payload = dumps(payload)

    converted_payload = (
        None
        if converted_payload is None
        else base64.b64encode(converted_payload.encode("ascii"))
    )
    d: dict[str, Any] = {
        request_type: {
            uri_key: handlerUri,
            "http_method": "POST",
            "body": converted_payload,
            "headers": {
                "Content-Type": "application/json",
            },
        }
    }

    # disable sending taskName for now because sender is not correctly formatting it per:
    # https://cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks#Task.FIELDS.name
    # if taskName is not None:
    #     d["name"] = taskName

    return d


def _create_task(
    queue: str,
    handlerUri: str,
    payload: Union[Dict[str, Any], str, None] = None,
    in_seconds: int = None,
    taskName: str = None,
):
    # https://cloud.google.com/tasks/docs/creating-appengine-tasks

    taskArgs: Dict[str, str] = _createTaskPayload(handlerUri, payload, taskName)
    if in_seconds is not None:
        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=in_seconds)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)
        taskArgs["schedule_time"] = timestamp

    # send task from here:
    parent = _getQueuePath(queue)
    createdTask: Task = _getTaskClient().create_task(parent=parent, task=taskArgs)  #
    logging.info("Created task at {0}".format(parent))
    logging.info("web url: " + taskArgs.get("url", "NA"))
    logging.info("gae uri: " + taskArgs.get("relative_uri", "NA"))
    # logging.info(createdTask)


def _create_task_get(
    queue: str,
    handlerUri: str,
    in_seconds: int = None,
    taskName: str = None,
):
    # https://cloud.google.com/tasks/docs/creating-appengine-tasks

    task: Dict[str, str] = _createTaskPayload(handlerUri, None, taskName)
    task["app_engine_http_request"]["http_method"] = "GET"
    task["app_engine_http_request"]["body"] = None
    task["app_engine_http_request"]["headers"] = None

    if in_seconds is not None:
        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=in_seconds)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)
        task["schedule_time"] = timestamp

    # send task from here:
    parent = _getQueuePath(queue)
    queueAck = _getTaskClient().create_task(parent=parent, task=task)  #
    logging.info("Created task {} --".format(queueAck.name))
    logging.info(queueAck)


def test_create_task(
    queue: str,
    handlerUri: str,
    payload: map = None,
    in_seconds: int = None,
):
    _create_task(queue, handlerUri, payload, in_seconds)


# You can change DOCUMENT_ID with USER_ID or something to identify the task
# example call:
# create_task(PROJECT_ID, QUEUE, REGION, DOCUMENT_ID)


def _create_queue_if(qName: str = "default") -> bool:
    "app-internal function creating default queue if it does not exist"
    try:
        _getTaskClient().get_queue(name=qName)
    except Exception as e:
        if "does not exist" in str(e):
            parent = _getPathPrefix(_getQueuePath(qName))
            _getTaskClient().create_queue(parent=parent, queue={"name": qName})
    return True
