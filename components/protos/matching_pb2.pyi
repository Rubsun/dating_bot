from typing import ClassVar as _ClassVar
from typing import Iterable as _Iterable
from typing import Optional as _Optional

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class FindMatchesRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    def __init__(self, user_id: _Optional[str] = ...) -> None: ...

class FindMatchesResponse(_message.Message):
    __slots__ = ("matched_user_ids",)
    MATCHED_USER_IDS_FIELD_NUMBER: _ClassVar[int]
    matched_user_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, matched_user_ids: _Optional[_Iterable[str]] = ...) -> None: ...
