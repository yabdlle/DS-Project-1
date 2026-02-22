from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PutRequest(_message.Message):
    __slots__ = ("key", "textbook_chunk", "embedding")
    KEY_FIELD_NUMBER: _ClassVar[int]
    TEXTBOOK_CHUNK_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_FIELD_NUMBER: _ClassVar[int]
    key: str
    textbook_chunk: str
    embedding: bytes
    def __init__(self, key: _Optional[str] = ..., textbook_chunk: _Optional[str] = ..., embedding: _Optional[bytes] = ...) -> None: ...

class PutResponse(_message.Message):
    __slots__ = ("overwritten",)
    OVERWRITTEN_FIELD_NUMBER: _ClassVar[int]
    overwritten: bool
    def __init__(self, overwritten: bool = ...) -> None: ...

class StreamEmbeddingsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class EmbeddingEntry(_message.Message):
    __slots__ = ("key", "embedding")
    KEY_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_FIELD_NUMBER: _ClassVar[int]
    key: str
    embedding: bytes
    def __init__(self, key: _Optional[str] = ..., embedding: _Optional[bytes] = ...) -> None: ...

class GetTextRequest(_message.Message):
    __slots__ = ("key",)
    KEY_FIELD_NUMBER: _ClassVar[int]
    key: str
    def __init__(self, key: _Optional[str] = ...) -> None: ...

class GetTextResponse(_message.Message):
    __slots__ = ("found", "textbook_chunk")
    FOUND_FIELD_NUMBER: _ClassVar[int]
    TEXTBOOK_CHUNK_FIELD_NUMBER: _ClassVar[int]
    found: bool
    textbook_chunk: str
    def __init__(self, found: bool = ..., textbook_chunk: _Optional[str] = ...) -> None: ...

class DeleteRequest(_message.Message):
    __slots__ = ("key",)
    KEY_FIELD_NUMBER: _ClassVar[int]
    key: str
    def __init__(self, key: _Optional[str] = ...) -> None: ...

class DeleteResponse(_message.Message):
    __slots__ = ("deleted",)
    DELETED_FIELD_NUMBER: _ClassVar[int]
    deleted: bool
    def __init__(self, deleted: bool = ...) -> None: ...

class ListRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListResponse(_message.Message):
    __slots__ = ("keys",)
    KEYS_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, keys: _Optional[_Iterable[str]] = ...) -> None: ...

class HealthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthResponse(_message.Message):
    __slots__ = ("server_name", "server_version", "key_count")
    SERVER_NAME_FIELD_NUMBER: _ClassVar[int]
    SERVER_VERSION_FIELD_NUMBER: _ClassVar[int]
    KEY_COUNT_FIELD_NUMBER: _ClassVar[int]
    server_name: str
    server_version: str
    key_count: int
    def __init__(self, server_name: _Optional[str] = ..., server_version: _Optional[str] = ..., key_count: _Optional[int] = ...) -> None: ...
