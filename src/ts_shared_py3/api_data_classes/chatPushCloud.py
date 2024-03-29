from datetime import date
from typing import ClassVar, Type
from dataclasses import field, fields, make_dataclass
from marshmallow_dataclass import dataclass
from marshmallow import Schema

from .base import BaseApiData
from ..schemas.base import DataClassBaseSchema

"""
msg types related to users chatting
    and also APN/GCM  (push notifications)
"""

# usage
# from common.messages.chatPushCloud import InitChatMessage, ChatInfoMessage, PushNotifyMessage, SubscribeTagPnMessage


# class ThreadIdMessage(messages.Message):
#     thread_id = messages.IntegerField(1)    # optional if resuming a prior chat
# StartChatMessage = compose(InitChatMessage, ThreadIdMessage)


@dataclass(base_schema=DataClassBaseSchema)
class ChatInfoMessage(BaseApiData):
    # tells the client how to auth at the XMPP server
    juser_id: str = field(default="")
    jpw: str = field(default="")
    jnick: str = field(default="")
    thread_id: int = field(
        default=0, metadata=dict(required=True)
    )  # tell client the ChatLog ID  (purpose unclear)
    #
    Schema: ClassVar[Type[Schema]] = Schema


# class StoreTokenMessage(messages.Message):
#     # tells the client how to auth at the XMPP server
#     juser_id = messages.StringField(1)
#     jpw = messages.StringField(2)
#     jnick = messages.StringField(3)
#     thread_id = messages.IntegerField(4)    # tell client the ChatLog ID  (purpose unclear)


@dataclass(base_schema=DataClassBaseSchema)
class PushNotifyMessage(BaseApiData):
    userId: str = field(default="", metadata=dict(required=True))
    regToken: str = field(default="", metadata=dict(required=True))
    deviceType: str = field(
        default="", metadata=dict(required=True)
    )  # actual device type;  to decide between apns & gcm
    enable: bool = field(default=True)
    isAndroid: bool = field(default=False)
    #
    Schema: ClassVar[Type[Schema]] = Schema


@dataclass(base_schema=DataClassBaseSchema)
class SubscribeTagPnMessage(BaseApiData):
    userId: str = field(default="", metadata=dict(required=True))
    regToken: str = field(default="", metadata=dict(required=True))
    tag: str = field(default="", metadata=dict(required=True))
    allDevices: bool = field(default=True)
    remove: bool = field(default=True)
    #
    Schema: ClassVar[Type[Schema]] = Schema


ChatInfoMessage.Schema.__model__ = ChatInfoMessage
PushNotifyMessage.Schema.__model__ = PushNotifyMessage
SubscribeTagPnMessage.Schema.__model__ = SubscribeTagPnMessage
