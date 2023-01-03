from __future__ import annotations
from pathlib import Path
from enum import IntEnum, unique, auto

#
from ..env.env import CURRENT_ENV

_ROOT_PATH_PREFIX = None


@unique
class ServiceType(IntEnum):
    FB_LIMITED = auto()
    FB_ADMIN = auto()
    GCP_APP = auto()
    EMAIL = auto()

    @property
    def get_credential_path(self: ServiceType, cred_file_name: str):
        global _ROOT_PATH_PREFIX
        if _ROOT_PATH_PREFIX is None:
            _ROOT_PATH_PREFIX = _get_root_path()
        mid_path = _get_mid_path(self)
        return _ROOT_PATH_PREFIX + mid_path + "/" + cred_file_name


def _get_root_path():
    global _ROOT_PATH_PREFIX

    file_path = Path(__file__).absolute()

    # config root is one folder above this one
    _ROOT_PATH_PREFIX = file_path.joinpath


def _get_mid_path(serviceType: ServiceType):
    if serviceType == ServiceType.FB_LIMITED:
        return ""
    elif serviceType == ServiceType.FB_ADMIN:
        return ""
    elif serviceType == ServiceType.GCP_APP:
        return ""
    elif serviceType == ServiceType.EMAIL:
        return ""

    # elif serviceType == ServiceType.FB_LIMITED:
    #     return ""
    # return
