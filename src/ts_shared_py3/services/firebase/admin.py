from pathlib import Path
from firebase_admin import initialize_app, credentials

#
from ...constants import FIR_CREDS_FILENAME, PROJ_ID
from ...config.env_vars import OsPathInfo, ThirdPtSvcType

# usage
# from common.firebase.admin import tsFirebaseApp


# provided by firebase console as setup example
# import firebase_admin
# from firebase_admin import credentials
#
# cred = credentials.Certificate("path/to/serviceAccountKey.json")
# firebase_admin.initialize_app(cred)


# Use the credentials object to authenticate app instance
creds_path = OsPathInfo().get_credential_path(
    ThirdPtSvcType.FIR_ADMIN, FIR_CREDS_FILENAME
)
# print("creds_path: {0}".format(creds_path))
serviceCreds = credentials.Certificate(creds_path)
config = {
    "databaseURL": "https://{0}.firebaseio.com/".format(PROJ_ID),
    "projectId": PROJ_ID,
}

try:
    tsFirebaseApp = initialize_app(serviceCreds, options=config)
except Exception as e:
    print("Could not initialize Firebase Admin")
    print(str(e))
