from enum import Enum

class ContentType(str, Enum):
    APPLICATION_JSON = "application/json"
    APPLICATION_XML = "application/xml"
    TEXT_XML = "text/xml"
    APPLICATION_X_WWW_FORM_URLENCODED = "application/x-www-form-urlencoded"
    MULTIPART_FORM_DATA = "multipart/form-data"
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    APPLICATION_OCTET_STREAM = "application/octet-stream"
    APPLICATION_PDF = "application/pdf"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    APPLICATION_YAML = "application/yaml"
    APPLICATION_MSGPACK = "application/msgpack"