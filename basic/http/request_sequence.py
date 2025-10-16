from dataclasses import field
from typing import List, Iterator

import msgspec
import requests

from api.api_node import ApiNode
from basic.http.http_request import HTTPRequest


class RequestSequence(msgspec.Struct, tag="request_sequence"):
    reqs: list[HTTPRequest]
    
    def __getitem__(self, index: int) -> HTTPRequest:
        return self.reqs[index]
    
    def __setitem__(self, index: int, value: HTTPRequest) -> None:
        self.reqs[index] = value
    
    def __len__(self) -> int:
        return len(self.reqs)
    
    def __iter__(self) -> Iterator[HTTPRequest]:
        return iter(self.reqs)
    
    def __contains__(self, item: HTTPRequest) -> bool:
        return item in self.reqs
    
    def append(self, request: HTTPRequest) -> None:
        self.reqs.append(request)

    def pop(self, index: int = -1) -> HTTPRequest:
        return self.reqs.pop(index)

    def execute(self, ip: str, port: int, session = requests.session()) -> List[requests.Response]:
        """执行整个请求序列"""
        if not self.reqs:
            raise ValueError("Empty request sequence")
        responses = []
        for request in self.reqs:
            try:
                response = request.session_send(ip, port, session)
                responses.append(response)
            except Exception as e:
                # 可以根据需求决定是否继续执行后续请求
                raise Exception(f"Request failed: {str(e)}")

        return responses
    
    def get_api_list(self) -> list[ApiNode]:
        """获取请求序列中的Api列表"""
        api_list: list[ApiNode] = []
        for request in self.reqs:
            api_list.append(msgspec.msgpack.decode(request.api, type=ApiNode))
        return api_list
