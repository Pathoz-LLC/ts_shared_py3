from __future__ import annotations
import os
import types
from pathlib import Path
from enum import IntEnum, unique, auto

from ..utils.singleton import Singleton

"""
    reads ENV-vars and also creates OS-path for various
    config & security files

    this is a public repo so no secrets should be stored here
"""

_ROOT_PATH_PREFIX: str = None


@unique
class ThirdPtSvcType(IntEnum):
    """responsible for any custom folder names related to 3rd pty service creds"""

    FIR_USER = auto()
    FIR_ADMIN = auto()
    GCP_APIS = auto()
    EMAIL = auto()

    @property
    def mid_file_path(self: ThirdPtSvcType) -> str:
        return ""


@unique
class CurrentEnvEnum(IntEnum):
    """indicates current runtime environment"""

    LOCAL = auto()
    DEV = auto()
    STAGE = auto()
    PROD = auto()


class OsPathInfo(metaclass=Singleton):
    """used to find path to security & credential files for 3rd pty svcs"""

    def set_proj_root(self: OsPathInfo, proj_root: str) -> None:
        global _ROOT_PATH_PREFIX
        assert _ROOT_PATH_PREFIX is None, "proj_root already set to {0}".format(
            _ROOT_PATH_PREFIX
        )
        trail_slash_if_missing = "" if proj_root.endswith("/") else "/"
        _ROOT_PATH_PREFIX = proj_root + trail_slash_if_missing

    def get_path_rel_proj_root(self: OsPathInfo, cred_file_name: str) -> str:
        # return cred_file_name
        global _ROOT_PATH_PREFIX
        assert _ROOT_PATH_PREFIX is not None, "proj_root not set"
        # mid_path = _get_mid_path(thirdPtSvc)
        return _ROOT_PATH_PREFIX + cred_file_name


# def _get_mid_path(svc_type: ThirdPtSvcType) -> str:
#     mid_dir_name = "/auth/prod" if CURRENT_ENV == CurrentEnvEnum.PROD else "/auth/stage"
#     if svc_type == ThirdPtSvcType.FIR_USER:
#         # file_name = _env_vars.FIREBASE_ADMIN_CREDENTIAL
#         return mid_dir_name  # + "/" + file_name
#     elif svc_type == ThirdPtSvcType.FIR_ADMIN:
#         return mid_dir_name
#     elif svc_type == ThirdPtSvcType.GCP_APIS:
#         return mid_dir_name
#     elif svc_type == ThirdPtSvcType.EMAIL:
#         return mid_dir_name


class EnvVarVals(metaclass=Singleton):
    """ """

    def __init__(self) -> None:
        if self.init_completed:
            return
        self.CURRENT_ENV = CurrentEnvEnum[os.environ.get("ENV", "LOCAL")]
        self.init_completed = True

    # current runtime env as CurrentEnvEnum
    # @property
    # def CURRENT_ENV(self: EnvVarVals) -> CurrentEnvEnum:
    #     return CurrentEnvEnum[os.environ.get("ENV", "LOCAL")]

    # Root path of project
    @property
    def PROJECT_PATH(self: EnvVarVals) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    @property
    def APP_ID(self: EnvVarVals) -> str:
        return os.environ.get("APP_ID", "1:695770025165:web:c9f839379c3397c80a6d84")

    @property
    def DEBUG(self: EnvVarVals) -> bool:
        dStr: str = os.environ.get("DEBUG", "false")
        return dStr != "false"

    @property
    def TESTING(self: EnvVarVals) -> bool:
        dStr: str = os.environ.get("TESTING", "false")
        return dStr != "false"

    @property
    def PORT(self: EnvVarVals) -> int:
        return int(os.environ.get("PORT", "80"))

    @property
    def SECRET_KEY(self: EnvVarVals) -> str:
        return os.environ.get("SECRET_KEY", "iufh97531defhihh3")

    @property
    def PROJ_ID(self: EnvVarVals) -> str:
        return os.environ.get("PROJ_ID", "tsapi-stage2")

    @property
    def REGION_ID(self: EnvVarVals) -> str:
        return os.environ.get("REGION_ID", "us-central1")

    @property
    def HOST_URL(self: EnvVarVals) -> str:
        return os.environ.get("HOST_URL", "localhost")

    @property
    def BASE_URL(self: EnvVarVals) -> str:
        return os.environ.get("BASE_URL", "tsapi-stage2.appspot.com/")

    @property
    def FIR_DB_URL(self: EnvVarVals) -> str:
        return os.environ.get(
            "FIR_DB_URL", "https://tsapi-stage2-default-rtdb.firebaseio.com/"
        )

    @property
    def FIREBASE_ADMIN_CREDENTIAL(self: EnvVarVals) -> str:
        return os.environ.get(
            "FIREBASE_ADMIN_CREDENTIAL",
            "auth/stage/ts-firebase-adminsdk.json",
        )

    @property
    def GOOGLE_APPLICATION_CREDENTIALS(self: EnvVarVals) -> str:
        return os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS",
            "auth/stage/ts-firebase-adminsdk.json",
        )

    @property
    def STORAGE_BUCKET_ROOT_PATH(self: EnvVarVals) -> str:
        return os.environ.get("STORAGE_BUCKET_ROOT_PATH", "example-gcs-bucket")

    @property
    def FIREBASE_CFG(self: EnvVarVals) -> dict[str, str]:
        """
        self.api_key = config["apiKey"]
        self.auth_domain = config["authDomain"]
        self.database_url = config["databaseURL"]
        self.storage_bucket = config["storageBucket"]

        defaults below are for stage2
        """
        return {
            "apiKey": "_apiKey_",
            "authDomain": "_authDomain_",
            "databaseURL": self.FIR_DB_URL,
            "projectId": self.PROJ_ID,
            "storageBucket": self.STORAGE_BUCKET_ROOT_PATH,
            "messagingSenderId": "_messagingSenderId_",
            "appId": self.APP_ID,
            "measurementId": "YOUR_MEASUREMENT_ID",
            "serviceAccount": self.FIREBASE_ADMIN_CREDENTIAL,
        }

    def list_prop_names(self) -> list[str]:
        selfDirAsLst = list(dir(self))
        propNameLst = [
            pName
            for pName in selfDirAsLst
            if not pName.startswith("_")
            and not type(getattr(self, pName)) == types.MethodType
        ]
        return propNameLst


CURRENT_ENV: CurrentEnvEnum = EnvVarVals().CURRENT_ENV


# if __name__ == "__main__":
#     # relative import of singleton fails here
#     envs = EnvVarVals()
#     instProps = dir(envs)
#     envNames = [
#         pName
#         for pName in list(instProps)
#         if not pName.startswith("_")
#         and not type(getattr(envs, pName)) == types.MethodType
#     ]
#     print("In {0} environment:".format(CURRENT_ENV.name))
#     for nam in envNames:
#         print("\t{0} == {1}".format(nam, getattr(envs, nam)))
