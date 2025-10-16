from typing import Set

from api.api_node import ApiNode
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override


class SolrApiDoc(Docable):

    a0 = ApiNode(
        "/api/cores",
        HTTPMethod.GET,
    )

    a1 = ApiNode("/api/cores/${p_core}", HTTPMethod.GET)

    a2 = ApiNode(
        path="/api/cores",
        method=HTTPMethod.POST,
        json='{"create": {"name": "${v_name}", "instanceDir": "${v_instanceDir}", "config": "${v_config}", "schema": "${v_schema}", "dataDir": "${v_dataDir}", "configSet": "${v_configSet}"}}',
    )

    a3 = ApiNode("/api/cores/${p_core}/reload", HTTPMethod.POST)

    a4 = ApiNode(
        path="/api/cores/${p_core}/unload",
        method=HTTPMethod.POST,
        json='{"deleteIndex": "${v_deleteIndex}", "deleteDataDir": "${v_deleteDataDir}", "deleteInstanceDir": "${v_deleteInstanceDir}"}',
    )

    a5 = ApiNode(
        "/api/cores/${p_core}/rename",
        HTTPMethod.POST,
        json='{"other": "${v_other}"}',
    )

    a6 = ApiNode("/api/cores/${p_core}/config", HTTPMethod.GET)

    a7 = ApiNode(
        path="/api/cores/${p_core}/config",
        method=HTTPMethod.POST,
        json='{"update-queryresponsewriter": {"startup": "${v_startup}", "name": "${v_name}", "class": "${v_class}", "template.base.dir": "${v_template.base.dir}", "solr.resource.loader.enabled": "${v_solr.resource.loader.enabled}", "params.resource.loader.enabled": "${v_params.resource.loader.enabled}"}}',
    )

    a8 = ApiNode(
        path="/api/cores/${p_core}/select",
        method=HTTPMethod.POST,
        params="q=${q_q}&wt=${q_wt}&v.template=${q_template}&v.template.custom=${q_template.custom}",
    )

    a9 = ApiNode(
        path="/api/cores/${p_core}/update/docs",
        method=HTTPMethod.POST,
        json='{"add-requesthandler": {"name": "${v_name}", "class": "${v_class}", "defaults": ${v_defaults}}}',
    )

    a10 = ApiNode("/api/cores/${p_core}/schema", HTTPMethod.GET)

    a11 = ApiNode(
        path="/api/cores/${p_core}/schema",
        method=HTTPMethod.POST,
        json='{"add-field": {"name": "${v_field_name}", "type": "${v_field_type}", "stored": "${v_stored}", "indexed": "${v_indexed}"}}',
    )

    a12 = ApiNode("/api/cores/${p_core}/update", HTTPMethod.POST, json='{"commit": {}}')

    a13 = ApiNode(
        path="/api/cores/${p_core}/update",
        method=HTTPMethod.POST,
        json='{"delete": {"query": "${v_delete_query}"}}',
    )

    a14 = ApiNode("/solr/admin/info/system", HTTPMethod.GET)

    a15 = ApiNode("/solr/${p_core}/admin/ping", HTTPMethod.GET)

    a16 = ApiNode("/solr/${p_core}/admin/luke", HTTPMethod.GET)

    a17 = ApiNode("/solr/${p_core}/admin/system", HTTPMethod.GET)

    a18 = ApiNode("/solr/${p_core}/admin/threads", HTTPMethod.GET)

    a19 = ApiNode("/solr/${p_core}/admin/properties", HTTPMethod.GET)

    a20 = ApiNode("/solr/${p_core}/admin/plugins", HTTPMethod.GET)

    nodes: Set[ApiNode] = {
        a0,
        a1,
        a2,
        a3,
        a4,
        a5,
        a6,
        a7,
        a8,
        a9,
        a10,
        a11,
        a12,
        a13,
        a14,
        a15,
        a16,
        a17,
        a18,
        a19,
        a20,
    }

    @override
    def get_nodes(self):
        return self.nodes
