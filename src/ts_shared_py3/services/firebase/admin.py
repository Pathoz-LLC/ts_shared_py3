from firebase_admin import initialize_app, credentials
from ...constants import FIREBASE_CREDS_PATH, PROJ_ID


# usage
# from common.firebase.admin import tsFirebaseApp


# provided by firebase console as setup example
# import firebase_admin
# from firebase_admin import credentials
#
# cred = credentials.Certificate("path/to/serviceAccountKey.json")
# firebase_admin.initialize_app(cred)


# Use the credentials object to authenticate app instance
serviceCreds = credentials.Certificate(FIREBASE_CREDS_PATH)
config = {
    "databaseURL": "https://{0}.firebaseio.com/".format(PROJ_ID),
    "projectId": PROJ_ID,
}

try:
    tsFirebaseApp = initialize_app(serviceCreds, options=config)
except Exception as e:
    print("Could not initialize Firebase Admin")
    print(str(e))
