from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.content_type import ContentType
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override

class AirflowApiDoc(Docable):

    a0 = ApiNode(
        path = "/admin",
        method = HTTPMethod.GET,
    )


    a1 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST, 
        params = "is_paused=${q_is_paused}&dag_id=example_trigger_target_dag",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_trigger_target_dag",
    )
    a2 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST, 
        params = "is_paused=${q_is_paused}&dag_id=example_bash_operator",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_bash_operator",
    )
    a3 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST, 
        params = "is_paused=${q_is_paused}&dag_id=example_branch_dop_operator_v3",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_branch_dop_operator_v3",
    )
    a4 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST, 
        params = "is_paused=${q_is_paused}&dag_id=example_branch_operator",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_trigger_target_dag",
    )
    a5 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_complex",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_complex",
    )
    a6 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_external_task_marker_child",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_external_task_marker_child",
    )
    a7 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_external_task_marker_parent",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_external_task_marker_parent",
    )
    a8 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_http_operator",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_http_operator",
    )
    a9 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_nested_branch_dag",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_nested_branch_dag",
    )
    a10 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_passing_params_via_test_command",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_passing_params_via_test_command",
    )
    a11 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_pig_operator",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_pig_operator",
    )
    a12 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_python_operator",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_python_operator",
    )
    a13 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_short_circuit_operator",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_short_circuit_operator",
    )
    a14 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_skip_dag",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_skip_dag"
    )
    a15 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_subdag_operator",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_subdag_operator",
    )
    a16 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_trigger_controller_dag",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_trigger_controller_dag",
    )
    a17 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=example_xcom",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "example_xcom",
    )
    a18 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=latest_only",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "latest_only",
    )
    a19 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=latest_only_with_trigger",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "latest_only_with_trigger",
    )
    a20 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=test_utils",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "test_utils",
    )
    a21 = ApiNode(
        path = "/admin/airflow/paused",
        method = HTTPMethod.POST,
        params = "is_paused=${q_is_paused}&dag_id=tutorial",
        headers='{"X-CSRFToken": "${hv_X-CSRFToken}"}',
        filter_id = "tutorial",
    )

    # GET Trigger DAG, 返回CSRF
    a22 = ApiNode(
        path = "/admin/airflow/trigger",
        method = HTTPMethod.GET,
        params = "dag_id=${q_dag_id}"
    )

    # POST Trigger DAG
    a23 = ApiNode(
        path = "/admin/airflow/trigger",
        method = HTTPMethod.POST,
        headers='{"Content-Type":"multipart/form-data"}', 
        data='{"dag_id":"${dv_dag_id}","conf":"${dv_conf}","csrf_token":"${dv_csrf_token}"}'
    )

    a24 = ApiNode(
        path = "/admin/airflow/dag_stats",
        method = HTTPMethod.GET,
    )

    a25 = ApiNode(
        path="/admin/airflow/refresh",
        method=HTTPMethod.POST,
        params="dag_id=${q_dag_id}",
        headers='{"Content-Type":"multipart/form-data"}', 
        data = '{"csrf_token": "${dv_csrf_token}"}',
    )
    nodes: Set[ApiNode] = {
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, a22, a23, a24, a25
    }
    node_list: list[ApiNode] = [
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, a22, a23, a24, a25
    ]

    api_doc: Dict[bytes, ApiNode] = {
        msgspec.msgpack.encode(node): node for node in nodes
    }

    @override
    def get_nodes(self):
        return self.nodes
    
