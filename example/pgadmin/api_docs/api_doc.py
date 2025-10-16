from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.content_type import ContentType
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override

class PgAdminApiDoc(Docable):

    a0 = ApiNode(
        path = "/",
        method = HTTPMethod.GET,
    )


    a1 = ApiNode(
        path = "/authenticate/login",
        method = HTTPMethod.POST, 
        headers='{"Content-Type":"multipart/form-data"}', 
        data='{"csrf_token":"${dv_csrf_token}","email":"vulhub@example.com","password":"vulhub"}'
    )

    a2 = ApiNode(
        path="/file_manager/init",
        method=HTTPMethod.POST,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
        json='{"dialog_type":"${v_dialog_type}", "supported_types":"${v_supported_types}", "dialog_title":"${v_dialog_title}"}'
    )

    a3 = ApiNode(
        path="/file_manager/filemanager/${p_trans_id}",
        method=HTTPMethod.POST,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
        json='{"path":"${v_path}", "mode":"addfolder", "name":"${v_name}", "storage_folder":"my_storage"}',
        filter_id="add_folder"
    )

    a4 = ApiNode(
        path="/file_manager/filemanager/${p_trans_id}",
        method=HTTPMethod.POST,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
        json='{"mode":"rename", "old":"${v_old}", "new":"${v_new}", "storage_folder":"my_storage"}',
        filter_id="rename_folder"
    )

    a5 = ApiNode(
        path="/file_manager/filemanager/${p_trans_id}",
        method=HTTPMethod.POST,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
        json='{"mode":"delete", "path":"${v_path}", "storage_folder":"my_storage"}',
        filter_id="delete_folder"
    )
    a6 = ApiNode(
        path="/misc/validate_binary_path",
        method=HTTPMethod.POST,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
        json='{"utility_path":"${v_utility_path}"}'
    )


    a7 = ApiNode(
        path="/browser",
        method=HTTPMethod.GET,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
    )

    a8 = ApiNode(
        path="/preferences",
        method=HTTPMethod.GET,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
    )
    
    a9 = ApiNode(
        path="/misc/cleanup",
        method=HTTPMethod.POST,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
    )

    a10 = ApiNode(
        path="/browser/lock_layout",
        method=HTTPMethod.PUT,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
        json='{"value": "${v_value}"}'
    )

    a11 = ApiNode(
        path="/settings/layout",
        method=HTTPMethod.DELETE,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
    )

    a12 = ApiNode(
        path="/browser/server_group/obj",
        method=HTTPMethod.POST,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
        json='{"name": "${v_name}"}'
    )

    a13 = ApiNode(
        path="/browser/server_group/obj/${p_obj_id}",
        method=HTTPMethod.DELETE,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
    )

    a14 = ApiNode(
        path="/browser/server_group/obj/${p_obj_id}",
        method=HTTPMethod.PUT,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
        json='{"name": "${v_name}","id": "${v_id}"}'
    )

    a15 = ApiNode(
        path="/browser/server_group/children/${p_obj_id}",
        method=HTTPMethod.GET,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}'
    )

    a16 = ApiNode(
        path="/settings/get_tree_state",
        method=HTTPMethod.GET,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
    )


    a17 = ApiNode(
        path="/user_management/role",
        method=HTTPMethod.GET,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
    )

    a18 = ApiNode(
        path="/user_management/user/",
        method=HTTPMethod.GET,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
    )

    a19 = ApiNode(
        path="/browser/change_password",
        method=HTTPMethod.GET,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
    )

    a20 = ApiNode(
        path="/browser/change_password",
        method=HTTPMethod.POST,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
        json='{"password": "${v_old_password}", "new_password": "${v_new_password}", "new_password_confirm": "${v_confirm_password}", "csrf_token": "${v_csrf_token}"}'
    ) # maybe 500

    a21 = ApiNode(
        path="/settings/save_tree_state",
        method=HTTPMethod.POST,
        headers='{"X-pgA-CSRFToken": "${hv_X-pgA-CSRFToken}"}',
    )

    nodes: Set[ApiNode] = {
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21,
    }

    node_list: list[ApiNode] = [
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, 
    ]

    api_doc: Dict[bytes, ApiNode] = {
        msgspec.msgpack.encode(node): node for node in nodes
    }

    @override
    def get_nodes(self):
        return self.nodes