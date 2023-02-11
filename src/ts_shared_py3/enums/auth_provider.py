from __future__ import annotations
from enum import IntEnum, unique, auto


@unique
class AuthProvider(IntEnum):
    """who user used to sign in"""

    UNPW = auto()  # username & password
    FACEBOOK = auto()
    GOOGLE = auto()
    APPLE = auto()
