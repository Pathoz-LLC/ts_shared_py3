from __future__ import annotations
import os
from types import MethodType
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path

#
from firebase_admin import credentials
from ..utils.singleton import Singleton
from .env_vars import EnvVarVals, ThirdPtSvcType, OsPathInfo

""" NOTE:

    When the config value varies PER environment
    then the actual live values for the properties
    below should be set as ENV vars in one of:
        run-debug.sh
        app_stage.yaml
        app_prod.yaml

    ENV vars should have the SAME name as class vars below
"""

_envVars: EnvVarVals = EnvVarVals()
_list_env_var_names: list[str] = _envVars.list_prop_names()


# std interface to all config objs
class CfgBaseIfc(object):
    #
    def __post_init__(self: CfgBaseIfc):
        # copy EnvVar vals to associated properties
        for prop_name in _list_env_var_names:
            if hasattr(self, prop_name):
                envar_val = getattr(_envVars, prop_name, "--")
                if envar_val != "--":
                    setattr(self, prop_name, envar_val)

    @property
    def as_dict(self: CfgBaseIfc) -> dict[str, Any]:
        # filter out dunder-props & methods from return dict
        # remove this method from list
        lst_inst_prop_names = list(self.__dict__.keys())
        self_dir_as_lst: list[str] = filter(
            lambda nm: nm != "as_dict", lst_inst_prop_names
        )
        prop_names_to_keep = [
            pName
            for pName in self_dir_as_lst
            if not pName.startswith("_") and type(getattr(self, pName)) != MethodType
        ]

        applicable_props: dict[str, Any] = {}
        for keyName in prop_names_to_keep:
            applicable_props[keyName] = getattr(self, keyName)
        #
        # print("applicable_props on {0}:".format(self.__class__.__name__))
        # print(applicable_props)
        return applicable_props


@dataclass(frozen=False)
class FlaskWebAppCfg(CfgBaseIfc, metaclass=Singleton):
    """build in flask config vals"""

    DEBUG: bool = True
    TESTING: bool = True
    SECRET_KEY: str = ""
    HOST_URL: str = "localhost"  # "http://0.0.0.0"
    PORT: int = 8080  # both web and api
    # web root
    APPLICATION_ROOT: str = "/api"


@dataclass(frozen=False)
class OpenApiCfg(CfgBaseIfc, metaclass=Singleton):
    """
    https://swagger.io/specification/
    https://flask-smorest.readthedocs.io/en/latest/openapi.html

    API_TITLE & API_VERSION both
    get auto-copied into the info dict  (both required here)

    [servers] key will be added to API_SPEC_OPTIONS by flask
    """

    @property
    def as_dict(self: OpenApiCfg) -> dict[str, Any]:
        #
        d = self.__dict__.copy()
        # d["API_SPEC_OPTIONS"]["API_TITLE"] = self.API_TITLE
        # d["title"] = self.API_TITLE
        return d

    title: str = "TS Core API"
    version: str = "1.0.2"
    openapi_version: str = "3.0.2"
    # openapi_url_prefix: str = "api/"

    # openapi_redoc_path: str = "/redoc"
    # openapi_redoc_url: str = (
    #     "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    # )
    # openapi_json_path: str = "api-spec.json"
    # openapi_swagger_ui_path: str = "/"
    # openapi_swagger_ui_url: str = (
    #     "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.24.2/"
    # )
    servers: Dict[str, Any] = field(
        default_factory=lambda: [
            {
                "url": "http://127.0.0.1",
            },
        ]
    )

    info: Dict[str, Any] = field(
        default_factory=lambda: {
            # "title": "required",
            # "version": "required",
            "description": "Touchstone API server",
            "termsOfService": "http://pathoz.com/terms/",
            "contact": {"email": "dewey@pathoz.com"},
            "license": {
                "name": "MIT License",
                "url": "https://fr.wikipedia.org/wiki/Licence_MIT",
            },
        }
    )

    # @staticmethod
    # def _spec_factory(_):
    #     return {
    #     "host": "http://http://127.0.0.1",
    #     "info": {
    #         # "title": "required",
    #         # "version": "required",
    #         "description": "Touchstone API server",
    #         "termsOfService": "http://pathoz.com/terms/",
    #         "contact": {"email": "dewey@pathoz.com"},
    #         "license": {
    #             "name": "MIT License",
    #             "url": "https://fr.wikipedia.org/wiki/Licence_MIT",
    #         },
    #     },
    # }


@dataclass(frozen=False)
class GcpSvcsCfg(CfgBaseIfc, metaclass=Singleton):
    """defaults only;  most in ENV vars"""

    PROJ_ID: str = "tsapi-stage2"
    APP_ID: str = "com.pathoz.touchstone.stage"
    STORAGE_BUCKET_ROOT_PATH: str = "tsapi-stage2.appspot.com"
    GOOGLE_APPLICATION_CREDENTIALS: str = "auth/stage/ts-gae-admin.json"

    # @property
    def GOOGLE_CRED_CERT(self: GcpSvcsCfg) -> credentials.Certificate:
        return credentials.Certificate(self.GOOGLE_APPLICATION_CREDENTIALS)

    def __post_init__(self: GcpSvcsCfg):
        self._set_gcp_creds_path()

    def _set_gcp_creds_path(self: GcpSvcsCfg) -> None:
        """update GOOGLE_APPLICATION_CREDENTIALS
        on this obj & also in ENV memory
        """

        path_to_cred_file = OsPathInfo().get_path_rel_proj_root(
            thirdPtSvc=ThirdPtSvcType.GCP_APIS,
            cred_file_name=self.GOOGLE_APPLICATION_CREDENTIALS,
        )
        # mid_dir_name = "/prod" if CURRENT_ENV == CurrentEnvEnum.PROD else "/stage"
        # to_this_file: Path = Path(__file__).absolute()
        # to_config_dir: Path = to_this_file.parent

        # to_env_dir: Path = to_config_dir.as_posix() + "/auth" + mid_dir_name
        # path_to_cred_file = to_env_dir + "/" + self.GOOGLE_APPLICATION_CREDENTIALS
        # # print("path_to_cred_file:  {0}".format(path_to_cred_file))
        self.GOOGLE_APPLICATION_CREDENTIALS = path_to_cred_file
        GcpSvcsCfg.GOOGLE_APPLICATION_CREDENTIALS = path_to_cred_file
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path_to_cred_file


@dataclass(frozen=False)
class FirebaseCfg(CfgBaseIfc, metaclass=Singleton):
    fir_db_url: str = "https://tsapi-stage2-default-rtdb.firebaseio.com/"
    firebase_admin_credential: str = "auth/stage/ts-firebase-adminsdk.json"

    apiKey: str = ""
    authDomain: str = "https://accounts.google.com/o/oauth2/auth"
    databaseURL: str = "https://tsapi-stage2-default-rtdb.firebaseio.com/"
    projectId: str = "tsapi-stage2"
    storageBucket: str = "tsapi-stage2.appspot.com"
    messagingSenderId: str = "115850684003"
    appId: str = "com.pathoz.touchstone.stage"
    measurementId: str = "YOUR_MEASUREMENT_ID"
    serviceAccount: str = "auth/stage/ts-firebase-adminsdk.json"

    @property
    def hardcoded_dict(self: FirebaseCfg) -> dict[str, str]:
        # web key: ""
        return {
            "apiKey": "",
            "authDomain": "https://accounts.google.com/o/oauth2/auth",
            "databaseURL": "https://tsapi-stage2-default-rtdb.firebaseio.com/",
            "projectId": "tsapi-stage2",
            "storageBucket": "tsapi-stage2.appspot.com",
            "messagingSenderId": "115850684003",
            "appId": "com.pathoz.touchstone.stage",
            "measurementId": "YOUR_MEASUREMENT_ID",
            "serviceAccount": "auth/stage/ts-firebase-adminsdk.json",
        }

    # @property
    # def FIREBASE_ADMIN_CRED_CERT(self: FirebaseCfg) -> credentials.Certificate:
    #     return credentials.Certificate(self.firebase_admin_credential)


@dataclass(frozen=False)
class UserAuthCfg(CfgBaseIfc, metaclass=Singleton):
    """JWT, credentials & security vals"""

    JWT_TOKEN_LOCATION: str = "headers"
    JWT_HEADER_NAME: str = "ts-auth-token"
    JWT_HEADER_TYPE: str = "Bearer"
    JWT_SECRET_KEY: str = "iufh97531defhihh3"  # Changed by ENV vars!
    JWT_ACCESS_TOKEN_EXPIRES: int = 36000
    JWT_ERROR_MESSAGE_KEY: str = "jwt invalid or expired"

    # SECRET_KEY = secrets.token_urlsafe(16)
    # WTF_CSRF_SECRET_KEY = secrets.token_urlsafe(16)
    WTF_CSRF_CHECK_DEFAULT: bool = False


@dataclass(frozen=False)
class LibCfg(CfgBaseIfc, metaclass=Singleton):
    """ """

    JSON_SORT_KEYS: bool = False
