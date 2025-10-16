import base64
from functools import total_ordering
import json
import re
from typing import Any
import io
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import msgspec
from basic.fuzzword import WordList
from basic.http.content_type import ContentType
from basic.http.http_request import HTTPMethod, HTTPRequest
from basic.position import ApiPosition
from loguru import logger


@total_ordering
class ApiNode(msgspec.Struct, tag="api_node"):
    path: str  # /api/cores/${p_core}
    method: HTTPMethod  # GET / POST / PUT / DELETE
    headers: str = (
        ""  # {"Content-Type": "application/json", "Content-Length": ${hv_token}}
    )
    params: str = ""  # "reload=${q_reload}&action=${q_action}"
    data: Any = ""  # {"name": ${dv_name}, "password": ${dv_password}}
    json: str = ""  # { ${k_core}: ${v_core}, "is_ok": ${v_is_ok} }
    files: str = ""  # file dictionary {"f1": ${fv_avatar}, "f2": ${fv_book}}

    filter_id: str = ""

    def __hash__(self) -> int:
        return hash((self.path, self.method, self.filter_id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ApiNode):
            return False
        return (
                self.path == other.path and
                self.method == other.method and
                self.filter_id == other.filter_id
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ApiNode):
            return NotImplemented
        return self.__repr__() < other.__repr__()

    def __repr__(self) -> str:
        return f"{self.method.value} {self.path} {self.filter_id}"

    @property
    def positions(self) -> list[ApiPosition]:
        result = list(
            self._parse_template(self.path)
            + self._parse_template(self.params)
            + self._parse_template(self.json)
            + self._parse_template(self.headers)
            + self._parse_template(self.files)
        )
        match = re.search(r'"Content-Type"\s*:\s*"([^"]+)"', self.headers)
        if match:
            content_type = str(match.group(1))
            if content_type in (
                    ContentType.APPLICATION_JSON,
                    ContentType.MULTIPART_FORM_DATA,
            ):
                result.extend(self._parse_template(self.data))
            if content_type in (
                    ContentType.APPLICATION_OCTET_STREAM,
                    ContentType.APPLICATION_X_WWW_FORM_URLENCODED,
            ):
                result.append(
                    ApiPosition(msgspec.msgpack.encode(self), "d_payload", True)
                )

        return result

    def _parse_template(self, template_str):
        pattern = r"\$\{([^}]+)\}"
        matches: list[str] = re.findall(pattern, template_str)
        result: list[ApiPosition] = []
        for match in matches:
            is_required = True
            # Check whether it ends with a question mark, indicating this position is optional
            if match.endswith("?"):
                match = match[:-1]  # remove the question mark
                is_required = False

            parts = match.split(":", 1)
            result.append(
                ApiPosition(
                    whose=msgspec.msgpack.encode(self),
                    name=parts[0].strip(),
                    is_required=is_required,
                )
            )
        return result

    def auto_fill(self, wordlist: WordList) -> HTTPRequest:
        # TODO: Look up the best-matching parameters in local_wordlist and fill them; currently using random values
        # For now, Solr APIs do not require strictly specified parameter values
        return self.to_request()  # type: ignore

    @staticmethod
    def _fill_template(template_str: str, value_dict: dict[str, Any]) -> str:
        def replace_var(match):
            full_match = match.group(0)  # full matched content
            var_content = match.group(1)
            parts = var_content.split(":", 1)
            name = parts[0].strip()
            default_str = parts[1].strip() if len(parts) > 1 else None
            value = value_dict.get(name, default_str)

            # Determine if the matched content is quoted
            is_quoted = full_match.startswith('"') and full_match.endswith('"')

            if isinstance(value, bool):
                return "true" if value else "false"
            elif value is None:
                return "null"
            elif isinstance(value, (int, float)):
                return str(value)
            elif isinstance(value, str):
                # Handle special string cases
                if value.lower() == "true":
                    return "true"
                elif value.lower() == "false":
                    return "false"
                if is_quoted:
                    return f"\"{json.dumps(value)[1:-1]}\""
                else:
                    return value
            elif isinstance(value, bytes):
                return base64.b64encode(value).decode()
            else:
                return f"\"{str(value)}\""

        return re.sub(r"\"?\$\{([^}]+)\}\"?", replace_var, template_str)

    def to_request(self, value_dict: dict[ApiPosition, Any] = {}):
        for pos in self.positions:
            if pos.is_required and pos not in value_dict:
                return None
        str_dict = {pos.name: value_dict[pos] for pos in value_dict.keys()}
        filled_json = ApiNode._fill_template(self.json, str_dict)
        if filled_json:
            unfilled_optional_params = re.findall(r"\$\{([^}]+\?)\}", filled_json)
            if unfilled_optional_params:
                try:
                    json_dict = json.loads(filled_json)
                    json_dict = self._remove_unfilled_optional_params(
                        json_dict, unfilled_optional_params
                    )
                    filled_json = json.dumps(json_dict)
                except json.JSONDecodeError:
                    logger.error(f"{filled_json} json decode error, set to None")
                    filled_json = None
            if filled_json:
                try:
                    filled_json = json.loads(filled_json.replace("\'", "\""))
                except:
                    filled_json = json.loads(filled_json)
            else:
                filled_json = None

        filled_path = ApiNode._fill_template(self.path, str_dict)
        filled_queries = ApiNode._fill_template(self.params, str_dict)
        params_dict = {}
        if filled_queries:
            unfilled_optional_params = re.findall(r"\$\{([^}]+\?)\}", filled_queries)
            for param in filled_queries.split("&"):
                if any(f"${{{op}}}" in param for op in unfilled_optional_params):
                    continue
                if "=" in param:
                    key, value = param.split("=", 1)
                    params_dict[key] = value

        filled_headers_str = ApiNode._fill_template(self.headers, str_dict)
        if filled_headers_str:
            filled_headers = json.loads(filled_headers_str)
        else:
            filled_headers = None
        filled_files_str = ApiNode._fill_template(self.files, str_dict)
        if filled_files_str:
            filled_files = json.loads(filled_files_str)
        else:
            filled_files = None

        if "d_payload" in str_dict:
            # d_payload defaults to bytes
            filled_data = str_dict["d_payload"]
            # If it's a BASE64-encoded string, convert to bytes
            if isinstance(filled_data, str):
                try:
                    filled_data = base64.b64decode(filled_data.encode())
                except:
                    filled_data = filled_data.encode()
        else:
            filled_data_str = ApiNode._fill_template(self.data, str_dict)
            if filled_data_str:
                filled_data = json.loads(filled_data_str)  # key-values
            else:
                filled_data = None

        return HTTPRequest(
            api=msgspec.msgpack.encode(self),
            method=self.method,
            headers=filled_headers,
            path=filled_path,
            data=filled_data,
            json=filled_json,
            params=None if not params_dict else params_dict,
            files={k: v for k, v in filled_files.items()} if filled_files else None,
        )

    def _remove_unfilled_optional_params(self, json_obj, unfilled_params):
        """Recursively remove key-value pairs in a JSON object that contain unfilled optional parameters."""
        if isinstance(json_obj, dict):
            result = {}
            for key, value in json_obj.items():
                if isinstance(value, str) and any(
                        f"${{{param}}}" in value for param in unfilled_params
                ):
                    continue
                elif isinstance(value, (dict, list)):
                    processed_value = self._remove_unfilled_optional_params(
                        value, unfilled_params
                    )
                    if processed_value:
                        result[key] = processed_value
                else:
                    result[key] = value
            return result
        elif isinstance(json_obj, list):
            result = []
            for item in json_obj:
                if isinstance(item, str) and any(
                        f"${{{param}}}" in item for param in unfilled_params
                ):
                    continue
                elif isinstance(item, (dict, list)):
                    processed_item = self._remove_unfilled_optional_params(
                        item, unfilled_params
                    )
                    if processed_item:
                        result.append(processed_item)
                else:
                    result.append(item)
            return result
        else:
            return json_obj
