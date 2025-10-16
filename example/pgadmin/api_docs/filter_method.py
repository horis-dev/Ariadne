from basic.http.http_request import HTTPRequest

def filter_add_folder(request: HTTPRequest):
    try:
        if "mode" in request.json and request.json["mode"] == "addfolder":
            return True
        return False
    except Exception:
        return False
    
def filter_rename_folder(request: HTTPRequest):
    try:
        if "mode" in request.json and request.json["mode"] == "rename":
            return True
        return False
    except Exception:
        return False
    
def filter_delete_folder(request: HTTPRequest):
    try:
        if "mode" in request.json and request.json["mode"] == "delete":
            return True
        return False
    except Exception:
        return False


filter_method = {
    "add_folder": filter_add_folder,
    "rename_folder": filter_rename_folder,
    "delete_folder": filter_delete_folder,
}

# 执行train
# filter_path="example.pgadmin.api_docs.filter_method" python normal_pgadmin.py