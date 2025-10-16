from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override
from basic.http.content_type import ContentType


class ActiveMQApiDoc(Docable):

    a0 = ApiNode(
        path = "/fileserver/${p_filename}",
        method = HTTPMethod.PUT,
        headers = '{"Content-Type": "application/octet-stream"}',
    )

    a1 = ApiNode(
        path = "/api",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a2 = ApiNode(
        path = "/",
        method = HTTPMethod.GET,
    )

    a3 = ApiNode(
        path = "/fileserver",
        method = HTTPMethod.GET,
    )

    a4 = ApiNode(
        path = "/fileserver/${p_filename}",
        method = HTTPMethod.MOVE,
        headers='{"Destination": "${hv_Destination}"}',
    )

    a5 = ApiNode(
        path = "/admin",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )


    a6 = ApiNode(
        path = "/admin/test",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a7 = ApiNode(
        path = "/admin/test/systemProperties.jsp",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a8 = ApiNode(
        path = "/admin/queues.jsp",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a9 = ApiNode(
        path = "/admin/topics.jsp",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a10 = ApiNode(
        path = "/admin/createDestination.action",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4=", "Content-Type":"multipart/form-data"}',
        data = '{"JMSDestinationType": "queue", "secret": "${dv_secret}", "JMSDestination": "${dv_JMSDestination}"}',
        filter_id = "create_queue",
    )

    a11 = ApiNode(
        path = "/admin/createDestination.action",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4=", "Content-Type":"multipart/form-data"}',
        data = '{"JMSDestinationType": "topic", "secret": "${dv_secret}", "JMSDestination": "${dv_JMSDestination}"}',
        filter_id = "create_topic",
    )

    a12 = ApiNode(
        path = "/admin/deleteDestination.action",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
        params = "JMSDestination=${q_JMSDestination}&JMSDestinationType=queue&secret=${q_secret}",
        filter_id = "delete_queue",
    )

    a13 = ApiNode(
        path = "/admin/deleteDestination.action",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
        params = "JMSDestination=${q_JMSDestination}&JMSDestinationType=topic&secret=${q_secret}",
        filter_id = "delete_topic",
    )

    a14 = ApiNode(
        path = "/admin/xml",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a15 = ApiNode(
        path = "/admin/queueGraph.jsp",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a16 = ApiNode(
        path = "/admin/subscribers.jsp",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a17 = ApiNode(
        path = "/admin/createSubscriber.action",
        method = HTTPMethod.POST,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4=", "Content-Type":"multipart/form-data"}',
        data = '{"JMSDestinationType": "topic", "secret": "${dv_secret}", "clientId": "${dv_clientId}", "subscriberName": "${dv_subscriberName}", "JMSDestination": "${dv_JMSDestination}","selector": "${dv_selector}"}',
    ) # csrf aaa bbb xxx xxx

    a18 = ApiNode(
        path = "/admin/deleteSubscriber.action",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
        params = "clientId=${q_clientId}&subscriberName=${q_subscriberName}&secret=${q_secret}",
    ) # aaa bbb csrf

    a19 = ApiNode(
        path = "/admin/connections.jsp",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a20 = ApiNode(
        path = "/admin/network.jsp",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a21 = ApiNode(
        path = "/admin/scheduled.jsp",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )

    a22 = ApiNode(
        path = "/admin/send.jsp",
        method = HTTPMethod.GET,
        headers = '{"Authorization": "Basic YWRtaW46YWRtaW4="}',
    )


    nodes: Set[ApiNode] = {
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, a22
    }

    node_list: list[ApiNode] = [
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, a22
    ]

    api_doc: Dict[bytes, ApiNode] = {
        msgspec.msgpack.encode(node): node for node in nodes
    }

    @override
    def get_nodes(self):
        return self.nodes