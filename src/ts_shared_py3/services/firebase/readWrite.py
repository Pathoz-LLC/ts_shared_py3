# try:
#     from functools import lru_cache
# except ImportError:
#     from functools32 import lru_cache

from .admin import tsFirebaseApp
from firebase_admin import db


# Memoize the authorized http, to avoid fetching new access tokens
# @lru_cache()
def _getDbRef(path: str):
    """Provides an authd http ref object."""
    # https://firebase.google.com/docs/reference/rest/database/user-auth
    # print("frDb path: {0}".format(path))
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
    dbRef = _getDbRef(path)
    dbRef.set(obj)


def firebase_patch(path: str, obj=None):
    """Update specific children or fields
    An HTTP PATCH allows specific children or fields to be updated without
    overwriting the entire object.
    Args:
        path - the url to the Firebase object to write.
        value - a json string.
    """
    dbRef = _getDbRef(path)
    dbRef.update(obj)


def firebase_post(path: str, obj=None):
    """Add an object to an existing list of data.
    An HTTP POST allows an object to be added to an existing list of data.
    A successful request will be indicated by a 200 OK HTTP status code. The
    response content will contain a new attribute "name" which is the key for
    the child added.
    Args:
        path - the url to the Firebase list to append to.
        value - a json string.
    """
    dbRef = _getDbRef(path)
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
    dbRef = _getDbRef(path)
    return dbRef.get()


def firebase_delete(path: str):
    """Removes the data at a particular path.
    An HTTP DELETE removes the data at a particular path.  A successful request
    will be indicated by a 200 OK HTTP status code with a response containing
    JSON null.
    Args:
        path - the url to the Firebase object to delete.
    """
    dbRef = _getDbRef(path)
    dbRef.delete()
