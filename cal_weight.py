"""
Use maximum weight matching on a bipartite graph to compute distance and complete seed selection.

In the bipartite graph:
U vertices: target state
V vertices: the state achievable after executing this seed
State: values of database rows
Edge weight: similarity between database rows

Workflow:
compute field similarity → weight to get row similarity (i.e., edge weight) → compute maximum weight matching value
"""

import math
import difflib
import networkx as nx
from networkx import edges
from basic.server_state import ServerState
from loguru import logger


# Field similarity calculation
def column_similarity(left_column, right_column):

    def sim_varchar(left_column, right_column):
        """
        Normalized Levenshtein distance (via difflib). Larger means more similar.
        """
        # Convert strings to character sets (Jaccard idea was here, now replaced by ratio)
        return difflib.SequenceMatcher(None, left_column, right_column).ratio()

    def sim_num(left_column, right_column, scale: float = 1.0):
        # Normalize |a - b| into [0,1]
        diff = abs(left_column - right_column)
        return max(0.0, 1.0 - diff / scale)

    def sim_enum(left_column, right_column):
        return 1 if left_column == right_column else 0

    # Determine field type
    if isinstance(left_column, str) and isinstance(right_column, str):
        return sim_varchar(left_column, right_column)
    elif isinstance(left_column, (int, float)) and isinstance(
        right_column, (int, float)
    ):
        return sim_num(left_column, right_column)
    else:
        return 0


# Row similarity calculation
def node_similarity(left_node, right_node):
    """
    :param left_node: one row among the multiple rows updated by the seed
    :param right_node: one row among the multiple rows in the target state
    :return: similarity score between two rows
    """
    total = 0
    # If row lengths differ, similarity is 0
    if len(left_node) != len(right_node):
        return 0
    for i in range(len(left_node)):
        sim = column_similarity(left_node[i], right_node[i])
        # print(f'''{left_node[i]} {right_node[i]} → {sim}''')
        total += sim
    return total / len(left_node)  # normalize each edge's weight


# Maximum-weight matching on a bipartite graph
def calculate_distance(current_state: ServerState, depended_state: ServerState):
    """
    :param current_state: state after executing the seed, containing multiple updated rows
    :param depended_state: target state, containing multiple rows finally read
    :return: maximum weight matching value
    """

    left_nodes, right_nodes = [], []

    for tbl in current_state.db_state:
        for row in tbl.rows:
            left_nodes.append(("L", tuple(row)))
    # logger.debug(left_nodes)
    for tbl in depended_state.db_state:
        for row in tbl.rows:
            right_nodes.append(("R", tuple(row)))
    # logger.debug(right_nodes)

    # Create an undirected weighted bipartite graph
    G = nx.Graph()

    # Add left-side nodes to the graph
    G.add_nodes_from(left_nodes, bipartite=0)  # bipartite=0 → left side

    # Add right-side nodes to the graph
    G.add_nodes_from(right_nodes, bipartite=1)  # bipartite=1 → right side

    edges_list = []
    for left_node in left_nodes:
        for right_node in right_nodes:
            weight = node_similarity(left_node[1], right_node[1])
            edge = (left_node, right_node, {"weight": weight})
            edges_list.append(edge)

    G.add_edges_from(edges_list)

    # Perform weighted bipartite matching
    matching = nx.max_weight_matching(G, weight="weight")
    max_weight = sum(G[u][v]["weight"] for u, v in matching)

    unmatched_right = len(right_nodes) - len(matching)  # e.g., 22-10=12
    unmatch_loss = 1.0
    db_score = max_weight - unmatched_right * unmatch_loss
    """
    logger.info("=== Weights after matching ===")
    total_weight = 0
    for u, v in matching:
        weight = G[u][v]['weight']
        logger.info(f"Match: {u} <-> {v}, weight: {weight}")
        total_weight += weight
    logger.info(f"Total weight: {total_weight}")
    logger.info(f"Total pairs: {len(matching)}")
    """

    # Output matching summary
    # logger.debug(f"Bipartite matching score: {max_weight}, penalty: {unmatched_right * unmatch_loss}, total score: {total_weight}")

    # === file_state section ===
    # Tunable parameters
    FILE_EXACT_MATCH_SCORE = 1.0
    DIR_EXISTENCE_SCORE    = 0.2

    # Index by (path, name)
    curr_map = {}
    for f in current_state.file_state:
        key = (f.file_path, f.file_name)
        curr_map.setdefault(key, []).append(f)

    dep_map = {}
    for f in depended_state.file_state:
        key = (f.file_path, f.file_name)
        dep_map.setdefault(key, []).append(f)

    file_score = 0.0

    # 1) Exact match: path + name + content are all identical
    matched_dep_keys = set()
    for key, curr_list in curr_map.items():
        dep_list = dep_map.get(key, [])
        for cf in curr_list:
            for df in dep_list:
                if cf.file_content == df.file_content:
                    file_score += FILE_EXACT_MATCH_SCORE
                    matched_dep_keys.add(key)
                    break  # each current file counts at most once for exact match

    # 2) Same-directory existence match: if the same directory has files but contents don't match,
    #    award a smaller score (do not re-count keys already exact-matched).
    #    Use file path (directory) as the unit.
    dirs_with_dep = set(f.file_path for f in depended_state.file_state)
    for key in curr_map:
        dirpath, _ = key
        if dirpath in dirs_with_dep and key not in matched_dep_keys:
            file_score += DIR_EXISTENCE_SCORE
            # Mark to avoid double-scoring the same directory
            dirs_with_dep.remove(dirpath)

    # Final score
    total_score = db_score + file_score
    logger.debug(f"DB_State_Score: {db_score}, File_State_Score:{file_score}")
    return total_score

def calculate_distance_NoDist(current_state: ServerState, depended_state: ServerState):
    """
    Removed the bipartite-matching-based state distance metric; during seed evaluation,
    rely only on traditional code coverage and response domain expansion as feedback.
    """
    return 0.0
