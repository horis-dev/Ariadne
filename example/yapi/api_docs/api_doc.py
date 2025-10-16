from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override

class YApiDoc(Docable):

    a0 = ApiNode(
        "/api/user/reg",
        HTTPMethod.POST,
        json='{"username":"${v_username}","email":"${v_email}","password":"${v_password}"}'
    )

    a1 = ApiNode(
        "/api/user/login",
        HTTPMethod.POST,
        json='{"email":"${v_email}","password":"${v_password}"}'
    )


    a2 = ApiNode(
        "/api/group/get_mygroup",
        HTTPMethod.GET
    )


    a3 = ApiNode(
        "/api/project/add",
        HTTPMethod.POST,
        json='{"name":"${v_name}","basepath":"${v_basepath}","group_id":"${v_group_id}","project_type":"${v_project_type}"}'
    )


    a4 = ApiNode(
        "/api/interface/list_menu",
        HTTPMethod.GET,
        params="project_id=${q_project_id}"
    )


    a5 = ApiNode(
        "/api/interface/add",
        HTTPMethod.POST,
        json='{"method":"${v_method}","path":"${v_path}","title":"${v_title}","project_id":"${v_project_id}","catid":"${v_catid}"}'
    )

    a6 = ApiNode(
        "/api/plugin/advmock/save",
        HTTPMethod.POST,
        json='{"project_id":"${v_project_id}","interface_id":"${v_interface_id}","mock_script":"${v_mock_script}","enable":"${v_enable}"}'
    )

    a7 = ApiNode(
        "/mock/${p_project_id}/${p_basepath}/${p_path}",
        HTTPMethod.GET
    )

    a8 = ApiNode(
        "/api/user/find",
        HTTPMethod.POST,
        json='{"id":"${v_id}"}'
    )


    a9 = ApiNode(
        "/api/user/update",
        HTTPMethod.POST,
        json='{"username":"${v_username}","email":"${v_email}","role":"${v_role}"}'
    )

    a10 = ApiNode(
        "/api/group/add",
        HTTPMethod.POST,
        json='{"group_name":"${v_group_name}","group_desc":"${v_group_desc}"}'
    )


    a11 = ApiNode(
        "/api/project/list",
        HTTPMethod.POST,
        json='{"group_id":"${v_group_id}"}'
    )


    a12 = ApiNode(
        "/api/project/up",
        HTTPMethod.POST,
        json='{"id":"${v_id}","name":"${v_name}","basepath":"${v_basepath}","desc":"${v_desc}"}'
    )

    a13 = ApiNode(
        "/api/project/del",
        HTTPMethod.POST,
        json='{"id":"${v_id}"}'
    )


    a14 = ApiNode(
        "/api/interface/get",
        HTTPMethod.GET,
        params="id=${q_id}"
    )


    a15 = ApiNode(
        "/api/interface/up",
        HTTPMethod.POST,
        json='{"id":"${v_id}","title":"${v_title}","path":"${v_path}","method":"${v_method}","desc":"${v_desc}"}'
    )

    a16 = ApiNode(
        "/api/interface/del",
        HTTPMethod.POST,
        json='{"id":"${v_id}"}'
    )

    a17 = ApiNode(
        "/api/interface/add_cat",
        HTTPMethod.POST,
        json='{"name":"${v_name}","project_id":"${v_project_id}","desc":"${v_desc}"}'
    )

    nodes: Set[ApiNode] = {
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17
    }

    api_doc: Dict[bytes, ApiNode] = {
        msgspec.msgpack.encode(node): node for node in nodes
    }

    @override
    def get_nodes(self):
        return self.nodes