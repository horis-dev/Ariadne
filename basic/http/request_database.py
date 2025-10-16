import msgspec

from basic.http.http_request import HTTPRequest

class RequestDatabase(msgspec.Struct, tag="request_database", frozen=True):
    request: HTTPRequest
    db_read: list[str]
    db_write: list[str]
    tables_read: list[str]
    tables_write: list[str]
