import json
from typing import Any

import requests

from basic.http.http_request import HTTPMethod, HTTPRequest
import urllib.parse
import msgspec

class RequestResponse(msgspec.Struct, tag="request_response", frozen=True):
    request: HTTPRequest
    response: requests.Response
    @classmethod
    def from_request_json(cls, json_obj: Any) -> 'RequestResponse':
        """从JSON对象构造RequestResponse实例
        
        参数格式示例:
        {
            "http.request.method": "GET",
            "http.request.uri": "http://10.0.0.252:8983/api/cores?indexInfo=false&wt=json",
            "http.file_json": "null",
            "http.file_data": "null",
            "http.response.code": "200",
            "http.response.body": "..."
        }
        
        返回:
            RequestResponse对象
        """
        url_parts = urllib.parse.urlparse(json_obj.get("http.request.uri", ""))
        path = url_parts.path

        params = {}
        if url_parts.query:
            params = dict(urllib.parse.parse_qsl(url_parts.query))
        
        method_str = json_obj.get("http.request.method", "GET")
        method = HTTPMethod(method_str)
        
        json_data = None
        form_data = None
        file_json = json_obj.get("http.file_json")
        if isinstance(file_json, str) and file_json != "null":
            try:
                json_data = json.loads(file_json)
            except (json.JSONDecodeError, TypeError):
                pass
                
        file_data = json_obj.get("http.file_data")
        if isinstance(file_data, str) and file_data != "null":
            form_data = file_data
        
        host = url_parts.netloc
        path_parts = path.strip('/').split('/')
        api = path_parts[0] if path_parts else "api"
        
        request = HTTPRequest(
            api=msgspec.msgpack.encode(api),
            path=path,
            method=method,
            params=params,
            json=json_data,
            data=form_data
        )
        
        response_content = json_obj.get("http.response.body", "")
        response_code = int(json_obj.get("http.response.code", 200))
        
        mock_response = requests.Response()
        mock_response.status_code = response_code
        
        if isinstance(response_content, str):
            if response_content.startswith('"') and response_content.endswith('"'):
                try:
                    unescaped_content = json.loads(response_content)
                    if isinstance(unescaped_content, str):
                        mock_response._content = unescaped_content.encode('utf-8')
                    else:
                        mock_response._content = json.dumps(unescaped_content).encode('utf-8')
                except (json.JSONDecodeError, TypeError):
                    mock_response._content = response_content.encode('utf-8')
            else:
                mock_response._content = response_content.encode('utf-8')
        else:
            mock_response._content = json.dumps(response_content).encode('utf-8')
        
        return cls(request=request, response=mock_response)
