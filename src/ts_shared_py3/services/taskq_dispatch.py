import os
import base64
from typing import Any, Union, Dict
import logging
import datetime
from json import dumps as json_dumps
from google.auth import default as authDefault
from google.protobuf import timestamp_pb2
import google.cloud.tasks_v2 as tasks_v2
from google.cloud.tasks_v2 import (
    Task,
    CloudTasksClient,
    CreateTaskRequest,
    CloudTasksAsyncClient,
    RetryConfig,
)

#
from ..config.all import EnvVarVals, GcpSvcsCfg
from ..constants import IS_RUNNING_LOCAL, LOCAL_PUBLIC_URL_DEFAULT
from ..enums.queued_work import QueuedWorkTyp

log = logging.getLogger("queue_dispatch")


# gcpCfg: GcpSvcsCfg = GcpSvcsCfg()
_ts_task_client: CloudTasksClient = None
# _retryConfig: RetryConfig = RetryConfig(dict(max_attempts=2))


# main export;  primary funciton
def do_background_work(
    workType: QueuedWorkTyp,
    payload: str = None,
    in_seconds: int = None,
    taskName: str = None,
):
    # uses POST
    queue = workType.queueName
    non_gae_web_host = LOCAL_PUBLIC_URL_DEFAULT if IS_RUNNING_LOCAL else None
    handlerUri = workType.postHandlerFullUri(non_gae_web_host=non_gae_web_host)

    _create_task_post(queue, handlerUri, payload, in_seconds, taskName)


def do_background_work_get(
    handlerUri: str,
    queueName: str = "default",
    in_seconds: int = None,
    taskName: str = None,
):
    # uses GET
    _create_task_get(queueName, handlerUri, in_seconds, taskName)


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


def _getQueuePath(queueName: str) -> str:
    ctc = _getTaskClient()
    ev = EnvVarVals()  # regionId: str = "us-central1"
    return ctc.queue_path(ev.PROJ_ID, ev.REGION_ID, queueName)


def _getPathPrefix(qPath: str) -> str:
    # used only for creating new queues
    # method conflicts with queue.yaml approach for creating queues
    return qPath.rsplit("/", 2)[0]


def _createTaskPayload(
    handlerUri: str, payload: str, taskName: str = None
) -> tasks_v2.AppEngineHttpRequest:  # dict[str, str]:
    #
    # print("task payload type: {0}".format(type(payload)))
    # assert isinstance(payload, str), "payload must be a string"
    # request_type: str = (
    #     "http_request" if IS_RUNNING_LOCAL else "app_engine_http_request"
    # )
    uri_key: str = "url" if IS_RUNNING_LOCAL else "relative_uri"
    assert (
        isinstance(payload, str) or payload is None
    ), "payload must be a string or none"
    encoded_payload: str = "_empty".encode() if payload is None else payload.encode()
    d: dict[str, Any] = {
        uri_key: handlerUri,
        "http_method": "POST",
        "body": encoded_payload,
        "headers": {
            "Content-Type": "application/json",
        },
    }

    # disable sending taskName for now because sender is not correctly formatting it per:
    # https://cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks#Task.FIELDS.name
    # if taskName is not None:
    #     d["name"] = taskName

    if IS_RUNNING_LOCAL:
        # hit local web server
        return tasks_v2.HttpRequest(d)
    else:
        # hit GAE
        return tasks_v2.AppEngineHttpRequest(d)


def _create_task_post(
    queue: str,
    handlerUri: str,
    payload: Union[str, dict, None] = "",
    in_seconds: int = None,
    taskName: str = None,
):
    # https://cloud.google.com/tasks/docs/creating-appengine-tasks
    if isinstance(payload, dict):
        payload = json_dumps(payload)

    requestObj = _createTaskPayload(handlerUri, payload, taskName)  # : Dict[str, str]
    if in_seconds is not None:
        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=in_seconds)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)
        # requestObj is no longer a dict/map, but a protobuf object; below won't work
        # requestObj["schedule_time"] = timestamp

    # send task from here:
    parent: str = _getQueuePath(queue)
    t: Task = None
    if IS_RUNNING_LOCAL:
        t = tasks_v2.Task(http_request=requestObj)
    else:
        t = tasks_v2.Task(app_engine_http_request=requestObj)

    taskRequest = CreateTaskRequest(
        parent=parent,
        task=t,
    )

    createdTask: Task = _getTaskClient().create_task(request=taskRequest)
    # createdTask: Task = _getTaskClient().create_task(parent=parent, task=taskArgs)  #
    logging.info("Created task at {0}--{1}".format(parent, createdTask))
    # logging.info("web url: " + requestObj)
    # logging.info("gae uri: " + requestObj)
    # logging.info(createdTask)


def _create_task_get(
    queue: str,
    handlerUri: str,
    in_seconds: int = None,
    taskName: str = None,
):
    # https://cloud.google.com/tasks/docs/creating-appengine-tasks

    taskRequest: Union[
        tasks_v2.AppEngineHttpRequest, tasks_v2.HttpRequest
    ] = _createTaskPayload(handlerUri, "", taskName)
    taskRequest.http_method = "GET"
    taskRequest.body = None
    taskRequest.headers = None
    # task["app_engine_http_request"]["http_method"] = "GET"
    # task["app_engine_http_request"]["body"] = None
    # task["app_engine_http_request"]["headers"] = None

    if in_seconds is not None:
        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=in_seconds)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)
        # TODO:  fixme
        # task.schedule_time = timestamp

    # send task from here:
    parent = _getQueuePath(queue)
    t: Task = None
    if IS_RUNNING_LOCAL:
        t = tasks_v2.Task(http_request=taskRequest)
    else:
        t = tasks_v2.Task(app_engine_http_request=taskRequest)

    taskRequest = CreateTaskRequest(
        parent=parent,
        task=t,
    )
    queueAck = _getTaskClient().create_task(request=taskRequest)  #
    logging.info("Created task {} --".format(queueAck.name))
    logging.info(queueAck)


def test_create_task(
    queue: str,
    handlerUri: str,
    payload: map = None,
    in_seconds: int = None,
):
    _create_task_post(queue, handlerUri, payload, in_seconds)


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
