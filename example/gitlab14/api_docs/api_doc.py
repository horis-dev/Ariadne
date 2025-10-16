from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.content_type import ContentType
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override

class Gitlab14RestApiDoc(Docable): 
    a0 = ApiNode(
        path = "/api/v4/projects",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a1 = ApiNode(
        path = "/project_aliases",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a2 = ApiNode(
        path = "/project_aliases/${p_name}",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a3 = ApiNode(
        path = "/api/v4/projects/${p_id}/fork",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
        json='{"name":"${v_name}", "path":"${v_path}"}'
    )

    a4 = ApiNode(
        path = "/api/v4/projects/${p_id}/forks",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a5 = ApiNode(
        path = "/api/v4/projects/${p_id}/fork/${p_forked_from_id}",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a6 = ApiNode(
        path = "/api/v4/projects/${p_id}/fork",
        method = HTTPMethod.DELETE,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a7 = ApiNode(
        path = "/api/v4/projects",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
        json='{"name":"${v_name}", "path":"${v_path}"}'
    ) 

    a8 = ApiNode(
        path = "/api/v4/projects/${p_id}/custom_attributes",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a9 = ApiNode(
        path = "/api/v4/projects/${p_id}",
        method = HTTPMethod.DELETE,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a10 = ApiNode(
        path = "/api/v4/users/${p_user_id}/starred_projects",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a11 = ApiNode(
        path = "/api/v4/projects/${p_id}/starrers",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a12 = ApiNode(
        path = "/api/v4/projects/${p_id}/star",
        method = HTTPMethod.POST,    
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a13 = ApiNode(
        path = "/api/v4/projects/${p_id}/unstar",
        method = HTTPMethod.POST,    
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a14 = ApiNode(
        path = "/api/v4/projects/${p_id}/statistics",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a15 = ApiNode(
        path = "/api/v4/projects/${p_id}/milestones",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )
    
    a16 = ApiNode(
        path = "/api/v4/projects/${p_id}/milestones/${p_milestone_id}",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a17 = ApiNode(
        path = "/api/v4/projects/${p_id}/milestones",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
        json='{"title":"${v_title}"}'
    )

    a18 = ApiNode(
        path = "/api/v4/projects/${p_id}/milestones/${p_milestone_id}",
        method = HTTPMethod.PUT,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
        json='{"title":"${v_title}"}'
    )

    a19 = ApiNode(
        path = "/api/v4/projects/${p_id}/milestones/${p_milestone_id}",
        method = HTTPMethod.DELETE,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a20 = ApiNode(
        path = "/api/v4/projects/${p_id}/milestones/${p_milestone_id}/issues",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a21 = ApiNode(
        path = "/api/v4/projects/${p_id}/milestones/${p_milestone_id}/merge_requests",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a22 = ApiNode(
        path = "/api/v4/projects/${p_id}/boards",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a23 = ApiNode(
        path = "/api/v4/projects/${p_id}/boards/${p_board_id}",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a24 = ApiNode(
        path = "/api/v4/projects/${p_id}/boards",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
        json='{"name":"${v_name}"}'
    )

    a25 = ApiNode(
        path = "/api/v4/projects/${p_id}/boards/${p_board_id}",
        method = HTTPMethod.DELETE,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )


    a26 = ApiNode(
        path = "/api/v4/projects/${p_id}/labels",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a27 = ApiNode(
        path = "/api/v4/projects/${p_id}/labels/${p_label_id}",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a28 = ApiNode(
        path = "/api/v4/projects/${p_id}/labels",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
        json='{"name":"${v_name}", "color":"#5843AD"}'
    )

    a29 = ApiNode(
        path = "/api/v4/projects/${p_id}/labels/${p_label_id}",
        method = HTTPMethod.DELETE,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a30 = ApiNode(
        path = "/api/v4/projects/${p_id}/labels/${p_label_id}/subscribe",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )

    a31 = ApiNode(
        path = "/api/v4/projects/${p_id}/labels/${p_label_id}/unsubscribe",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Bearer z5DDDf8efs7dH_62qTfi"}',
    )
    
    nodes: Set[ApiNode] = {
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, a22, a23, a24, a25, a26, a27, a28, a29, a30, a31
    }

    node_list: list[ApiNode] = [
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, a22, a23, a24, a25, a26, a27, a28, a29, a30, a31
    ]

    api_doc: Dict[bytes, ApiNode] = {
        msgspec.msgpack.encode(node): node for node in nodes
    }

    @override
    def get_nodes(self):
        return self.nodes