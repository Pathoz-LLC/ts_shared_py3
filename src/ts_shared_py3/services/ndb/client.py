import os
import json
import logging
import google.cloud.ndb as ndb
from google.oauth2 import service_account

from ...config.env.cfg_defaults import GcpSvcsCfg
from ...config.env.load import EnvConfigTyp

# from ...config.env.env import EnvVarVals


def get_ndb_client() -> ndb.Client:

    gcp_config: GcpSvcsCfg = EnvConfigTyp.GCP_SVCS.config_obj
    logging.info(
        "loading NDB from:  {0}".format(gcp_config.GOOGLE_APPLICATION_CREDENTIALS)
    )
    f = open(gcp_config.GOOGLE_APPLICATION_CREDENTIALS)
    json_acct_info = json.load(f)
    credentials = service_account.Credentials.from_service_account_info(json_acct_info)

    return ndb.Client(credentials=credentials)
