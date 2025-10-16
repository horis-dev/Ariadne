from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override


class ElasticsearchApiDoc(Docable):
    # 创建文档 - 向索引中添加新文档
    a0 = ApiNode(
        path="/${p_index}/${p_type}/",
        method=HTTPMethod.POST,
        json='{"name": "${v_name}"}',
    )

    # 获取文档 - 根据ID获取特定文档
    a1 = ApiNode(
        path="/${p_index}/${p_type}/${p_id}",
        method=HTTPMethod.GET,
    )

    # 删除文档 - 删除特定文档
    a3 = ApiNode(
        path="/${p_index}/${p_type}/${p_id}",
        method=HTTPMethod.DELETE,
    )

    # 创建索引 - 创建新的索引配置
    a4 = ApiNode(
        path="/${p_index}",
        method=HTTPMethod.PUT,
        json='{"settings": {"number_of_shards": ${v_shards}, "number_of_replicas": ${v_replicas}}, "mappings": {"properties": {"name": {"type": "string"}, "status": {"type": "string"}}}}',
    )

    # 更新文档 - 更新特定文档
    a5 = ApiNode(
        path="/${p_index}/${p_type}/${p_id}/_update",
        method=HTTPMethod.POST,
        json='{"doc": {"name": "${v_name}", "status": "${v_status}"}}',
    )

    # 搜索文档 - 在索引中搜索
    a6 = ApiNode(
        path="/${p_index}/_search",
        method=HTTPMethod.POST,
        json='{"query": {"match": {"name": "${v_value}"}}}',
    )

    # 删除索引 - 删除整个索引
    a7 = ApiNode(
        path="/${p_index}",
        method=HTTPMethod.DELETE,
    )

    # 获取索引信息 - 获取索引的设置和映射
    a8 = ApiNode(
        path="/${p_index}",
        method=HTTPMethod.GET,
    )

    # 批量操作 - 执行多个索引/更新/删除操作
    a9 = ApiNode(
        path="/_bulk",
        method=HTTPMethod.POST,
        json='{"index": {"_index": "${p_index}", "_type": "${p_type}", "_id": "${p_id}"}}\n{"name": "${v_name}"}\n',
    )

    # 多重搜索 - 执行多个搜索请求
    a10 = ApiNode(
        path="/_msearch",
        method=HTTPMethod.POST,
        json='{"index": "${p_index}"}\n{"query": {"match_all": {}}}\n',
    )

    # 获取映射 - 获取索引的字段映射
    a11 = ApiNode(
        path="/${p_index}/_mapping",
        method=HTTPMethod.GET,
    )

    # 更新映射 - 更新索引的字段映射
    a12 = ApiNode(
        path="/${p_index}/_mapping/${p_type}",
        method=HTTPMethod.PUT,
        json='{"properties": {"name": {"type": "${v_type}"}, "status": {"type": "${v_field_type}"}}}',
    )

    # 刷新索引 - 刷新索引使更改可见
    a13 = ApiNode(
        path="/${p_index}/_refresh",
        method=HTTPMethod.POST,
    )

    # 强制合并 - 强制合并索引段
    a14 = ApiNode(
        path="/${p_index}/_forcemerge",
        method=HTTPMethod.POST,
    )

    # 获取集群健康状态
    a15 = ApiNode(
        path="/_cluster/health",
        method=HTTPMethod.GET,
    )

    # 获取集群状态
    a16 = ApiNode(
        path="/_cluster/state",
        method=HTTPMethod.GET,
    )

    # 获取节点信息
    a17 = ApiNode(
        path="/_nodes",
        method=HTTPMethod.GET,
    )

    # 获取索引统计信息
    a18 = ApiNode(
        path="/${p_index}/_stats",
        method=HTTPMethod.GET,
    )

    # 创建别名 - 为索引创建别名
    a19 = ApiNode(
        path="/_aliases",
        method=HTTPMethod.POST,
        json='{"actions": [{"add": {"index": "${p_index}", "alias": "${v_alias}"}}]}',
    )

    nodes: Set[ApiNode] = {
        a0,
        a1,
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
    }
    api_doc: Dict[bytes, ApiNode] = {
        msgspec.msgpack.encode(node): node for node in nodes
    }

    @override
    def get_nodes(self):
        return self.nodes