from pathlib import Path
from firebase_admin import db, initialize_app, credentials

#
from ...constants import IS_RUNNING_LOCAL
from ...config.env_vars import OsPathInfo, ThirdPtSvcType, EnvVarVals, CURRENT_ENV

# usage
# from common.firebase.client_admin import firebase_post, firebase_put, firebase_patch

# Use the credentials object to authenticate app instance
configEnv = EnvVarVals()

creds_path = OsPathInfo().get_path_rel_proj_root(configEnv.FIREBASE_ADMIN_CREDENTIAL)
# print("1) creds_path: {0} for {1}".format(creds_path, configEnv.FIR_DB_URL))

serviceCreds = credentials.Certificate(creds_path)
config = {
    "databaseURL": configEnv.FIR_DB_URL,
    "projectId": configEnv.PROJ_ID,
}

try:
    tsFirebaseApp = initialize_app(serviceCreds, options=config)
except Exception as e:
    print("Could not initialize Firebase Admin")
    print(e)


# Memoize the authorized http, to avoid fetching new access tokens
# @lru_cache()
def _getDbRef(path: str) -> db.Reference:
    """Provides an authd http ref object."""
    # https://firebase.google.com/docs/reference/rest/database/user-auth
    # print("frDb path: {0}".format(path))
    assert tsFirebaseApp is not None
    return db.reference(path, app=tsFirebaseApp)


# [START rest_writing_data]
def firebase_put(path: str, obj=None):
    """Writes data to Firebase.
    An HTTP PUT writes an entire object at the given database path. Updates to
    fields cannot be performed without overwriting the entire object
    Args:
        path - the url to the Firebase object to write.
        value - a json string.
    """
    dbRef: db.Reference = _getDbRef(path)
    dbRef.set(obj)


def firebase_patch(path: str, obj=None):
    """Update specific children or fields
    An HTTP PATCH allows specific children or fields to be updated without
    overwriting the entire object.
    Args:
        path - the url to the Firebase object to write.
        value - a json string.
    """
    dbRef: db.Reference = _getDbRef(path)
    dbRef.update(obj)


def firebase_post(path: str, obj: map = None):
    """Add an object to an existing list of data.
    An HTTP POST allows an object to be added to an existing list of data.
    A successful request will be indicated by a 200 OK HTTP status code. The
    response content will contain a new attribute "name" which is the key for
    the child added.
    Args:
        path - the url to the Firebase list to append to.
        value - a json string.
    """
    dbRef: db.Reference = _getDbRef(path)
    dbRef.push(obj)


# [END rest_writing_data]


def firebase_get(path: str):
    """Read the data at the given path.
    An HTTP GET request allows reading of data at a particular path.
    A successful request will be indicated by a 200 OK HTTP status code.
    The response will contain the data being retrieved.
    Args:
        path - the url to the Firebase object to read.
    """
    dbRef: db.Reference = _getDbRef(path)
    return dbRef.get()


def firebase_delete(path: str):
    """Removes the data at a particular path.
    An HTTP DELETE removes the data at a particular path.  A successful request
    will be indicated by a 200 OK HTTP status code with a response containing
    JSON null.
    Args:
        path - the url to the Firebase object to delete.
    """
    dbRef: db.Reference = _getDbRef(path)
    dbRef.delete()
