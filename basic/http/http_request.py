import base64
from enum import Enum
from io import BytesIO
import io
from typing import Any
from loguru import logger
from collections.abc import Sequence
import msgspec
import requests


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    MOVE = "MOVE"


class HTTPRequest(msgspec.Struct, tag="http_request"):
    api: bytes
    path: str
    method: HTTPMethod
    headers: Any = None
    params: Any = None
    data: Any = None
    json: Any = None
    data: Any = None
    files: Any = None
    
    def _process_json_data(self, data: Any) -> Any:
        """递归处理JSON数据，将字符串布尔值和数字转换为对应的Python类型"""
        if data is None:
            return data
        
        if isinstance(data, dict):
            return {k: self._process_json_data(v) for k, v in data.items()}
        
        if isinstance(data, list):
            return [self._process_json_data(item) for item in data]
        
        if isinstance(data, str):
            if data.lower() == 'true':
                return True
            elif data.lower() == 'false':
                return False
            try:
                if '.' not in data:
                    return int(data)
            except (ValueError, TypeError):
                pass
            try:
                return float(data)
            except (ValueError, TypeError):
                pass
        
        # 如果无法转换，返回原值
        return data

    def send(self, ip: str, port: int) -> requests.Response:
        """发送HTTP请求"""
        headers = None
        if self.headers:
            headers = {k: v for k, v in self.headers.items() 
                      if k.lower() != 'content-type'}
        
        # 转换json数据，将字符串布尔值和数字转换为对应的Python类型
        processed_json = self._process_json_data(self.json) if self.json else None
        
        return requests.request(
            headers=headers,
            method=self.method.value,
            url=f"http://{ip}:{port}{self.path}",
            data=self.data,
            json=processed_json,
            params=self.params,
            files={
                k: base64.b64decode(v.encode())
                for k, v in self.files.items()
            } if self.files else None
        )
    def session_send(self, ip:str, port:int, session: requests.Session) -> requests.Response:
        """使用session发送HTTP请求"""
        headers = None
        if self.headers:
            headers = {k: v for k, v in self.headers.items() 
                      if k.lower() != 'content-type'}
        processed_json = self._process_json_data(self.json) if self.json else None
        return session.request(
            method=self.method.value,
            url=f"http://{ip}:{port}{self.path}",
            data=self.data,
            json=processed_json,
            params=self.params,
            headers=headers,
            files={
                k: base64.b64decode(v.encode())
                for k, v in self.files.items()
            } if self.files else None
        )
    """
    def show(self):
        # 打印请求信息
        json_dict = {"path": f"{self.method.value} {self.path}"}
        for key in ["params", "json", "data", "files", "headers"]:
            value = getattr(self, key, None)
            if key == "headers" and value:
                # 不区分大小写删除 Content-Type
                value = {k: v for k, v in value.items() if k.lower() != 'content-type'}
            if value:
                json_dict[key] = value
        return json_dict
    """

    def show(self):
        """打印请求信息"""
        def encode_bytes_inplace(obj):
            # 仅在 show 内部使用的小闭包，不额外对外暴露
            if isinstance(obj, (bytes, bytearray, memoryview)):
                return base64.b64encode(bytes(obj)).decode("utf-8")
            if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
                t = type(obj)
                try:
                    return t(encode_bytes_inplace(x) for x in obj)
                except TypeError:
                    return [encode_bytes_inplace(x) for x in obj]
            return obj

        json_dict = {"path": f"{self.method.value} {self.path}"}
        for key in ["params", "json", "data", "files", "headers"]:
            value = getattr(self, key, None)

            if key == "headers" and value:
                # 不区分大小写删除 Content-Type
                value = {k: v for k, v in value.items() if k.lower() != "content-type"}

            # 对 data / files 的 bytes 值进行 base64 编码
            if key in ("data", "files") and value is not None:
                value = encode_bytes_inplace(value)

            if value:
                json_dict[key] = value
        return json_dict
    
if __name__ == '__main__':
    from loguru import logger
    req = HTTPRequest(
        api=b"test_api",
        path="/test_path",
        method=HTTPMethod.GET,
        params={"a": 1, "b": 2},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"},
        files={"file": b"Hello, world!"},
    )
    logger.debug("请求详情:{}", req.show())