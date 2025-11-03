from basic.http.http_request import HTTPRequest

def filter_func_node(request: HTTPRequest) -> bool:
    try:
        return request.params.get("runtime") == "node-16.0"
    except Exception:
        return False

def filter_func_php(request: HTTPRequest) -> bool:
    try:
        return request.params.get("runtime") == "php-8.0"
    except Exception:
        return False

def filter_func_ruby(request: HTTPRequest) -> bool:
    try:
        return request.params.get("runtime") == "ruby-3.0"
    except Exception:
        return False

def filter_func_python(request: HTTPRequest) -> bool:
    try:
        return request.params.get("runtime") == "python-3.9"
    except Exception:
        return False

def filter_service_account(request: HTTPRequest) -> bool:
    try:
        return request.params.get("service") == "account"
    except Exception:
        return False

def filter_service_avatars(request: HTTPRequest) -> bool:
    try:
        return request.params.get("service") == "avatars"
    except Exception:
        return False

def filter_service_database(request: HTTPRequest) -> bool:
    try:
        return request.params.get("service") == "database"
    except Exception:
        return False

filter_method = {
    "func_node": filter_func_node,
    "func_php": filter_func_php,
    "func_ruby": filter_func_ruby,
    "func_python": filter_func_python,
    "service_account": filter_service_account,
    "service_avatars": filter_service_avatars,
    "service_database": filter_service_database,
}

# 生成API依赖图前，要记得加环境变量： filter_path="example.appwrite.api_docs.filter_method" python xxx.py