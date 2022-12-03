from functools import wraps
from flask import request, g  # , redirect, session

# from google.appengine.api import users


def auth_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        g.userId = request.headers.get("", "")
        g.userToken = request.headers.get("", "")
        g.user = None
        # if users.get_current_user() is None:
        #     return redirect(users.create_login_url(dest_url=request.url))
        return f(*args, **kwargs)

    return decorated_view
