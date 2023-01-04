from __future__ import annotations
from pathlib import Path
from enum import IntEnum, unique, auto

#
from ..env.env import CurrentEnv, CURRENT_ENV, EnvVarVals

_ROOT_PATH_PREFIX = None

# _env_vars = EnvVarVals()  # singleton obj


@unique
class ThirdPtSvcType(IntEnum):
    FB_LIMITED = auto()
    FB_ADMIN = auto()
    GCP_APP = auto()
    EMAIL = auto()

    def get_credential_path(self: ThirdPtSvcType, cred_file_name: str) -> str:
        global _ROOT_PATH_PREFIX
        if _ROOT_PATH_PREFIX is None:
            _ROOT_PATH_PREFIX = _get_root_path()
        mid_path = _get_mid_path(self)
        return _ROOT_PATH_PREFIX + mid_path + "/" + cred_file_name


def _get_root_path() -> str:
    # config root is two folders above this file
    config_dir_path = Path(__file__).absolute().parent.parent
    assert config_dir_path.is_dir, "oops--config should be a directory"
    return config_dir_path.as_posix() + "/"


def _get_mid_path(svc_type: ThirdPtSvcType) -> str:
    mid_dir_name = "auth/prod" if CURRENT_ENV == CurrentEnv.PROD else "auth/stage"
    if svc_type == ThirdPtSvcType.FB_LIMITED:
        # file_name = _env_vars.FIREBASE_ADMIN_CREDENTIAL
        return mid_dir_name  # + "/" + file_name
    elif svc_type == ThirdPtSvcType.FB_ADMIN:
        return mid_dir_name
    elif svc_type == ThirdPtSvcType.GCP_APP:
        return mid_dir_name
    elif svc_type == ThirdPtSvcType.EMAIL:
        return mid_dir_name

    # elif serviceType == ServiceType.FB_LIMITED:
    #     return ""
    # return
