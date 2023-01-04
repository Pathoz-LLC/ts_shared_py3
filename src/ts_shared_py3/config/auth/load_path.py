from __future__ import annotations
from pathlib import Path
from enum import IntEnum, unique, auto

#
from ..env.env import CurrentEnv, CURRENT_ENV, EnvVarVals

_ROOT_PATH_PREFIX = None

_env_vars = EnvVarVals()


@unique
class ThirdPtSvcType(IntEnum):
    FB_LIMITED = auto()
    FB_ADMIN = auto()
    GCP_APP = auto()
    EMAIL = auto()

    @property
    def get_credential_path(self: ThirdPtSvcType, cred_file_name: str) -> str:
        global _ROOT_PATH_PREFIX
        if _ROOT_PATH_PREFIX is None:
            _ROOT_PATH_PREFIX = _get_root_path() + "/"
        mid_path = _get_mid_path()
        return _ROOT_PATH_PREFIX + mid_path + "/" + cred_file_name


def _get_root_path(self: ThirdPtSvcType) -> str:
    # config root is two folders above this file
    config_dir_path = Path(__file__).absolute().parent.parent
    assert config_dir_path.is_dir, "oops??"
    return config_dir_path.as_posix()


def _get_mid_path(self: ThirdPtSvcType) -> str:
    mid_dir_name = "/auth/prod" if CURRENT_ENV == CurrentEnv.PROD else "/auth/stage"
    if self == ThirdPtSvcType.FB_LIMITED:
        # file_name = _env_vars.FIREBASE_ADMIN_CREDENTIAL
        return mid_dir_name  # + "/" + file_name
    elif self == ThirdPtSvcType.FB_ADMIN:
        return mid_dir_name
    elif self == ThirdPtSvcType.GCP_APP:
        return mid_dir_name
    elif self == ThirdPtSvcType.EMAIL:
        return mid_dir_name

    # elif serviceType == ServiceType.FB_LIMITED:
    #     return ""
    # return
