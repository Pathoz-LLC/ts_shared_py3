from typing import Any
from json import dumps
from google.auth import default as authDefault
from google.cloud.tasks_v2 import CloudTasksAsyncClient, RetryConfig

#
from ..config.all import GcpSvcsCfg

IS_DEV_SERVER = False
# from ..constants import IS_DEV_SERVER

# usage:
# from .config import ts_client, QUEUE_PATH, createTaskPayload

# google.auth.exceptions.DefaultCredentialsError: File tsapi-stage2-540f7db98f01.json was not found.
gcpCfg = GcpSvcsCfg()
ts_task_client = CloudTasksAsyncClient(
    credentials=gcpCfg.GOOGLE_APPLICATION_CREDENTIALS
)

retryConfig = RetryConfig(dict(max_attempts=2))

_, PROJECT_ID = authDefault()
REGION_ID = "REGION_ID"  # replace w/your own
QUEUE_NAME = "default"  # replace w/your own
QUEUE_PATH = ts_task_client.queue_path(PROJECT_ID, REGION_ID, QUEUE_NAME)
PATH_PREFIX = QUEUE_PATH.rsplit("/", 2)[0]


def createTaskPayload(path: str, payload: dict[str, Any]) -> dict[str, Any]:

    request_type = "http_request" if IS_DEV_SERVER else "app_engine_http_request"
    uri_key = "url" if IS_DEV_SERVER else "relative_uri"
    return {
        request_type: {
            uri_key: path,
            "body": dumps(payload).encode(),
            "headers": {
                "Content-Type": "application/json",
            },
        }
    }


def getFullQueuePath(queue_name: str) -> str:
    return ts_task_client.queue_path(PROJECT_ID, "us-central1", queue_name)


def _create_queue_if():
    "app-internal function creating default queue if it does not exist"
    try:
        ts_task_client.get_queue(name=QUEUE_NAME)
    except Exception as e:
        if "does not exist" in str(e):
            ts_task_client.create_queue(parent=PATH_PREFIX, queue={"name": QUEUE_NAME})
    return True

    _ = _create_queue_if()
