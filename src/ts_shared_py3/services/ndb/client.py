import os
import logging
import google.cloud.ndb as ndb

from ...config.env.load import EnvConfigTyp
from ...config.env.env import EnvVarVals


def get_ndb_client() -> ndb.Client:
    # cred_path = EnvVarVals.
    # os.environ['API_USER'] = ""

    gcp_config = EnvConfigTyp.GCP_FB.config_obj
    logging.info(
        "loading NDB from:  {0}".format(gcp_config.GOOGLE_APPLICATION_CREDENTIALS)
    )
    return ndb.Client(
        credentials=gcp_config.GOOGLE_APPLICATION_CREDENTIALS
    )  # (credentials='')
