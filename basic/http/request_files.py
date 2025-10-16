import msgspec
from basic.http.http_request import HTTPRequest
from typing import Any

class RequestFile(msgspec.Struct, tag="request_files", frozen=True):
    request: HTTPRequest
    read: list[str]
    write: list[str]
    