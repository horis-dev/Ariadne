from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override


class SpringCloudGatewayApiDoc(Docable):
    a0 = ApiNode(
        "/actuator/health",
        HTTPMethod.GET,
    )

    a1 = ApiNode(
        "/actuator/gateway/routes",
        HTTPMethod.GET,
    )

    a2 = ApiNode(
        "/actuator/gateway/routes/${p_route_id}",
        HTTPMethod.GET,
    )

    a3 = ApiNode(
        path="/actuator/gateway/routes/${p_route_id}",
        method=HTTPMethod.POST,
        json='{"id":"${v_id}","uri":"${v_uri}","filters":[{"name":"${v_name}","args":{"name":"${v_args_name}","value":"${v_value}"}}]}',
    )

    a4 = ApiNode("/actuator/gateway/routes/${p_route_id}", HTTPMethod.DELETE)

    a5 = ApiNode("/actuator/gateway/globalfilters", HTTPMethod.GET)

    a6 = ApiNode("/actuator/gateway/routefilters", HTTPMethod.GET)

    a7 = ApiNode("/actuator/gateway/refresh", HTTPMethod.POST)

    a8 = ApiNode("/actuator/metrics", HTTPMethod.GET)

    a9 = ApiNode("/actuator/metrics/${p_metric_name}", HTTPMethod.GET)

    a10 = ApiNode("/actuator/configprops", HTTPMethod.GET)

    a11 = ApiNode("/actuator/env", HTTPMethod.GET)

    a12 = ApiNode("/actuator/env/${p_property_name}", HTTPMethod.GET)

    a15 = ApiNode("/actuator/info", HTTPMethod.GET)

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
        a15,
    }

    api_doc: Dict[bytes, ApiNode] = {
        msgspec.msgpack.encode(node): node for node in nodes
    }

    @override
    def get_nodes(self):
        return self.nodes
