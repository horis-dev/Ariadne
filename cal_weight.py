"""
利用二分图最大权匹配，实现距离的计算，并完成种子库的选择。

二分图中：
顶点U：目标状态
顶点V：这个种子执行完之后，能够达到的状态
状态：数据库行的值
边的权重：数据库行之间的相似度

计算流程：
计算字段的相似度 → 加权得到行的相似度，也就是边的权重 → 计算二分图最大权匹配值
"""

import math
import difflib
import networkx as nx
from networkx import edges
from basic.server_state import ServerState
from loguru import logger


# 字段相似度计算
def column_similarity(left_column, right_column):

    def sim_varchar(left_column, right_column):
        """
        Jaccard相似度+归一化，值越大相似度越大
        """
        # 将字符串转换为字符集合
        # set_a = set(left_column)
        # set_b = set(right_column)
        #
        # # 计算交集和并集的大小
        # intersection = set_a.intersection(set_b)
        # union = set_a.union(set_b)
        #
        # # 计算 Jaccard 相似度的 x = |A ∩ B| / |A ∪ B|
        # x = len(intersection) / len(union) if len(union) > 0 else 0  # 防止除以零
        #
        # # 计算 S_varchar = e^-x
        # S_varchar = math.exp(-x)
        #
        # return S_varchar

        """
        Levenshtein 距离的归一化
        """
        return difflib.SequenceMatcher(None, left_column, right_column).ratio()

    def sim_num(left_column, right_column, scale: float = 1.0):
        # 计算 |a - b|
        # difference = abs(left_column-right_column)
        #
        # # 计算 S_int = 1 / sqrt(|a - b|)
        # if difference == 0:
        #     return float('inf')  # 防止除以零，返回无穷大
        # S_int = 1 / (1+math.sqrt(difference))
        #
        # return S_int

        diff = abs(left_column - right_column)
        return max(0.0, 1.0 - diff / scale)

    def sim_enum(left_column, right_column):
        if left_column == right_column:
            return 1
        else:
            return 0

    # 判断字段类型
    if isinstance(left_column, str) and isinstance(right_column, str):
        return sim_varchar(left_column, right_column)
    elif isinstance(left_column, (int, float)) and isinstance(
        right_column, (int, float)
    ):
        return sim_num(left_column, right_column)
    else:
        return 0


# 行相似度计算
def node_similarity(left_node, right_node):
    """
    :param left_node: 更新的多个行中的某一行
    :param right_node:目标状态的多个行中的某一行
    :return:两个行的相似度值
    """
    sum = 0
    # 行的长度不相等，相似度返回0
    if len(left_node) != len(right_node):
        return 0
    for i in range(len(left_node)):
        sim = column_similarity(left_node[i], right_node[i])
        # print(f'''{left_node[i]} {right_node[i]} → {sim}''')
        sum += sim
    return sum / len(left_node)  # 每条边的权重进行归一化


# 二分图最大权匹配
def calculate_distance(current_state: ServerState, depended_state: ServerState):
    """
    :param left_nodes: 种子执行完的状态，包含执行后更新了的多个行
    :param right_nodes: 目标状态，包含最终读取的多个行
    :return:二分图最大权匹配值
    """

    left_nodes, right_nodes = [], []

    for tbl in current_state.db_state:
        for row in tbl.rows:
            left_nodes.append(("L",tuple(row)))
    #logger.debug(left_nodes)
    for tbl in depended_state.db_state:
        for row in tbl.rows:
            right_nodes.append(("R",tuple(row)))
    #logger.debug(right_nodes)
    # 创建一个无向加权二分图
    G = nx.Graph()

    # 添加左侧节点到图中
    G.add_nodes_from(left_nodes, bipartite=0)  # bipartite=0 表示是左侧节点

    # 添加右侧节点到图中
    G.add_nodes_from(right_nodes, bipartite=1)  # bipartite=1 表示是右侧节点

    edges = []
    for left_node in left_nodes:
        for right_node in right_nodes:
            weight = node_similarity(left_node[1], right_node[1])
            edge = (left_node, right_node, {"weight": weight})
            edges.append(edge)

    G.add_edges_from(edges)

    # 执行带权二分图匹配
    matching = nx.max_weight_matching(G, weight="weight")
    max_weight = sum(G[u][v]["weight"] for u, v in matching)

    unmatched_right = len(right_nodes) - len(matching) # 22-10=12
    unmatch_loss = 1.0
    db_score = max_weight - unmatched_right * unmatch_loss
    """
    logger.info("=== 匹配后权重表 ===")
    total_weight = 0
    for u, v in matching:
        weight = G[u][v]['weight']
        logger.info(f"匹配: {u} <-> {v}，权重: {weight}")
        total_weight += weight
    logger.info(f"总权重: {total_weight}")
    logger.info(f"总配对数: {len(matching)}")
    """

    # 输出匹配结果
    # logger.debug(f"二分图匹配得分：{max_weight}，惩罚得分：{unmatched_right * unmatch_loss}，总得分：{total_weight}")
    
    # === file_state 部分 ===
    # 参数，按需调节
    FILE_EXACT_MATCH_SCORE = 1.0
    DIR_EXISTENCE_SCORE    = 0.2

    # 索引：按 (path, name) 分组
    curr_map = {}
    for f in current_state.file_state:
        key = (f.file_path, f.file_name)
        curr_map.setdefault(key, []).append(f)

    dep_map = {}
    for f in depended_state.file_state:
        key = (f.file_path, f.file_name)
        dep_map.setdefault(key, []).append(f)

    file_score = 0.0

    # 1. 精确匹配：路径+名称+内容完全相同
    matched_dep_keys = set()
    for key, curr_list in curr_map.items():
        dep_list = dep_map.get(key, [])
        for cf in curr_list:
            for df in dep_list:
                if cf.file_content == df.file_content:
                    file_score += FILE_EXACT_MATCH_SCORE
                    matched_dep_keys.add(key)
                    break  # 每个 curr_file 只算一次 exact match

    # 2. 同目录存在性匹配：同目录下有文件但内容不匹配，也要给次高分
    #    （不重复计算已经 exact match 的 key）
    #    以文件路径（目录）为单位
    dirs_with_dep = set(f.file_path for f in depended_state.file_state)
    for key in curr_map:
        dirpath, _ = key
        if dirpath in dirs_with_dep and key not in matched_dep_keys:
            file_score += DIR_EXISTENCE_SCORE
            # 标记，防止同目录重复加分
            dirs_with_dep.remove(dirpath)

    # 最终得分
    total_score = db_score + file_score
    logger.debug(f"DB_State_Score: {db_score}, File_State_Score:{file_score}")
    return total_score 

def calculate_distance_NoDist(current_state: ServerState, depended_state: ServerState):
    """
    移除了基于二分图匹配的状态距离度量，在种子评估时仅依赖传统的代码覆盖率和响应值域扩展作为反馈。
    """
    return 0.0

