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

    PROJ_ID: str = "playerbusterapi"
    APP_ID: str = "com.pathoz.touchstone.stage"
    STORAGE_BUCKET_ROOT_PATH: str = "example-gcs-bucket"
    GOOGLE_APPLICATION_CREDENTIALS: str = "auth/stage/tsapipy3-28638db28462.json"

    # @property
    def GOOGLE_CRED_CERT(self: GcpSvcsCfg) -> credentials.Certificate:
        return credentials.Certificate(self.GOOGLE_APPLICATION_CREDENTIALS)

    def __post_init__(self: GcpSvcsCfg):
        self._set_gcp_creds_path()

    def _set_gcp_creds_path(self: GcpSvcsCfg) -> None:
        """update GOOGLE_APPLICATION_CREDENTIALS
        on this obj & also in ENV memory
        """

        path_to_cred_file = OsPathInfo().get_credential_path(
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
    fir_db_url: str = "https://playerbusterapi.firebaseio.com"
    firebase_admin_credential: str = (
        "playerbusterapi-firebase-adminsdk-6ksdg-b582e4140c.json"
    )

    apiKey: str = "YOUR_API_KEY"
    authDomain: str = "YOUR_API_DOMAIN"
    databaseURL: str = "YOUR_URL"
    projectId: str = "playerbusterapi"
    storageBucket: str = "example-gcs-bucket"
    messagingSenderId: str = "YOUR_MESSENGER_ID"
    appId: str = "com.pathoz.touchstone.stage"
    measurementId: str = "YOUR_MEASUREMENT_ID"

    @property
    def hardcoded_dict(self: FirebaseCfg) -> dict[str, str]:
        # web key:  AIzaSyDATAObZ5IQOORmVqOwYETB-5xhTnyhBCA
        return {
            "apiKey": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQClzq3QDyYr7sB8\n61SZ8sCWYA77eSqELPqi37Z7e046LlfalHuw6SbSW5vG+j4dD21bJUN+6a7Xgsob\nT5s9O2HZJCVf+44PnuWxeBatl4RTbv4/3LDd9szPe/PrGmi3Nda9Q6gKR6Ap4vw2\neVX6WR3e+VDXM30e9FjvleySJNyhvNL9+Lf6mNR8jWqNUVlKCg7WYUPQw44919nj\nP+zeWqhO0PAtRA957EdRi81IYbdgbLtrTv+Qx46Tax0Ej56NkQ0Q+ftBBWdoptSC\n+S0FZ9FaaJOv5i9p3eB/SjYQLUlV36Byi5z/MK7IWhoSvolanbFHBirtHbc0hNhF\nP4+y2LixAgMBAAECggEABE2x+zV5cyh2PIfLIVfIod6KZQKHFPkp5DJURS41IJN1\nWkoCT9wtUsZn66kxFYYB+5yi/NdJ33QYlM7jI5q39m/WvIAF9ufT5GBOjmDhYVz/\nIl8zA//U3wnDkfWUhDTUhwMLiIDFanDmxO8vSRkpClGERKGkfLow2L8WbdChHV2D\nlgAm+lKLChvzAydWayxE6uyDTaPim9HyxmX9KqB8dtIoPMoFjGaWOWWs6EPGW3JS\nSgGK/fDbqlK4xaw+zkAmNfF3ePbkr1nEfHqvcuX2VQqLptpT++3MAJWLwMeKvZsi\nDhhSe5im7Hesz+c69y0G8JPMGrVNjSUtL+W6zsHisQKBgQDSJi4oa7+AFuzCXsht\n/TZnfW49Zv6hlbUcImJtvMs0pOwFPePUxrxAQ6c11j29/TabvvBNGkiehaT0q+QA\nf6boJEUFNV01ZygZgunXbP0RECS8IZ1ZHSnyCrX3F4i/XMhW+YfIhD9uP6K2ySuc\n3QTLwC230CqNAhENdE1RGrVw/QKBgQDJ+8zSTvVrLL2I3MLGgFg69Wd6Rl+Zxppz\nDafVbNzLgl6pxto71yL9k0AzONkVC9HHu3H2HWwvPIVtqtcwt4jaHMPMSs/UW7oN\nSVPSkqLaU3bB0upZC5HHRKM+xZQ06x0Ol8+FB1acUiU15mNiuOUuuqgv6gUJBQrY\nDI6B8eG+xQKBgQCOyRRZsIQoUutBUcdbPE3n2Ui6/a0LOz4YRKCeMUXcmiYnlZqk\nqvejrpQBN3UyDsc44W5C5RXsZ5/iApzjXdiZKHOhC1Yuf822L8YU8l+sZUygazKP\nJwqmA3MJ1Xq7kx4oQllo+7phfWlgSqWQanfkvMoTd6RBtOLDQn96GOypPQKBgCSQ\niMupr5PvTYBxNnFo2pARzOG9y6Cy61LYrgFc67uLpkdl0Cv1DkiJV53uNJ4yvY9C\nx6aePO9wLVdlDf+rugKCIo/hGy5+THgLRjlggkqzwVPlMrdb+M/yBPtgGSxbQ69Y\nnCCg63TxCftv8Z31isei0r+Zxb+UQhpKa6Hqf8thAoGAYu7hib/HwpnsjRMuzrzG\n+YXX/gGp45aAOKoEtqlYEGBhSLBV+FUQuhQt9Srg/U5U7fvs4M2/lwxFn2Dl7M58\nviS2mJUGEhefoqm87epW71JynZWJKPr6M2gX4tIdSIGs06Njy4rrjg9I5nbI0S56\nINMA7ejml6O34SdGNpk6Vy8=\n-----END PRIVATE KEY-----\n",
            "authDomain": "https://accounts.google.com/o/oauth2/auth",
            "databaseURL": "https://playerbusterapi.firebaseio.com/",
            "projectId": "playerbusterapi",
            "storageBucket": "playerbusterapi.appspot.com",
            "messagingSenderId": "115850684003",
            "appId": "com.pathoz.touchstone.stage",
            "measurementId": "YOUR_MEASUREMENT_ID",
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
    JWT_SECRET_KEY: str = "iufh97531defhihh3"  # Change this!
    JWT_ACCESS_TOKEN_EXPIRES: int = 36000
    JWT_ERROR_MESSAGE_KEY: str = "jwt invalid or expired"

    # SECRET_KEY = secrets.token_urlsafe(16)
    # WTF_CSRF_SECRET_KEY = secrets.token_urlsafe(16)
    WTF_CSRF_CHECK_DEFAULT: bool = False


@dataclass(frozen=False)
class LibCfg(CfgBaseIfc, metaclass=Singleton):
    """ """

    JSON_SORT_KEYS: bool = False
