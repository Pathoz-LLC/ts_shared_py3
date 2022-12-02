class PushError(BaseException):
    """Base class for other exceptions"""

    pass


class UserNotFoundErr(PushError):
    """user ID not found in DB"""

    pass


class MissingReqFieldErr(PushError):
    """user ID not found in DB"""

    pass
