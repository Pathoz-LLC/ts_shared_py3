import os

#
from ts_shared_py3.config.env_vars import *

# OsPathInfo is a singleton;  must set path before importing client_admin
# OsPathInfo().set_proj_root(os.path.dirname(os.path.abspath(__file__)))
OsPathInfo().set_proj_root("/Users/dgaedcke/dev/Touchstone/Server/ts_main_api_server/")
#
from ts_shared_py3 import *
from ts_shared_py3.api_data_classes import *
from ts_shared_py3.api_data_classes.community import *
from ts_shared_py3.models import *
from ts_shared_py3.enums import *
from ts_shared_py3.schemas import *
from ts_shared_py3.wrappers import *

from ts_shared_py3.scoring import *

# from ts_shared_py3.scoring import *
from ts_shared_py3.scoring import *
from ts_shared_py3.services import *
from ts_shared_py3.config.behavior.load_yaml import *


from ts_shared_py3.services.firebase.client_admin import (
    firebase_post,
    firebase_put,
    firebase_patch,
)


# to look for errors or import probs, run this:
#  python src/main_validate.py


# print(enums)
# print(config)
# print(models)
# print(schemas)
# print(utils)
# print(scoring)

cfe1 = CommunityFeedEvent.testDefault()

jsonData = cfe1.toJson

cfe2 = CommunityFeedEvent.Schema().loads(jsonData)

assert isinstance(cfe2, CommunityFeedEvent)
# print(type(cfe2))
print("cfe hydrated:")
print(cfe2.toDict)


firebase_post("commNews/usa-2023-07-2", cfe2.toDict)
