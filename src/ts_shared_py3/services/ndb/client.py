import os
import json
import logging
import google.cloud.ndb as ndb
from google.oauth2 import service_account

from ...config.all import GcpSvcsCfg

# from ...config.env.env import EnvVarVals

# is this safe or will it expire?
_ndb_client: ndb.Client = None


def get_ndb_client() -> ndb.Client:
    global _ndb_client
    if _ndb_client is not None:
        return _ndb_client

    gcp_config = GcpSvcsCfg()
    logging.info(
        "loading NDB from:  {0}".format(gcp_config.GOOGLE_APPLICATION_CREDENTIALS)
    )
    with open(gcp_config.GOOGLE_APPLICATION_CREDENTIALS) as f:
        json_acct_info = json.load(f)
        credentials = service_account.Credentials.from_service_account_info(
            json_acct_info
        )
        _ndb_client = ndb.Client(credentials=credentials)
    return _ndb_client
