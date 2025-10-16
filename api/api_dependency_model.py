import copy
import importlib
import json
import re
from math import exp
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence, Set, Union

import msgspec
import numpy as np
from basic.fuzzword import FuzzWord
from basic.http.http_request import HTTPRequest
from basic.http.request_database import RequestDatabase
from basic.http.request_files import RequestFile
from basic.http.request_response import RequestResponse
from basic.position import ApiPosition, ResponsePosition, TablePosition, FilePosition
from api.api_node import ApiNode
from api.edge import Edge, EdgeType
from basic.seed import BLANK_SEED_INPUT, SeedInput
from basic.position import ApiPosition, FilePosition, ResponsePosition, TablePosition
from basic.server_state import ServerState
from interface.docable import Docable
from loguru import logger
from msgspec import field
from util.util import response2fuzzwords
from word_lib import WordLib

from api.api_node import ApiNode
from api.edge import Edge, EdgeType

class APIDependencyModel(msgspec.Struct, tag="api_dependency_model"):
    class VertexInfo(msgspec.Struct, tag="vertex_info"):
        words: list[FuzzWord] = field(default_factory=list)
        files_read: list[str] = field(default_factory=list)
        files_write: list[str] = field(default_factory=list)
        dbs_read: list[str] = field(default_factory=list)
        dbs_write: list[str] = field(default_factory=list)
        docs_read: list[str] = field(default_factory=list)
        docs_write: list[str] = field(default_factory=list)

    vertexes: dict[ApiNode, VertexInfo] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    response_words: dict[ApiNode, list[FuzzWord]] = field(default_factory=dict)
    _cache_edges_by_src: dict[ApiNode, list[Edge]] = field(default_factory=dict)
    _cache_valid: bool = field(default=False)

    def pre_filter(self, node: ApiNode, request: HTTPRequest):
        try:
            filter_id = node.filter_id
        except:
            return True

        import os

        if "filter_path" not in os.environ:
            return True

        filter_path = os.environ["filter_path"]

        try:
            cve_filter_module = importlib.import_module(filter_path)
            filter_method = cve_filter_module.filter_method
            if filter_id not in filter_method:
                return True
            return filter_method[filter_id](request)
        except Exception as e:
            logger.error(f"cve_filter_module {filter_path} failed to load, {e}")
            return True

    def edges_start_by(self) -> dict[ApiNode, list[Edge]]:
        # If cache is invalid or uninitialized, recompute
        if not self._cache_valid or self._cache_edges_by_src is None:
            self._update_cache()
        return self._cache_edges_by_src

    def _update_cache(self):
        """Update edge cache."""
        result: dict[ApiNode, list[Edge]] = {}
        for node in self.vertexes.keys():
            result[node] = []
        for edge in self.edges:
            result[edge.src].append(edge)
        self._cache_edges_by_src = result
        self._cache_valid = True

    def _train_response(
            self, request_response_list: list[RequestResponse], scaler: float = 10
    ):
        # Clear vertexes and response_words payloads
        for vertex_info in self.vertexes.values():
            vertex_info.words.clear()
        for edge in self.edges:
            if edge.typ == EdgeType.RESPONSE:
                self.edges.remove(edge)
        for words in self.response_words.values():
            words.clear()

        # Mark cache invalid
        self._cache_valid = False
        for request_response in request_response_list:
            request = request_response.request

            # Match ApiNode by method and path; choose the one with the fewest template params
            matched_node = self._find_best_matching_node(request)

            if matched_node is None:  # No request in the input came from any API; move on
                logger.warning(f"Request {request.method} {request.path} did not match any API")
                continue
            self._update_positions(matched_node, request)

            response_fuzz_words: list[FuzzWord] = response2fuzzwords(
                request_response.response, msgspec.msgpack.encode(matched_node)
            )
            if self.response_words.get(matched_node) is None:
                self.response_words[matched_node] = []
            for word in response_fuzz_words:
                self.response_words[matched_node].append(word)
            # Add new FuzzWords to the list
            # current_words = {word.value: word for word in self.response_words[matched_node]}
            # for word in response_fuzz_words:
            #    if word.value not in current_words:
            #        self.response_words[matched_node].append(word)

    def _train_database(self, request_db_list: list[RequestDatabase]):
        for edge in self.edges:
            if edge.typ == EdgeType.DATABASE:
                self.edges.remove(edge)
        for request_db in request_db_list:
            request = request_db.request
            # Match ApiNode by method and path; choose the one with the fewest template params
            matched_node = self._find_best_matching_node(request)

            if matched_node is None:  # No request is from the API; stop training this item
                continue
            read = request_db.db_read
            write = request_db.db_write
            self.vertexes[matched_node].dbs_read = list(
                set(self.vertexes[matched_node].dbs_read) | set(read)
            )
            self.vertexes[matched_node].dbs_write = list(
                set(self.vertexes[matched_node].dbs_write) | set(write)
            )
            self.vertexes[matched_node].docs_read = list(
                set(self.vertexes[matched_node].docs_read) | set(request_db.tables_read)
            )
            self.vertexes[matched_node].docs_write = list(
                set(self.vertexes[matched_node].docs_write)
                | set(request_db.tables_write)
            )

    def _train_request_files(
            self, request_files_list: list[RequestFile], scaler: float = 10
    ):
        for edge in self.edges:
            if edge.typ == EdgeType.FILE:
                self.edges.remove(edge)
        for request_files in request_files_list:
            request = request_files.request

            # Match ApiNode by method and path; choose the one with the fewest template params
            matched_node = self._find_best_matching_node(request)

            if matched_node is None:  # No request is from the API; stop training this item
                continue
            read = request_files.read
            write = request_files.write
            self.vertexes[matched_node].files_read = list(
                set(self.vertexes[matched_node].files_read) | set(read)
            )
            self.vertexes[matched_node].files_write = list(
                set(self.vertexes[matched_node].files_write) | set(write)
            )

    def to_wordlib(self) -> WordLib:
        wordlib = WordLib([])
        for info in self.vertexes.values():
            for word in info.words:
                wordlib.insert_word(word)
        for words in self.response_words.values():
            for word in words:
                wordlib.insert_word(word)
        return wordlib

    def dump_bin(self, output: str):
        """
        Serialize the instance to MessagePack format and write the binary data to a file.

        Args:
            output (str): Path to the output file where the binary data will be written.

        Returns:
            None

        Example:
            ```
            model = ApiDependencyModel(...)
            model.dump_bin('/path/to/output.bin')
            ```
        """
        self_bytes = msgspec.msgpack.encode(self)
        Path(output).write_bytes(self_bytes)

    def train(
            self, request_x_list: Sequence[RequestResponse | RequestFile | RequestDatabase]
    ):
        """
        Try to map each request_response.request to an ApiNode in vertexes.keys() using the HTTP method and path
        (uniquely). After finding the node, determine the values filled into each ApiPosition of the ApiNode in the
        actual request and update vertexes.
        For request_response.response, convert the response to list[FuzzWord] with response2fuzzwords and update the
        node's words in response_words (set union).
        """
        if len(request_x_list) == 0:
            self._add_edges("response")
            self._add_edges("file")
            self._add_edges("database")
            self._normalize()
            return
        try:
            if isinstance(request_x_list[0], RequestResponse):
                self._train_response(request_x_list)  # type: ignore
            elif isinstance(request_x_list[0], RequestFile):
                self._train_request_files(request_x_list)  # type: ignore
            elif isinstance(request_x_list[0], RequestDatabase):
                self._train_database(request_x_list)  # type: ignore
            else:
                raise ValueError(
                    "Elements of request_x_list must be RequestResponse or RequestFiles"
                )
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise e
        finally:
            if isinstance(request_x_list[0], RequestResponse):
                self._add_edges("response")
            elif isinstance(request_x_list[0], RequestFile):
                self._add_edges("file")
            elif isinstance(request_x_list[0], RequestDatabase):
                self._add_edges("database")
            else:
                raise ValueError(
                    "Elements of request_x_list must be RequestResponse or RequestFiles"
                )
            self._normalize()

    def _normalize(self):
        """
        Normalize: for edges starting from the same node a, group by type and normalize weights
        (divide by the sum per type). Process all such nodes.
        """
        import numpy as np

        # Group by source and edge type
        edges_by_src = {}
        for edge in self.edges:
            if edge.src not in edges_by_src:
                edges_by_src[edge.src] = {}
            if edge.typ not in edges_by_src[edge.src]:
                edges_by_src[edge.src][edge.typ] = []
            edges_by_src[edge.src][edge.typ].append(edge)

        # Normalize the weights for each edge type per source
        for src_node, edge_types in edges_by_src.items():
            for edge_type, edges in edge_types.items():
                if not edges:
                    continue

                weights = np.array([edge.w for edge in edges], dtype=float)

                # Normalize by sum
                sum_weights = np.sum(weights)
                if sum_weights > 0:
                    normalized_weights = weights / sum_weights
                else:
                    # If sum == 0, use a uniform distribution
                    normalized_weights = np.ones_like(weights) / len(edges)

                for i, edge in enumerate(edges):
                    edge.w = float(normalized_weights[i])

        logger.debug("Edge weight normalization completed")

    def export_words_by_position(
            self,
    ) -> dict[
        Union[ApiPosition, TablePosition, ResponsePosition, FilePosition], list[Any]
    ]:
        """
        Group self.response_words and self.vertexes' FuzzWord by position and
        return dict[ApiPosition, list[Any]].
        """
        result = {}

        # Process FuzzWord in vertexes
        for node, info in self.vertexes.items():
            for word in info.words:
                position = word.position
                if position not in result:
                    result[position] = []
                if word.value not in result[position]:
                    result[position].append(word.value)

        # Process FuzzWord in response_words
        for node, words in self.response_words.items():
            for word in words:
                position = word.position
                if position not in result:
                    result[position] = []
                if word.value not in result[position]:
                    result[position].append(word.value)

        return result

    def _add_edges(self, type: Literal["response", "file", "database"]):
        """
        Use _follow_probability to compute directed edge weights between ApiNodes and add edges.
        """
        api_nodes = self.vertexes.keys()
        for a1 in api_nodes:
            for a2 in api_nodes:
                if a1 is a2:
                    continue
                if type == "response":
                    prob = self._follow_probability(a1, a2, "response")
                    self.edges.append(Edge(a1, a2, EdgeType.RESPONSE, prob))
                elif type == "file":
                    prob = self._follow_probability(a1, a2, "file")
                    self.edges.append(Edge(a1, a2, EdgeType.FILE, prob))
                elif type == "database":
                    prob = self._follow_probability(a1, a2, "database")
                    self.edges.append(Edge(a1, a2, EdgeType.DATABASE, prob))
        # Mark cache invalid because edges were updated
        self._cache_valid = False

    def _follow_probability(
            self,
            a1: ApiNode,
            a2: ApiNode,
            type: Literal["response", "file", "database"],
            db_percentage: float = 0.3,
    ) -> float:
        """
        Estimate the probability that a2 follows a1 in real requests.

        For type == "response":
          - Obtain list[FuzzWord] from self.response_words for a1's response.
          - Obtain list[FuzzWord] from self.vertexes for a2's request.
          - Group both lists by position into two dicts: dict[ApiPosition, list[Any]].
          - Compute Jaccard similarity for every pair of (resp_position_list, req_position_list),
            and return the maximum similarity.

        For file/database types, use intersections of write/read sets accordingly.
        """
        if type == "response":
            if (
                    (a1 not in self.response_words)
                    or (not self.response_words[a1])
                    or (a2 not in self.vertexes)
            ):
                logger.warning(
                    f"{a1.method.value} {a1.path} -> {a2.method.value} {a2.path} follow probability (response): 0.0"
                )
                return 0.0

            response_words: List[FuzzWord] = self.response_words[a1]
            request_words: List[FuzzWord] = self.vertexes[a2].words

            # Group a1 response FuzzWords by position (dict1)
            response_position_words: Dict[
                Union[ApiPosition, ResponsePosition, TablePosition], List[Any]
            ] = {}
            for word in response_words:
                position = word.position
                assert not isinstance(position, FilePosition)
                if response_position_words.get(position) is None:
                    response_position_words[position] = []
                response_position_words[position].append(word.value)

            # Group a2 request FuzzWords by position (dict2)
            request_position_words: Dict[
                Union[ApiPosition, ResponsePosition, TablePosition], List[Any]
            ] = {}
            for word in request_words:
                position = word.position
                assert not isinstance(position, FilePosition)
                if position not in request_position_words:
                    request_position_words[position] = []
                request_position_words[position].append(word.value)

            # Compute Jaccard similarity per position pair, take maximum
            max_similarity: float = 0.0
            for resp_words in response_position_words.values():
                for req_words in request_position_words.values():
                    if not resp_words or not req_words:
                        continue

                    resp_set = set(str(x) for x in resp_words)
                    req_set = set(str(x) for x in req_words)

                    intersection_size = len(resp_set.intersection(req_set))
                    union_size = len(resp_set.union(req_set))

                    if union_size > 0 and intersection_size > 0:
                        jaccard = intersection_size / union_size
                        max_similarity = max(max_similarity, jaccard)
        elif type == "file":
            # Use intersection of a1.files_write and a2.files_read
            set1 = set(self.vertexes[a1].files_write)
            set2 = set(self.vertexes[a2].files_read)
            max_similarity = len(set1 & set2)
        elif type == "database":
            # Use intersection of a1.docs_write and a2.docs_read
            set1 = set(self.vertexes[a1].docs_write)
            set2 = set(self.vertexes[a2].docs_read)
            max_similarity = len(set1 & set2)
        return max_similarity

    def _count_template_params(self, template_path: str) -> int:
        """Count the number of parameter placeholders in a template path."""
        import re
        return len(re.findall(r"\$\{p_[^}]+\}", template_path))

    def _match_path(self, template_path: str, actual_path: str) -> bool:
        import re
        regex_pattern = re.escape(template_path)
        # Specifically match placeholders in the form ${p_xxx}
        regex_pattern = re.sub(r"\\\$\\\{p_[^}]+\\\}", "([^/]+)", regex_pattern)
        regex_pattern = f"^{regex_pattern}$"

        return re.match(regex_pattern, actual_path) is not None

    def _find_best_matching_node(self, request):
        """Find the best-matching API node (fewest template parameters)."""
        candidates = []
        for node in self.vertexes.keys():
            if (
                    self.pre_filter(node, request)
                    and node.method == request.method
                    and self._match_path(node.path, request.path)
            ):
                param_count = self._count_template_params(node.path)
                candidates.append((node, param_count))

        if not candidates:
            return None

        # Sort by number of template parameters and choose the minimum
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    def _update_positions(self, node: ApiNode, request: HTTPRequest):
        """
        node.json is a JSON template that can be parsed via json.loads into a template dict.
        The template uses placeholders like "${v_name}". Compare this template with request.json
        to extract actual values filled into the placeholders. Then add FuzzWord entries to
        self.vertexes[node].words. ApiPosition should be derived by comparing with node.positions,
        ensuring each position has a unique name matching the template.
        """

        logger.debug(
            f"Update node positions: node={node.method.value} {node.path}, request path={request.path}"
        )

        # Ensure node exists in vertexes
        if node not in self.vertexes:
            self.vertexes[node] = APIDependencyModel.VertexInfo()

        # Create a mapping from position name to ApiPosition
        position_map = {pos.name: pos for pos in node.positions}

        # Handle JSON template matching
        if node.json and request.json:
            try:
                # Parse node.json template
                template_dict = json.loads(node.json)
                request_dict = request.json

                logger.debug(f"JSON template: {template_dict}")
                logger.debug(f"Request JSON data: {request_dict}")

                # Recursively compare template and actual data, extracting placeholder values
                self._extract_json_values(
                    template_dict, request_dict, position_map, node
                )

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON template: {e}")
            except Exception as e:
                logger.warning(f"Error while processing JSON template: {e}")

        # Handle other types of parameters (path params, query params, etc.)
        for position in node.positions:
            if (
                    position.name.startswith(
                        ("p_", "q_", "hv_", "hk_", "dv_", "dk_", "fv_", "fk_")
                    )
                    or position.name == "d_payload"
            ):
                value = self._extract_position_value(position, node, request, 0)
                if value is not None:
                    logger.success(f"Position {position.name} detected value: {value}")
                    fuzz_word = FuzzWord(value=value, position=position)

                    # Dedup check
                    exists = any(
                        word.value == value and word.position == position
                        for word in self.vertexes[node].words
                    )

                    if not exists:
                        self.vertexes[node].words.append(fuzz_word)
                        logger.debug(f"Added new value: position = {position.name}, value = {value}")
                    else:
                        logger.debug(
                            f"Value already exists, skip: position = {position.name}, value = {value}"
                        )
                else:
                    logger.debug(f"Position {position.name} value not extractable")

    def _extract_json_values(
            self, template, actual, position_map: dict[str, ApiPosition], node: ApiNode
    ):
        """
        Recursively compare JSON template and actual data, extracting placeholder values.
        """
        if isinstance(template, dict) and isinstance(actual, dict):
            for key, template_value in template.items():
                # Handle key template ${k_xxx}
                if (
                        isinstance(key, str)
                        and key.startswith("${k_")
                        and key.endswith("}")
                ):
                    key_placeholder = key[2:-1]  # remove ${ and }
                    if key_placeholder in position_map:
                        # Find a matching key in the actual object
                        for actual_key in actual.keys():
                            if self._key_matches_template(key, actual_key):
                                logger.success(
                                    f"Position {key_placeholder} detected key: {actual_key}"
                                )
                                fuzz_word = FuzzWord(
                                    value=actual_key,
                                    position=position_map[key_placeholder],
                                )
                                if not self._word_exists(fuzz_word, node):
                                    self.vertexes[node].words.append(fuzz_word)
                                    logger.debug(
                                        f"Extract key: {key_placeholder} = {actual_key}"
                                    )
                                else:
                                    logger.debug(
                                        f"Key already exists, skip: {key_placeholder} = {actual_key}"
                                    )
                                # Recurse into the matched value
                                if actual_key in actual:
                                    self._extract_json_values(
                                        template_value,
                                        actual[actual_key],
                                        position_map,
                                        node,
                                    )
                                break
                elif key in actual:
                    # Direct key match, recurse on the value
                    self._extract_json_values(
                        template_value, actual[key], position_map, node
                    )
                else:
                    # Try to find a matching key (consider underscore prefix)
                    for actual_key, actual_value in actual.items():
                        if actual_key == key or actual_key == f"_{key}":
                            self._extract_json_values(
                                template_value, actual_value, position_map, node
                            )
                            break

        elif isinstance(template, list) and isinstance(actual, list):
            # Lists: recurse element by element
            min_len = min(len(template), len(actual))
            for i in range(min_len):
                self._extract_json_values(template[i], actual[i], position_map, node)

        elif (
                isinstance(template, str)
                and template.startswith("${v_")
                and template.endswith("}")
        ):
            # Handle value template ${v_xxx}
            value_placeholder = template[2:-1]  # remove ${ and }
            if value_placeholder in position_map:
                logger.success(f"Position {value_placeholder} detected value: {actual}")
                fuzz_word = FuzzWord(
                    value=actual, position=position_map[value_placeholder]
                )
                if not self._word_exists(fuzz_word, node):
                    self.vertexes[node].words.append(fuzz_word)
                    logger.debug(f"Extract value: {value_placeholder} = {actual}")
                else:
                    logger.debug(f"Value already exists, skip: {value_placeholder} = {actual}")

    def _key_matches_template(self, template_key: str, actual_key: str) -> bool:
        """
        Check whether the actual key matches the template key.
        """
        if template_key.startswith("${k_") and template_key.endswith("}"):
            # For key templates, any non-empty string may match
            return isinstance(actual_key, str) and len(actual_key) > 0
        return template_key == actual_key

    def _word_exists(self, fuzz_word: FuzzWord, node: ApiNode) -> bool:
        """
        Check whether a FuzzWord already exists.
        """
        return any(
            word.value == fuzz_word.value and word.position == fuzz_word.position
            for word in self.vertexes[node].words
        )

    def _extract_position_value(
            self,
            position: ApiPosition,
            node: ApiNode,
            request: HTTPRequest,
            position_cnt: int,
    ) -> Any:
        name = position.name

        # Path params (p_xxx)
        if name.startswith("p_"):
            param_name = name[2:]  # remove 'p_' prefix
            template_parts = node.path.split("/")
            actual_parts = request.path.split("/")

            # Ensure the number of parts matches
            if len(template_parts) != len(actual_parts):
                logger.debug(
                    f"Path segment count mismatch: template={template_parts}, actual={actual_parts}"
                )
                return None

            # Find the placeholder in the path and extract value
            for i, part in enumerate(template_parts):
                placeholder = f"${{p_{param_name}}}"
                if placeholder in part:
                    # If the entire segment is the placeholder, return the segment directly
                    if part == placeholder:
                        return actual_parts[i]
                    else:
                        # Otherwise, extract the placeholder-matched portion
                        pattern_str = re.escape(part).replace(
                            re.escape(placeholder), "([^/]+)"
                        )
                        pattern = re.compile(pattern_str)
                        match = pattern.match(actual_parts[i])
                        if match:
                            return match.group(1)

        # Query params (q_xxx)
        elif name.startswith("q_"):
            param_name = name[2:]  # remove 'q_' prefix
            if request.params and isinstance(request.params, dict):
                return request.params.get(param_name)

        # JSON fields (v_xxx or k_xxx)
        elif (name.startswith("v_") or name.startswith("k_")) and request.json:
            return self._search_json_value(name, request.json, position_cnt)

        # Headers (hv_xxx or hk_xxx)
        elif name.startswith("hv_") or name.startswith("hk_") and request.headers:
            return self._search_json_value(name, request.headers, position_cnt)
        # data payload
        elif name == "d_payload":
            return request.data
        # Form data (dv_xxx or dk_xxx)
        elif name.startswith("dv_") or name.startswith("dk_"):
            return self._search_json_value(name, request.data, position_cnt)
        # File uploads (fv_xxx or fk_xxx)
        elif name.startswith("fv_") or name.startswith("fk_"):
            return self._search_json_value(name, request.files, position_cnt)
        return None

    def _search_json_value(self, name: str, json_data: Any, position_cnt: int) -> Any:
        logger.info(f"Current JSON {json_data}, searching for the {position_cnt}-th match")

        # Track number of matches found
        found_count = [0]  # use list for closure mutation

        def _search_recursive(data):
            if isinstance(data, list):
                for item in data:
                    result = _search_recursive(item)
                    if result is not None:
                        return result
            elif isinstance(data, dict):
                for k, v in data.items():
                    # Handle fields with v_ prefix
                    if name.startswith("v_"):
                        field_name = name[2:]  # remove v_ prefix
                        # Match field name directly or with underscore prefix
                        if k == field_name or k == f"_{field_name}":
                            if found_count[0] == position_cnt:
                                logger.debug(
                                    f"Found the {position_cnt}-th matching field: {k} -> {v}"
                                )
                                return v
                            found_count[0] += 1
                    elif (
                            name.startswith("dv_")
                            or name.startswith("hv_")
                            or name.startswith("fv_")
                    ):
                        field_name = name[3:]  # remove xV_ prefix
                        # Match field name directly or with underscore prefix
                        if k == field_name or k == f"_{field_name}":
                            if found_count[0] == position_cnt:
                                logger.debug(
                                    f"Found the {position_cnt}-th matching field: {k} -> {v}"
                                )
                                return v
                            found_count[0] += 1
                    # Handle keys with k_ prefix
                    elif name.startswith("k_"):
                        key_name = name[2:]  # remove k_ prefix
                        if k == key_name or k == f"_{key_name}":
                            if found_count[0] == position_cnt:
                                logger.debug(f"Found the {position_cnt}-th matching key: {k}")
                                return k
                            found_count[0] += 1
                    elif name.startswith("dk_") or name.startswith("hk_"):
                        key_name = name[3:]  # remove xk_ prefix
                        if k == key_name or k == f"_{key_name}":
                            if found_count[0] == position_cnt:
                                logger.debug(f"Found the {position_cnt}-th matching key: {k}")
                                return k
                            found_count[0] += 1

                    # Recurse into nested dict/list
                    if isinstance(v, (dict, list)):
                        result = _search_recursive(v)
                        if result is not None:
                            return result
            return None

        return _search_recursive(json_data)

    def _max_probability(self, api: ApiNode, target: ApiNode, ratio: str) -> float:
        """
        Compute the maximum probability among all paths from api to target.
        Consider all edge types: RESPONSE, FILE, DATABASE.
        For each node pair, combine the three edge types according to the provided ratio.
        Since weights represent probabilities (0<prob<=1), maximizing the product of edge
        probabilities is equivalent to minimizing the sum of -ln(prob), i.e., a shortest
        path problem.
        """
        splited_ratio = ratio.split(":")
        response, file, database = (
            float(splited_ratio[0]),
            float(splited_ratio[1]),
            float(splited_ratio[2]),
        )
        ratio_sum = response + file + database
        response, file, database = (
            response / ratio_sum,
            file / ratio_sum,
            database / ratio_sum,
        )

        if api == target:
            return 1.0

        # Build merged-edge graph: combine three types per node pair by ratio
        merged_edges = {}  # (src, dst) -> combined_weight

        for edge in self.edges:
            key = (edge.src, edge.dst)
            if key not in merged_edges:
                merged_edges[key] = 0.0

            # Weighted merge by edge type
            if edge.typ == EdgeType.RESPONSE:
                merged_edges[key] += edge.w * response
            elif edge.typ == EdgeType.FILE:
                merged_edges[key] += edge.w * file
            elif edge.typ == EdgeType.DATABASE:
                merged_edges[key] += edge.w * database

        # Dijkstra on -ln(prob) to find the maximum-probability path
        import heapq

        graph = {}
        for (src, dst), prob in merged_edges.items():
            if src not in graph:
                graph[src] = []
            if prob > 0:
                weight = -np.log(prob)
            else:
                weight = float("inf")
            graph[src].append((dst, weight))

        # Ensure all nodes are present
        all_nodes = set(self.vertexes.keys())
        for node in all_nodes:
            if node not in graph:
                graph[node] = []

        # Dijkstra
        distances = {node: float("inf") for node in all_nodes}
        distances[api] = 0.0
        # Unique counter to avoid ApiNode comparison issues
        counter = 0
        pq = [(0.0, counter, api)]
        visited = set()

        while pq:
            current_dist, _, current_node = heapq.heappop(pq)

            if current_node in visited:
                continue

            visited.add(current_node)

            if current_node == target:
                if distances[target] == float("inf"):
                    return 0.0
                return np.exp(-distances[target])

            for neighbor, weight in graph.get(current_node, []):
                if neighbor not in visited:
                    new_dist = current_dist + weight
                    if new_dist < distances[neighbor]:
                        distances[neighbor] = new_dist
                        counter += 1
                        heapq.heappush(pq, (new_dist, counter, neighbor))

        # No path found
        return 0.0

    def _supress(self, apis: list['ApiNode'], prob: np.ndarray, seed: SeedInput) -> np.ndarray:
        """
        If a specific API has already been selected >= 3 times, heavily suppress its probability.
        apis and prob are aligned.
        Return the normalized suppressed probabilities.
        """
        api_selected_times = {}
        for api in seed.api_list:
            if api in api_selected_times:
                api_selected_times[api] += 1
            else:
                api_selected_times[api] = 1
        # Get times selected for each API
        counts = np.array([api_selected_times.get(api, 0) for api in apis])

        # Build suppression factors: strong suppression when count >= 3
        suppression_factors = np.ones(len(counts))
        # Tunable: e.g., 0.1 means reduce to 10% of the original
        strong_suppress_factor = 0.05  # Tunable: 0.01~0.3
        suppression_factors[counts >= 2] *= strong_suppress_factor

        # Apply suppression
        suppressed_prob = prob * suppression_factors

        # Normalize
        total = np.sum(suppressed_prob)
        if total <= 0:
            # Fallback: if all suppressed to zero, revert to uniform
            return np.ones_like(prob) / len(prob)

        return suppressed_prob / total

    def _apply_context(
            self,
            api_sequence: List[ApiNode],
            apis: List[ApiNode],
            prob_based_on_normal: np.ndarray,
            state_diff: ServerState,
            ratio: str,
            graph_table_file: str,
            api_pos_satisfiability: dict[ApiPosition, float],
            seed: SeedInput
    ) -> np.ndarray:
        if len(prob_based_on_normal) != len(self.vertexes):
            logger.warning(
                f"Abnormal when adding state differences into API inference, len(probabilities) != len(self.vertexes): '{len(prob_based_on_normal)} != {len(self.vertexes)}'"
            )
            return prob_based_on_normal
        # logger.info(f"State diff: {state_diff}")
        tables_to_write: Set[str] = set()
        files_to_write: Set[str] = set()
        for table in state_diff.db_state:
            tables_to_write.add(table.table_name)
        for file in state_diff.file_state:
            files_to_write.add(file.file_path)
        # APIs that can cause these table changes
        tables_candidates: Dict[ApiNode, int] = {}
        # APIs that can cause these file changes
        files_candidates: Dict[ApiNode, int] = {}
        for api, info in self.vertexes.items():
            tables_this_api_write = set(info.dbs_write) | set(info.docs_write)
            changes_this_api_can_make = tables_this_api_write & tables_to_write
            if len(changes_this_api_can_make) > 0:
                tables_candidates[api] = len(changes_this_api_can_make)

            files_this_api_write = set(info.files_write)
            # Drop filename and consider parent directory
            files_this_api_write |= {str(Path(p).parent) for p in list(files_this_api_write) if p}
            changes_this_api_can_make = files_this_api_write & files_to_write
            if len(changes_this_api_can_make) > 0:
                files_candidates[api] = len(changes_this_api_can_make)

        # logger.info(f"APIs that can cause file state changes: { {api.path for api in files_candidates.keys()} }")
        logger.debug(f"APIs that can cause table state changes: { {api for api in tables_candidates.keys()} }")
        # Merge candidates
        candidates = tables_candidates.keys() | files_candidates.keys()
        score = [0.0] * len(prob_based_on_normal)
        for target_api in candidates:
            for i, api in enumerate(apis):
                score[i] += self._max_probability(api, target_api, ratio)
        # Normalize
        prob_based_on_state = np.array(score, dtype=float)
        if np.sum(prob_based_on_state) > 0:
            prob_based_on_state /= np.sum(prob_based_on_state)
        else:
            prob_based_on_state = np.ones_like(prob_based_on_state) / len(
                prob_based_on_state
            )

        # Inference based on parameter satisfiability
        prob_based_on_satisfiability = np.array(
            [1.0] * len(prob_based_on_normal), dtype=float
        )
        for i, api in enumerate(apis):
            for pos in api.positions:
                if pos not in api_pos_satisfiability:
                    pos_satisfiability = float('inf')
                else:
                    pos_satisfiability = api_pos_satisfiability[pos]
                # For each API, use the minimum of its positions' satisfiability
                f_pos = api_pos_satisfiability.get(pos, 0.0)
                prob_based_on_satisfiability[i] = min(
                    prob_based_on_satisfiability[i], pos_satisfiability
                )
        # Normalize
        if sum(prob_based_on_satisfiability) > 0:
            prob_based_on_satisfiability /= sum(prob_based_on_satisfiability)
        else:
            prob_based_on_satisfiability = np.ones_like(
                prob_based_on_satisfiability
            ) / len(prob_based_on_satisfiability)
        weights = [
            float(n) / sum(map(float, graph_table_file.split(":")))
            for n in graph_table_file.split(":")
        ]
        """
        logger.debug(f"Current sequence\n{api_sequence}")
        logger.debug("Static inference")
        for i, api in enumerate(apis):
            logger.debug(f"{api} --> {prob_based_on_normal[i]}")
        logger.debug("State-diff-based inference")
        for i, api in enumerate(apis):
            logger.debug(f"{api} --> {prob_based_on_state[i]}")
        logger.debug("Satisfiability-based inference")
        for i, api in enumerate(apis):
            logger.debug(f"{api} --> {prob_based_on_satisfiability[i]}")
        """
        prob = (
                weights[0] * prob_based_on_normal
                + weights[1] * prob_based_on_state
                + weights[2] * prob_based_on_satisfiability
        )
        """
        logger.debug("Combined inference")
        for i, api in enumerate(apis):
            logger.debug(f"{api} --> {prob[i]}")
        """
        suppressed_prob = self._supress(apis, prob, seed)

        return suppressed_prob

    def infer_NoSelect(
            self,
            api_sequence: list[ApiNode],
            api_pos_satisfiability: dict[ApiPosition, float],
            current_state: Optional[ServerState] = None,
            depended_state: Optional[ServerState] = None,
            h: Callable[[float], float] = lambda x: 4 * exp(-2 * x),
            b: float = 1.0,
            ratio: str = "1:2:2",  # Weighting across RESPONSE, FILE, DATABASE in the dependency graph
            static_state_satisfiability: str = "1:1:1",
            seed: SeedInput = BLANK_SEED_INPUT
    ) -> ApiNode:
        """
        Removed multi-heuristic API selection; instead, randomly select from all available APIs.
        """
        import random
        return random.choice(list(self.vertexes.keys()))

    def infer(
            self,
            api_sequence: list[ApiNode],
            api_pos_satisfiability: dict[ApiPosition, float],
            current_state: Optional[ServerState] = None,
            depended_state: Optional[ServerState] = None,
            h: Callable[[float], float] = lambda x: 4 * exp(-2 * x),
            b: float = 1.0,
            ratio: str = "1:2:2",  # Weighting across RESPONSE, FILE, DATABASE in the dependency graph
            static_state_satisfiability: str = "1:1:1",
            seed: SeedInput = BLANK_SEED_INPUT
    ) -> ApiNode:
        response_ratio, file_ratio, database_ratio = map(float, ratio.split(":"))
        d = {api: 0.0 for api in self.vertexes.keys()}
        scores = dict(sorted(d.items()))
        edges_from_src = self.edges_start_by()
        for i, api in enumerate(reversed(api_sequence)):
            for edge in edges_from_src[api]:
                if edge.typ == EdgeType.RESPONSE:
                    scores[edge.dst] += edge.w * h(i) * b * response_ratio
                elif edge.typ == EdgeType.FILE:
                    scores[edge.dst] += edge.w * h(i) * b * file_ratio
                elif edge.typ == EdgeType.DATABASE:
                    scores[edge.dst] += edge.w * h(i) * b * database_ratio
        # Softmax scores to probabilities and sample an API

        import random

        assert len(scores) > 0
        apis = list(scores.keys())
        score_values = np.array([scores[api] for api in apis], dtype=float)
        if len(score_values) > 0:
            score_values = score_values - np.max(score_values)
            exp_scores = np.exp(score_values)
            sum_exp_scores = np.sum(exp_scores)
            if sum_exp_scores > 0:
                probabilities = exp_scores / sum_exp_scores
            else:
                probabilities = np.ones_like(score_values) / len(score_values)
            # probabilities is the selection distribution
            if current_state and depended_state:
                probabilities = self._apply_context(
                    api_sequence,
                    apis,
                    probabilities,
                    depended_state - current_state,
                    ratio,
                    static_state_satisfiability,
                    api_pos_satisfiability,
                    seed
                )
            # logger.debug(f"Candidate APIs:{[api.method.value+' '+api.path for api in apis]}, Softmax probabilities: {probabilities}")
            selected_index = np.random.choice(len(apis), p=probabilities)
            api_sequence_path = [
                f"{api.method.value} {api.path}" for api in api_sequence
            ]
            logger.debug(
                f"Input sequence: {api_sequence_path}, inference result: {apis[selected_index].method.value} {apis[selected_index].path}"
            )
            selected_api = apis[selected_index]
            return selected_api
        else:
            if self.vertexes:
                selected_api = random.choice(list(self.vertexes.keys()))
                return selected_api
            else:
                raise ValueError("No available API node for inference")

    @classmethod
    def from_doc(cls, doc: Docable):
        """Create an API dependency model instance from a document."""
        model = cls(edges=[])
        response_words = {}
        for node in doc.get_nodes():
            model.vertexes[node] = APIDependencyModel.VertexInfo(
                words=[], files_read=[], files_write=[]
            )
            response_words[node] = []
        model.response_words = response_words
        return model

    def plot_dependency_graph_with_combined(
            self, output_file: str = "api_dependency_graph.html", ratio: str = "1:0:1"
    ):
        """
        Plot an interactive API dependency network graph with edges combined according to ratio.
        ratio: weights for RESPONSE, FILE, DATABASE edges.
        """
        try:
            import networkx as nx
            from pyvis.network import Network
        except ImportError:
            print("Please install required libs: pip install networkx pyvis")
            return

        # Parse weights
        splited_ratio = ratio.split(":")
        response_ratio, file_ratio, database_ratio = (
            float(splited_ratio[0]),
            float(splited_ratio[1]),
            float(splited_ratio[2]),
        )
        ratio_sum = response_ratio + file_ratio + database_ratio
        response_ratio, file_ratio, database_ratio = (
            response_ratio / ratio_sum,
            file_ratio / ratio_sum,
            database_ratio / ratio_sum,
        )

        method_colors = {
            "GET": "#1f77b4",
            "POST": "#ff7f0e",
            "PUT": "#2ca02c",
            "DELETE": "#d62728",
        }

        nodes = []
        for node in self.vertexes:
            m = node.method.value
            p = node.path
            disp = p if len(p) <= 15 else p[:15] + "..."
            nid = f"{m}_{p}"
            label = f"{m} {disp}"
            nodes.append((nid, label, m, p))

        node_cnt = len(nodes)
        NODE_SIZE = max(12, min(20, int(1100 / ((node_cnt + 8) ** 0.63))))
        SPRING_LENGTH = min(750, int(340 + node_cnt * 2.3))
        SPRING_LENGTH = max(SPRING_LENGTH, 350)
        FONT_SIZE = 11 if node_cnt < 80 else 10

        # Merge edge weights per node pair by type and ratio
        merged_edges = {}  # (src_id, dst_id) -> combined_weight
        edge_details = {}  # (src_id, dst_id) -> {response_w, file_w, database_w}

        for e in self.edges:
            if e.w < 0.0:
                continue
            src_id = f"{e.src.method.value}_{e.src.path}"
            dst_id = f"{e.dst.method.value}_{e.dst.path}"
            key = (src_id, dst_id)

            if key not in merged_edges:
                merged_edges[key] = 0.0
                edge_details[key] = {"RESPONSE": 0.0, "FILE": 0.0, "DATABASE": 0.0}

            # Weighted merge by type
            typ = e.typ.name
            edge_details[key][typ] = e.w
            if typ == "RESPONSE":
                merged_edges[key] += e.w * response_ratio
            elif typ == "FILE":
                merged_edges[key] += e.w * file_ratio
            elif typ == "DATABASE":
                merged_edges[key] += e.w * database_ratio

        logger.info(f"Merged edge count: {len(merged_edges)}")

        net = Network(height="830px", width="100%", directed=True, bgcolor="#f5f5f5")
        net.toggle_physics(True)

        # Add nodes
        for nid, label, method, full_path in nodes:
            color = method_colors.get(method, "#888")
            net.add_node(
                nid,
                label=label,
                title=f"{method} {full_path}",
                shape="circle",
                size=NODE_SIZE,
                color={"background": color, "border": "#333"},  # type: ignore
                font={"face": "Helvetica, Arial, sans-serif", "size": FONT_SIZE},
            )

        # Add merged edges
        for (src_id, dst_id), combined_weight in merged_edges.items():
            if combined_weight <= 0:
                continue

            details = edge_details[(src_id, dst_id)]
            # Build detail string
            detail_parts = []
            if details["RESPONSE"] > 0:
                detail_parts.append(f"RESPONSE: {details['RESPONSE']:.3f}")
            if details["FILE"] > 0:
                detail_parts.append(f"FILE: {details['FILE']:.3f}")
            if details["DATABASE"] > 0:
                detail_parts.append(f"DATABASE: {details['DATABASE']:.3f}")
            detail_str = ", ".join(detail_parts)

            # Edge width based on merged weight
            width = 1 + min(5.0, combined_weight * 5.0)

            # Color based on dominant type
            dominant_type = max(details.keys(), key=lambda k: details[k])
            if dominant_type == "RESPONSE":
                edge_color = "#FF5733"
            elif dominant_type == "FILE":
                edge_color = "#33A8FF"
            else:  # DATABASE
                edge_color = "#33FF57"

            # Dashes for very small weights
            if combined_weight < 0.01:
                net.add_edge(
                    src_id,
                    dst_id,
                    title=f"Merged weight: {combined_weight:.3f}\\n{detail_str}",
                    color=edge_color,
                    width=1,
                    dashes=True,
                    smooth={"type": "curvedCW", "roundness": 0.1},
                )
            else:
                net.add_edge(
                    src_id,
                    dst_id,
                    title=f"Merged weight: {combined_weight:.3f}\\n{detail_str}",
                    color=edge_color,
                    width=width,
                    smooth={"type": "curvedCW", "roundness": 0.1},
                )

        # Network options
        options = {
            "physics": {
                "barnesHut": {
                    "gravitationalConstant": -2500,
                    "centralGravity": 0.21,
                    "springLength": SPRING_LENGTH,
                    "springConstant": 0.027,
                    "damping": 0.54,
                }
            },
            "edges": {
                "arrows": {"to": {"enabled": True, "scaleFactor": 1.18}},
                "smooth": True,
            },
            "interaction": {
                "dragNodes": True,
                "zoomView": True,
                "navigationButtons": True,
                "hover": True,
            },
        }
        net.set_options(json.dumps(options))
        net.save_graph(output_file)

        # Sidebar & interactions
        panel = f"""
        <style>
          #info-panel {{
            position: absolute; top:10px; left:10px;
            background:#fff; padding:10px; border:1px solid #ccc;
            border-radius:6px; font-size:13px; z-index:999;
            width:380px; max-height:700px; overflow:auto;
          }}
          #ratio-info {{
            position: absolute; top:10px; right:10px;
            background:#fff; padding:8px; border:1px solid #ccc;
            border-radius:4px; font-size:12px; z-index:999;
          }}
          .weight-detail {{
            margin: 5px 0; padding: 3px; 
            background: #f8f9fa; border-radius: 3px;
          }}
        </style>
        <div id="ratio-info">
          <strong>Weight ratio:</strong><br>
          RESPONSE: {response_ratio:.2f}<br>
          FILE: {file_ratio:.2f}<br>
          DATABASE: {database_ratio:.2f}
        </div>
        <div id="info-panel">
          <h4>Merged-edge Dependency Graph</h4>
          <div id="node-info">Click a node to see details of merged outgoing edges</div>
        </div>
        <script>
        function init() {{
          if (typeof network==='undefined') return setTimeout(init,200);

          network.on('click', function(params){{
            if(params.nodes.length!==1) return;
            var id = params.nodes[0];
            var node = network.body.data.nodes.get(id);

            // Collect all outgoing edges of this node
            var outEdges = [];
            network.body.data.edges.get().forEach(function(e){{
                if(e.from===id) {{
                    var toNode = network.body.data.nodes.get(e.to);
                    var weightMatch = e.title.match(/Merged weight: ([0-9.]+)/);
                    var weight = weightMatch ? parseFloat(weightMatch[1]) : 0;
                    outEdges.push({{
                        to: toNode.title,
                        weight: weight,
                        details: e.title
                    }});
                }}
            }});

            // Sort by weight desc
            outEdges.sort(function(a,b){{return b.weight - a.weight}});

            var html = '<b>Node:</b> ' + node.title + '<br><br>';
            if(outEdges.length > 0) {{
                html += '<b>Outgoing edges (by weight desc):</b><br>';
                outEdges.forEach(function(e){{
                    html += '<div class="weight-detail">';
                    html += '<b>→ ' + e.to + '</b><br>';
                    html += e.details.replace(/\\n/g, '<br>');
                    html += '</div>';
                }});
            }} else {{
                html += '<i>No outgoing edges</i>';
            }}

            document.getElementById('node-info').innerHTML = html;
          }});
        }}
        init();
        </script>
        """

        with open(output_file, "r", encoding="utf-8") as f:
            html = f.read()
        html = html.replace("</body>", panel + "</body>")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"Interactive dependency graph with merged weights saved to: {output_file}")

    def plot_dependency_graph(self, output_file: str = "api_dependency_graph.html"):
        """
        Plot an interactive API dependency network graph. The sidebar groups edges by type
        and sorts each group by weight in descending order. Arrow/line alignment optimized.
        """
        try:
            import networkx as nx
            from pyvis.network import Network
        except ImportError:
            print("Please install required libs: pip install networkx pyvis")
            return

        method_colors = {
            "GET": "#1f77b4",
            "POST": "#ff7f0e",
            "PUT": "#2ca02c",
            "DELETE": "#d62728",
        }
        edge_cfg = {
            "RESPONSE": {"color": "#FF5733", "curve": 0.2},
            "FILE": {"color": "#33A8FF", "curve": -0.2},
            "DATABASE": {"color": "#33FF57", "curve": 0},
        }

        nodes = []
        for node in self.vertexes:
            m = node.method.value
            p = node.path
            filter_id = node.filter_id
            disp = p if len(p) <= 15 else p[:15] + "..."
            nid = f"{m}_{p}_{filter_id}"
            label = f"{m} {disp}"
            nodes.append((nid, label, m, p, filter_id))

        node_cnt = len(nodes)
        NODE_SIZE = max(12, min(20, int(1100 / ((node_cnt + 8) ** 0.63))))
        SPRING_LENGTH = min(750, int(340 + node_cnt * 2.3))
        SPRING_LENGTH = max(SPRING_LENGTH, 350)
        FONT_SIZE = 11 if node_cnt < 80 else 10

        raw_edges = []
        stats = {"RESPONSE": 0, "FILE": 0, "DATABASE": 0}
        pair_counts = {}
        for e in self.edges:
            if e.w < 0.0:
                continue
            src_id = f"{e.src.method.value}_{e.src.path}_{e.src.filter_id}"
            dst_id = f"{e.dst.method.value}_{e.dst.path}_{e.dst.filter_id}"
            typ = e.typ.name
            key = (src_id, dst_id, typ)
            pair_counts[key] = pair_counts.get(key, 0) + 1
            raw_edges.append((src_id, dst_id, typ, e.w))
            stats[typ] += 1

        logger.info(
            f"Ready to add edges: TOTAL={len(raw_edges)}, "
            + ", ".join(f"{k}={v}" for k, v in stats.items())
        )

        net = Network(height="830px", width="100%", directed=True, bgcolor="#f5f5f5")
        net.toggle_physics(True)

        for nid, label, method, full_path, filter_id in nodes:
            color = method_colors.get(method, "#888")
            net.add_node(
                nid,
                label=label,
                title=f"{method} {full_path}",
                shape="circle",
                size=NODE_SIZE,
                color={"background": color, "border": "#333"},  # type: ignore
                font={"face": "Helvetica, Arial, sans-serif", "size": FONT_SIZE},
                # Add filter_id as a custom node attribute
                filter_id=filter_id,
                method=method,
                full_path=full_path,
            )

        for src_id, dst_id, typ, w in raw_edges:
            cfg = edge_cfg[typ]
            cnt = pair_counts[(src_id, dst_id, typ)]
            rd = cfg["curve"] * (1 + cnt // 2)
            width = 1 + min(3.2, w * 3.2)
            if w < 0.01:
                net.add_edge(
                    src_id,
                    dst_id,
                    title=f"{typ} weight={w:.3f}",
                    color=cfg["color"],
                    width=1,
                    edge_type=typ,
                    dashes=True,
                    smooth={"type": "curvedCW", "roundness": rd},
                )
            else:
                net.add_edge(
                    src_id,
                    dst_id,
                    title=f"{typ} weight={w:.3f}",
                    color=cfg["color"],
                    width=width,
                    edge_type=typ,
                    smooth={"type": "curvedCW", "roundness": rd},
                )

        options = {
            "physics": {
                "barnesHut": {
                    "gravitationalConstant": -2500,
                    "centralGravity": 0.21,
                    "springLength": SPRING_LENGTH,
                    "springConstant": 0.027,
                    "damping": 0.54,
                }
            },
            "edges": {
                "arrows": {"to": {"enabled": True, "scaleFactor": 1.18}},
                "smooth": True,
            },
            "interaction": {
                "dragNodes": True,
                "zoomView": True,
                "navigationButtons": True,
                "hover": True,
            },
        }
        net.set_options(json.dumps(options))
        net.save_graph(output_file)

        panel_colors = {"RESPONSE": "#FF5733", "FILE": "#33A8FF", "DATABASE": "#33FF57"}
        panel = f"""
        <style>
          #filter, #detail {{
            position: absolute; top:10px; background:#fff;
            padding:8px; border:1px solid #ccc;
            border-radius:4px; font-size:13px; z-index:999;
          }}
          #filter {{ right:10px; }}
          #detail {{
            left:10px; width:350px;
            max-height:700px; overflow:auto;
          }}
          .etype-response{{color:{panel_colors['RESPONSE']};font-weight:bold}}
          .etype-file{{color:{panel_colors['FILE']};font-weight:bold}}
          .etype-database{{color:{panel_colors['DATABASE']};font-weight:bold}}
          .out-class-title{{margin:3px 0 2px 2px;padding:2px 2px 2px 0;font-size:14px;}}
          .filter-id{{color:#666;font-size:11px;margin-top:2px;}}
        </style>
        <div id="filter">
          <strong>Edge type filter:</strong><br>
          <label><input type="checkbox" id="c-RESPONSE" checked> <span style="color:{panel_colors['RESPONSE']}">RESPONSE</span></label><br>
          <label><input type="checkbox" id="c-FILE"     checked> <span style="color:{panel_colors['FILE']}">FILE</span></label><br>
          <label><input type="checkbox" id="c-DATABASE" checked> <span style="color:{panel_colors['DATABASE']}">DATABASE</span></label>
        </div>
        <div id="detail">
          <h4>Node details</h4>
          <div id="info">Click a node to view details</div>
        </div>
        <script>
        function edgeType2Class(tp) {{
            if(tp==="RESPONSE") return "etype-response";
            if(tp==="FILE") return "etype-file";
            if(tp==="DATABASE") return "etype-database";
            return "";
        }}
        function edgeType2Disp(tp) {{
            if(tp==="RESPONSE") return "RESPONSE";
            if(tp==="FILE") return "FILE";
            if(tp==="DATABASE") return "DATABASE";
            return tp;
        }}
        function init() {{
          if (typeof network==='undefined') return setTimeout(init,200);
          ['RESPONSE','FILE','DATABASE'].forEach(function(t){{
            document.getElementById('c-'+t).onchange = function(){{
              var hide = !this.checked;
              network.body.data.edges.get().forEach(function(e){{
                if(e.edge_type===t){{
                  network.body.data.edges.update({{id:e.id,hidden:hide}});
                }}
              }});
            }};
          }});
          network.on('click', function(params){{
            if(params.nodes.length!==1) return;
            var id = params.nodes[0];
            var node = network.body.data.nodes.get(id);

            // Group outgoing edges by type
            var outmap = {{"RESPONSE":[], "FILE":[], "DATABASE":[]}};
            network.body.data.edges.get().forEach(function(e){{
                if(e.from===id) {{
                    var typ = e.edge_type;
                    var toNode = network.body.data.nodes.get(e.to);
                    outmap[typ].push({{
                        to: toNode.title,
                        to_filter_id: toNode.filter_id,
                        typ: typ,
                        w: parseFloat(e.title.split(' weight=')[1])
                    }});
                }}
            }});
            Object.keys(outmap).forEach(function(typ){{
                outmap[typ].sort(function(a,b){{return b.w - a.w}});
            }});

            var html = '<b>Method:</b> ' + node.title.split(' ')[0] + '<br>' +
                       '<b>Full path:</b> ' + node.title.split(' ').slice(1).join(' ') + '<br>' +
                       '<div class="filter-id"><b>Filter ID:</b> ' + node.filter_id + '</div>';

            ["RESPONSE","FILE","DATABASE"].forEach(function(typ){{
                if(outmap[typ].length>0){{
                    html += '<div class="out-class-title '+edgeType2Class(typ)+'">'+typ+'</div><ul>';
                    outmap[typ].forEach(function(e){{
                        html += '<li>' + e.to + ' <span style="color:gray">(weight: ' + e.w.toFixed(3) + ')</span>' +
                               '<div class="filter-id">Filter ID: ' + e.to_filter_id + '</div></li>';
                    }});
                    html += '</ul>';
                }}
            }});
            document.getElementById('info').innerHTML = html;
          }});
        }}
        init();
        </script>
        """
        with open(output_file, "r", encoding="utf-8") as f:
            html = f.read()
        html = html.replace("</body>", panel + "</body>")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"Interactive dependency graph saved to: {output_file}")


