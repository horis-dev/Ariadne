from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.content_type import ContentType
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override

class AppwriteApiDoc(Docable):

    # Database operations:
    # - Reads: identities (check email uniqueness)
    # - Writes: users (create user document), targets (create target document)
    a0 = ApiNode(
        path = "/v1/account",
        method = HTTPMethod.POST,
        json = '{"userId":"unique()","email":"${v_email}","password":"${v_password}","name":"${v_name}"}',
    )

    # Database operations:
    # - Reads: users (verify user credentials)
    # - Writes: users (update password hash, clear cache), sessions (create session document)
    a1 = ApiNode(
        path = "/v1/account/sessions",
        method = HTTPMethod.POST,
        json = '{"email":"${v_email}","password":"${v_password}"}',
    )

    # Database operations:
    # - Reads: teams (for ID generation and checks)
    # - Writes: teams (create team document), memberships (create membership document)
    a2 = ApiNode(
        path = "/v1/teams",
        method = HTTPMethod.POST,
        json = '{"teamId":"unique()","name":"${v_name}"}',
    )

    # Database operations:
    # - Reads: teams (verify team ID)
    # - Writes: projects (create project document)
    a3 = ApiNode(
        path = "/v1/projects",
        method = HTTPMethod.POST,
        json = '{"projectId":"unique()","name":"${v_name}","teamId":"${v_teamId}","region":"default"}',
    )

    # Database operations:
    # - Reads: users (check user uniqueness)
    # - Writes: users (create user document), targets (create target document)
    a4 = ApiNode(
        path = "/v1/users",
        method = HTTPMethod.POST,
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        json = '{"userId":"unique()","email":"${v_email}","password":"${v_password}","name":"${v_name}","role":"owner"}',
    )

    # Database operations:
    # - Reads: users (get user document)
    a5 = ApiNode(
        path = "/v1/account",
        method = HTTPMethod.GET,
    )

    # Database operations: None (static page)
    a6 = ApiNode(
        path = "/console",
        method = HTTPMethod.GET,
    )

    # Database operations: None (authentication page)
    a7 = ApiNode(
        path = "/auth/signin",
        method = HTTPMethod.GET,
    )
    
    # Database operations:
    # - Reads: projects (list projects)
    a8 = ApiNode(
        path = "/v1/projects",
        method = HTTPMethod.GET,
    )

    # Database operations:
    # - Reads: functions (list functions)
    a9 = ApiNode(
        path = "/v1/functions",
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        method = HTTPMethod.GET,
    )

    # Database operations:
    # - Reads: functions (get function document)
    a10 = ApiNode(
        path = "/v1/functions/${p_functionId}",
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        method = HTTPMethod.GET,
    )

    # Database operations:
    # - Writes: functions (create function document)
    a11 = ApiNode(
        path = "/v1/functions",
        method = HTTPMethod.POST,
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        json = '{"functionId":"unique()","name":"${v_name}","execute":"","runtime":"node-16.0"}',
        filter_id = "func_node",
    )

    # Database operations:
    # - Writes: functions (create function document)
    a12 = ApiNode(
        path = "/v1/functions",
        method = HTTPMethod.POST,
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        json = '{"functionId":"unique()","name":"${v_name}","execute":"","runtime":"php-8.0"}',
        filter_id = "func_php",
    )

    # Database operations:
    # - Writes: functions (create function document)
    a13 = ApiNode(
        path = "/v1/functions",
        method = HTTPMethod.POST,
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        json = '{"functionId":"unique()","name":"${v_name}","execute":"","runtime":"ruby-3.0"}',
        filter_id = "func_ruby",
    )

    # Database operations:
    # - Writes: functions (create function document)
    a14 = ApiNode(
        path = "/v1/functions",
        method = HTTPMethod.POST,
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        json = '{"functionId":"unique()","name":"${v_name}","execute":"","runtime":"python-3.9"}',
        filter_id = "func_python",
    )

    # Database operations:
    # - Writes: functions (delete function document)
    a15= ApiNode(
        path = "/v1/functions/${p_functionId}",
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        method = HTTPMethod.DELETE,
    )

    # Database operations:
    # - Reads: projects (get project document)
    a16 = ApiNode(
        path = "/v1/projects/${p_projectId}",
        method = HTTPMethod.GET,
    )

    # Database operations:
    # - Reads: keys (list API keys)
    a17 = ApiNode(
        path = "/v1/projects/${p_projectId}/keys",
        method = HTTPMethod.GET,
    )

    # Database operations:
    # - Writes: projects (delete project document)
    a18 = ApiNode(
        path = "/v1/projects/${p_projectId}",
        method = HTTPMethod.DELETE,
        json = '{"password":"${v_password}"}',
    )

    # Database operations:
    # - Reads: users (list users)
    a19 = ApiNode(
        path = "/v1/users",
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        method = HTTPMethod.GET,
    )

    # Database operations:
    # - Reads: users (get user document)
    a20 = ApiNode(
        path = "/v1/users/${p_userId}",
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        method = HTTPMethod.GET,
    )

    # Database operations:
    # - Reads: users (get user document)
    # - Writes: users (update user name)
    a21 = ApiNode(
        path = "/v1/users/${p_userId}/name",
        method = HTTPMethod.PATCH,
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        json = '{"name":"${v_name}"}',
    )
    
    # Database operations:
    # - Reads: users (get user document)
    # - Writes: users (update user email)
    a22 = ApiNode(
        path = "/v1/users/${p_userId}/email",
        method = HTTPMethod.PATCH,
        headers='{"x-appwrite-project": "${hv_x-appwrite-project}", "x-appwrite-mode": "admin"}',
        json = '{"email":"${v_email}"}',
    )

    # Database operations:
    # - Reads: projects (get project document)
    # - Writes: projects (update service status)
    a23 = ApiNode(
        path = "/v1/projects/${p_projectId}/service",
        method = HTTPMethod.PATCH,
        json = '{"service":"account","status":"${v_status}"}',
        filter_id="service_account",
    )

    # Database operations:
    # - Reads: projects (get project document)
    # - Writes: projects (update service status)
    a24 = ApiNode(
        path = "/v1/projects/${p_projectId}/service",
        method = HTTPMethod.PATCH,
        json = '{"service":"avatars","status":"${v_status}"}',
        filter_id="service_avatars",
    )

    # Database operations:
    # - Reads: projects (get project document)
    # - Writes: projects (update service status)
    a25 = ApiNode(
        path = "/v1/projects/${p_projectId}/service",
        method = HTTPMethod.PATCH,
        json = '{"service":"database","status":"${v_status}"}',
        filter_id="service_database",
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
