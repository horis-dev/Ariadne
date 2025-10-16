from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.content_type import ContentType
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override

class GitlabApiDoc(Docable):
    a0 = ApiNode(
        path = "/users/sign_in",
        method = HTTPMethod.GET,
    )

    a1 = ApiNode(
        path = "/users",
        method = HTTPMethod.POST, 
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"authenticity_token":"${dv_authenticity_token}", "new_user[name]":"${dv_new_user[name]}", "new_user[username]":"${dv_new_user[username]}", "new_user[email]":"${dv_new_user[email]}", "new_user[password]":"${dv_new_user[password]}"}'
    )

    a2 = ApiNode(
        path="/projects/new",
        method=HTTPMethod.GET,
    )

    a3 = ApiNode(
        path="/import/gitlab_project",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"authenticity_token":"${dv_authenticity_token}", "namespace_id":"${dv_namespace_id}", "path":"${dv_path}"}',
        files = '{"file": "${fv_file}"}',
    )

    a4 = ApiNode(
        path="/${p_user_name}/${p_project_name}/import/new",
        method=HTTPMethod.GET,
    )

    a5 = ApiNode(
        path="/${p_user_name}/${p_project_name}",
        method=HTTPMethod.GET,
    )

    a6 = ApiNode(
        path="/dashboard/projects",
        method=HTTPMethod.GET,
    )

    a7 = ApiNode(
        path="/import/gitlab_project/new",
        params="namespace_id=${q_namespace_id}&path=${q_path}",
        method=HTTPMethod.GET,
    )

    a8 = ApiNode(
        path="/groups/new",
        method=HTTPMethod.GET,
    )

    a9 = ApiNode(
        path="/groups",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"utf8":"✓", "authenticity_token":"${dv_authenticity_token}", "group[path]":"${dv_group[path]}", "group[description]":"${dv_group[description]}", "group[visibility_level]":"${dv_group[visibility_level]}"}',
    ) # token name 123123 0

    a10 = ApiNode(
        path="/${p_group_name}",
        method=HTTPMethod.GET,
    )

    a11 = ApiNode(
        path="/groups/${p_group_name}/edit",
        method=HTTPMethod.GET,
    )

    a12 = ApiNode(
        path="/${p_group_name}",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"_method":"delete", "authenticity_token":"${dv_authenticity_token}"}',
    )

    a13 = ApiNode(
        path="/${p_user_name}/${p_project_name}/toggle_star",
        method=HTTPMethod.POST,
        headers='{"X-CSRF-Token": "${hv_X-CSRF-Token}"}',
    )

    a14 = ApiNode(
        path="/profile/emails",
        method=HTTPMethod.GET,
    )
    a15 = ApiNode(
        path="/profile/emails",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"utf8":"✓", "authenticity_token":"${dv_authenticity_token}", "email[email]":"${dv_email[email]}"}',
    )

    a16 = ApiNode(
        path="/help",
        method=HTTPMethod.GET,
    )

    a17 = ApiNode(
        path="/${p_user_name}/${p_project_name}/issues/new",
        method=HTTPMethod.GET,
    )

    a18 = ApiNode(
        path="/${p_user_name}/${p_project_name}/issues",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"utf8":"✓", "authenticity_token":"${dv_authenticity_token}", "issue[title]":"${dv_issue[title]}", "issue[description]":"", "issue[confidential]":"0", "issue[label_ids][]":"", "issue[due_date]":"", "issue[due_date]":"", "issue[lock_version]":"0"}',
    )

    a19 = ApiNode(
        path="/${p_user_name}/${p_project_name}",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"_method":"delete", "authenticity_token":"${dv_authenticity_token}"}',
    )

    a20 = ApiNode(
        path="/${p_user_name}/${p_project_name}/activity",
        method=HTTPMethod.GET,
    )
    a21 = ApiNode(
        path="/${p_user_name}/${p_project_name}/pipelines",
        method=HTTPMethod.GET,
    )

    a22 = ApiNode(
        path="/${p_user_name}/${p_project_name}/issues",
        method=HTTPMethod.GET,
    )

    a23 = ApiNode(
        path="/${p_user_name}/${p_project_name}/merge_requests",
        method=HTTPMethod.GET,
    )

    a24 = ApiNode(
        path="/${p_user_name}/${p_project_name}/wikis/home",
        method=HTTPMethod.GET,
    )

    a25 = ApiNode(
        path="/${p_user_name}/${p_project_name}/snippets",
        method=HTTPMethod.GET,
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