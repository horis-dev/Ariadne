from basic.http.http_request import HTTPRequest

def filter_admin_edit_template(request: HTTPRequest):
    try:
        if "mact" in request.data and request.data["mact"] == "DesignManager,m1_,admin_edit_template,0":
            return True
        return False
    except Exception:
        return False
def filter_admin_settings(request: HTTPRequest):
    try:
        if "mact" in request.data and request.data["mact"] == "DesignManager,m1_,admin_settings,0":
            return True
        return False
    except Exception:
        return False
def filter_setprefs(request: HTTPRequest):
    try:
        if "mact" in request.data and request.data["mact"] == "ModuleManager,m1_,setprefs,0":
            return True
        return False
    except Exception:
        return False
def filter_admin_general_tab(request: HTTPRequest):
    try:
        if "mact" in request.data and request.data["mact"] == "DesignManager,m1_,admin_general_tab,0":
            return True
        return False
    except Exception:
        return False
def filter_addcategory(request: HTTPRequest):
    try:
        if "mact" in request.data and request.data["mact"] == "News,m1_,addcategory,0":
            return True
        return False
    except Exception:
        return False
    
def filter_clearcache(request: HTTPRequest):
    try:
        if "clearcache" in request.data:
            return True
        return False
    except Exception:
        return False
def filter_updatehierarchy(request: HTTPRequest):
    try:
        if "updatehierarchy" in request.data:
            return True
        return False
    except Exception:
        return False
def filter_updateurls(request: HTTPRequest):
    try:
        if "updateurls" in request.data:
            return True
        return False
    except Exception:
        return False
    
def filter_DesignManager(request: HTTPRequest):
    try:
        if "mact" in request.params and request.params["mact"] == "DesignManager,m1_,admin_settings,0":
            return True
        return False
    except Exception:
        return False
def filter_CMSContentManager(request: HTTPRequest):
    try:
        if "mact" in request.params and request.params["mact"] == "CMSContentManager,m1_,admin_settings,0":
            return True
        return False
    except Exception:
        return False
def filter_News(request: HTTPRequest):
    try:
        if "mact" in request.params and request.params["mact"] == "News,m1_,admin_settings,0":
            return True
        return False
    except Exception:
        return False
def filter_ModuleManager(request: HTTPRequest):
    try:
        if "mact" in request.params and request.params["mact"] == "ModuleManager,m1_,admin_settings,0":
            return True
        return False
    except Exception:
        return False
def filter_FileManager(request: HTTPRequest):
    try:
        if "mact" in request.params and request.params["mact"] == "FileManager,m1_,admin_settings,0":
            return True
        return False
    except Exception:
        return False

filter_method = {
    "admin_edit_template": filter_admin_edit_template,
    "admin_settings": filter_admin_settings,
    "setprefs": filter_setprefs,
    "admin_general_tab": filter_admin_general_tab,
    "addcategory": filter_addcategory,

    "clearcache": filter_clearcache,
    "updatehierarchy": filter_updatehierarchy,
    "updateurls": filter_updateurls,

    "DesignManager": filter_DesignManager,
    "CMSContentManager": filter_CMSContentManager,
    "News": filter_News,
    "ModuleManager": filter_ModuleManager,
    "FileManager": filter_FileManager,

}

# 执行train
# filter_path="example.cmsms.api_docs.filter_method" python normal_cmsms.py