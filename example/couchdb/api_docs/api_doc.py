from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.content_type import ContentType
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override

class CouchDBApiDoc(Docable):

    a0 = ApiNode(
        "/",
        HTTPMethod.GET,
    )


    a1 = ApiNode(
        "/_config",
        HTTPMethod.GET, 
    )


    a2 = ApiNode(
        path="/_config/query_servers/${p_name}",
        method=HTTPMethod.PUT,
        headers=f'{{"Content-Type":"{ContentType.APPLICATION_X_WWW_FORM_URLENCODED.value}"}}'      
    )


    a3 = ApiNode(
        "/${p_db}",
        HTTPMethod.PUT
    )


    a4 = ApiNode(
        "/${p_db}",
        HTTPMethod.DELETE
    )

    a5 = ApiNode(
        "/${p_db}",
        HTTPMethod.GET
    )


    a6 = ApiNode(
        "/${p_db}/${p_docid}",
        HTTPMethod.PUT,
        json='{"_id":"${v_id}"}'
    )


    a7 = ApiNode(
        "/${p_db}/${p_docid}",
        HTTPMethod.DELETE
    )


    a8 = ApiNode(
        "/${p_db}/${p_docid}",
        HTTPMethod.GET
    )

    a9 = ApiNode(
        "/_session",
        HTTPMethod.POST,
        json='{"name":"${v_name}","password":"${v_password}"}'
    )


    a11 = ApiNode(
        "/_session",
        HTTPMethod.GET
    )

    a12 = ApiNode(
        "/_all_dbs",
        HTTPMethod.GET
    )


    a13 = ApiNode(
        "/${p_db}/_all_docs",
        HTTPMethod.GET
    )


    a14 = ApiNode(
        "/${p_db}/_bulk_docs",
        HTTPMethod.POST,
        json='{"docs":[{"_id":"${v_id}","data":"${v_data}"}]}'
    )


    a16 = ApiNode(
        "/${p_db}/_design/${p_designdoc}/_view/${p_viewname}",
        HTTPMethod.GET
    )


    a17 = ApiNode(
        "/_stats",
        HTTPMethod.GET
    )


    a18 = ApiNode(
        "/${p_db}/_compact",
        HTTPMethod.POST
    )


    a19 = ApiNode(
        "/_uuids",
        HTTPMethod.GET
    )


    a20 = ApiNode(
        "/_active_tasks",
        HTTPMethod.GET
    )

    nodes: Set[ApiNode] = {
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a11, a12, a13, a14, a16, a17, a18, a19, a20
    }

    api_doc: Dict[bytes, ApiNode] = {
        msgspec.msgpack.encode(node): node for node in nodes
    }

    @override
    def get_nodes(self):
        return self.nodes