from basic.http.http_request import HTTPRequest

def filter_create_queue(request: HTTPRequest):
    try:
        if "JMSDestinationType" in request.data and request.data["JMSDestinationType"] == "queue":
            return True
        return False
    except Exception:
        return False

def filter_create_topic(request: HTTPRequest):
    try:
        if "JMSDestinationType" in request.data and request.data["JMSDestinationType"] == "topic":
            return True
        return False
    except Exception:
        return False

def filter_delete_queue(request: HTTPRequest):
    try:
        if "JMSDestinationType" in request.params and request.params["JMSDestinationType"] == "queue":
            return True
        return False
    except Exception:
        return False

def filter_delete_topic(request: HTTPRequest):
    try:
        if "JMSDestinationType" in request.params and request.params["JMSDestinationType"] == "topic":
            return True
        return False
    except Exception:
        return False

filter_method = {
    "create_queue": filter_create_queue,
    "create_topic": filter_create_topic,
    "delete_queue": filter_delete_queue,
    "delete_topic": filter_delete_topic,
}

# 执行train
# filter_path="example.activemq.api_docs.filter_method" python normal_activemq.py