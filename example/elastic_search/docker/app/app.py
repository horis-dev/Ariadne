import base64
import copy
import pickle
from util import get_db_write, get_doc_write, get_doc_read, get_db_read, get_file_read, get_file_write, update_log_position
from flask import Flask, request, Response
import requests
import json

app = Flask(__name__)

SOLR_URL = "http://elastic_search:9200"

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])
def proxy(path):
    # 构建目标URL
    url = f"{SOLR_URL}/{path}"
    
    headers = {key: value for key, value in request.headers if key != 'Host'}
    
    # 转发
    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        params=request.args,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        stream=True,
        verify=False
    )
        
    # 统一的响应处理方式
    db_write = get_db_write()
    db_read = get_db_read()
    table_write = get_doc_write(f"/{path}")
    table_read = get_doc_read(f"/{path}")
    file_read = get_file_read()
    file_write = get_file_write()
    
    serialized = pickle.dumps(resp)
    processed_data = {
        "file_write": file_write,
        "file_read": file_read,
        "db_write": db_write,
        "db_read": db_read,
        "table_write": table_write,
        "table_read": table_read,
        "encoded_response": base64.b64encode(serialized).decode("utf-8")
    }
    update_log_position()
    
    # 返回JSON格式的响应
    response = Response(
        json.dumps(processed_data),
        200,
        content_type='application/json'
    )

    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 