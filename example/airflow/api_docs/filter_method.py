from basic.http.http_request import HTTPRequest

def filter_example_bash_operator(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_bash_operator"
    except Exception:
        return False

def filter_example_branch_dop_operator_v3(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_branch_dop_operator_v3"
    except Exception:
        return False

def filter_example_branch_operator(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_branch_operator"
    except Exception:
        return False

def filter_example_complex(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_complex"
    except Exception:
        return False

def filter_example_external_task_marker_child(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_external_task_marker_child"
    except Exception:
        return False

def filter_example_external_task_marker_parent(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_external_task_marker_parent"
    except Exception:
        return False

def filter_example_http_operator(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_http_operator"
    except Exception:
        return False

def filter_example_nested_branch_dag(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_nested_branch_dag"
    except Exception:
        return False

def filter_example_passing_params_via_test_command(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_passing_params_via_test_command"
    except Exception:
        return False

def filter_example_pig_operator(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_pig_operator"
    except Exception:
        return False

def filter_example_python_operator(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_python_operator"
    except Exception:
        return False

def filter_example_short_circuit_operator(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_short_circuit_operator"
    except Exception:
        return False

def filter_example_skip_dag(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_skip_dag"
    except Exception:
        return False

def filter_example_subdag_operator(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_subdag_operator"
    except Exception:
        return False

def filter_example_trigger_controller_dag(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_trigger_controller_dag"
    except Exception:
        return False

def filter_example_trigger_target_dag(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_trigger_target_dag"
    except Exception:
        return False

def filter_example_xcom(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "example_xcom"
    except Exception:
        return False

def filter_latest_only(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "latest_only"
    except Exception:
        return False

def filter_latest_only_with_trigger(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "latest_only_with_trigger"
    except Exception:
        return False

def filter_test_utils(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "test_utils"
    except Exception:
        return False

def filter_tutorial(request: HTTPRequest) -> bool:
    try:
        return request.params.get("dag_id") == "tutorial"
    except Exception:
        return False

filter_method = {
    "example_bash_operator": filter_example_bash_operator,
    "example_branch_dop_operator_v3": filter_example_branch_dop_operator_v3,
    "example_branch_operator": filter_example_branch_operator,
    "example_complex": filter_example_complex,
    "example_external_task_marker_child": filter_example_external_task_marker_child,
    "example_external_task_marker_parent": filter_example_external_task_marker_parent,
    "example_http_operator": filter_example_http_operator,
    "example_nested_branch_dag": filter_example_nested_branch_dag,
    "example_passing_params_via_test_command": filter_example_passing_params_via_test_command,
    "example_pig_operator": filter_example_pig_operator,
    "example_python_operator": filter_example_python_operator,
    "example_short_circuit_operator": filter_example_short_circuit_operator,
    "example_skip_dag": filter_example_skip_dag,
    "example_subdag_operator": filter_example_subdag_operator,
    "example_trigger_controller_dag": filter_example_trigger_controller_dag,
    "example_trigger_target_dag": filter_example_trigger_target_dag,
    "example_xcom": filter_example_xcom,
    "latest_only": filter_latest_only,
    "latest_only_with_trigger": filter_latest_only_with_trigger,
    "test_utils": filter_test_utils,
    "tutorial": filter_tutorial,
}