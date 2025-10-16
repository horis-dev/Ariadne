from __future__ import annotations
from functools import cache
import requests
import re
from loguru import logger
from typing import Any, Callable, Dict, List, Union
from bs4 import BeautifulSoup
from basic.fuzzword import FuzzWord, MutateValue
from basic.position import ApiPosition, ResponsePosition
from basic.table import Table
from math import exp, sin, cos, log, sqrt
import numexpr as ne

def json2table(obj: Any, table_name: str, is_file: bool = False) -> Table:
    flattened: Dict[str, Any] = flatten_json(obj)
    table = Table(
        table_name, is_file, list(flattened.keys()), [list(flattened.values())]
    )
    return table

@cache
def str2func(expression: str) -> Callable[[float], float]:
    allowed_names = {
        "exp": exp,
        "sin": sin,
        "cos3": cos,
        "log": log,
        "sqrt": sqrt,
    }

    def func(x: float) -> float:
        local_namespace = {"x": x, **allowed_names}
        try:
            result = eval(expression, {"__builtins__": {}}, local_namespace)
        except Exception as e:
            raise ValueError(f"无法计算表达式 '{expression}': {e}")
        return float(result)

    return func


def flatten_json(json_obj: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """
    将 JSON 对象扁平化，支持嵌套列表的展开。

    :param json_obj: 原始 JSON 对象
    :param prefix: 当前的键前缀
    :return: 扁平化的 JSON 字典
    """
    flat_dict = {}

    for key, value in json_obj.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):  # 递归处理嵌套字典
            flat_dict.update(flatten_json(value, full_key))

        elif isinstance(value, list):  # 递归处理列表
            for i, item in enumerate(value):
                sub_key = f"{full_key}[{i}]"
                if isinstance(item, (int, float, str)):  # 直接存储基本类型
                    flat_dict[sub_key] = item
                elif isinstance(item, dict):  # 递归处理字典
                    flat_dict.update(flatten_json(item, sub_key))
                elif isinstance(item, list):  # 递归处理嵌套列表
                    flat_dict.update(flatten_json({sub_key: item}, ""))

        else:  # 直接存储基本类型
            flat_dict[full_key] = value

    return flat_dict


def html_2_json(html_str):
    soup = BeautifulSoup(html_str, "html.parser")
    result = {}

    # 1. 提取常见meta中的CSRF
    metas = soup.find_all("meta")
    csrf_meta = [
        meta
        for meta in metas
        if meta.get("name", "").lower()
        in {"csrf-token", "csrf_token", "_csrf", "xsrf-token", "x-csrf-token"}
    ]
    for meta in csrf_meta:
        result["csrf_token"] = meta.get("content")

    # 2. 提取input里的CSRF等安全信息
    # 常见key列表，可自行扩展
    csrf_input_names = [
        "csrfmiddlewaretoken",
        "_csrf",
        "csrf_token",
        "csrf",
        "authenticity_token",
        "xsrf-token",
        "token",
        "requesttoken",
        "__c"
    ]
    for name in csrf_input_names:
        inp = soup.find("input", {"name": name})
        if inp and inp.get("value"):
            result["csrf_token"] = inp["value"]
            break  # 一旦找到就停止

    # 3. 针对形如<input name="project[namespace_id]" ...>等key-value对
    # 提取所有input带有value键的
    for inp in soup.find_all("input"):
        name = inp.get("name")
        value = inp.get("value")
        if name and value:
            # 如 name="project[namespace_id]"
            if "[" in name and "]" in name:
                key = name.split("[")[-1].replace("]", "")
                result[key] = value
            elif "token" in name.lower() or "id" in name.lower():
                # 例如 input name="user_id"
                result[name] = value

    # 4. 提取html文本中的JS对象：如 "csrfToken": "xxxx"、'csrfToken': 'xxxx'
    pattern_list = [
        r'"csrfToke[n]?"\s*:\s*["\']([^"\']+)["\']',  # "csrfToken": "xxx"
        r'name="_csrf"\s+value="([a-zA-Z0-9_\-]+)"',  # name="_csrf" value="xxx"
        r'name="csrfmiddlewaretoken"\s+value="([a-zA-Z0-9_\-]+)"',  # Django
        r'"x-csrf-token"\s*:\s*"([^"]+)"',
        r'"authenticity_token"\s*:\s*"([^"]+)"',
        r'CSRF\s*=\s*"([^"]+)"',
        r'__c=([A-Za-z0-9]+)',
    ]
    for pattern in pattern_list:
        m = re.search(pattern, html_str, re.IGNORECASE)
        if m:
            result["csrf_token"] = m.group(1)
            break

    # 5. 其它常见场景可按此方式随时扩展...

    # 6. 可自定义添加其它关键字段提取，比如namespace_id
    namespace_input = soup.find("input", {"name": "project[namespace_id]"})
    if namespace_input and namespace_input.get("value"):
        result["namespace_id"] = namespace_input["value"]

    # 7. 提取hidden input常见参数
    for inp in soup.find_all("input", {"type": "hidden"}):
        if inp.get("name") and inp.get("value"):
            if inp.get("name") not in result:
                result[inp.get("name")] = inp.get("value")

    # 返回dict或json字符串，按需选择
    return result  # 若要返回json: json.dumps(result, ensure_ascii=False, indent=2)


def response2fuzzwords(
    response: requests.Response, api: bytes = b"unknown"
) -> List[FuzzWord]:
    """将响应内容转换为FuzzWord"""
    # logger.debug(f"将{response.text}转为fuzzwords")
    fuzzwords = []
    if not response.text or not response:
        return fuzzwords
    content_type = response.headers.get("Content-Type", "").lower()
    if content_type.startswith("text/html"):
        response_json = html_2_json(response.text)
    else:
        response_json = response.json()
        if not isinstance(response_json, dict):
            response_json = {"RAW_RESPONSE": response.text}
    flat_json = flatten_json(response_json)

    for position, value in flat_json.items():
        if value is None or value=="":
            continue
        fuzzword = FuzzWord(
            value=value,
            position=ResponsePosition(where=position, type="HTTP", from_api=api),
        )
        fuzzwords.append(fuzzword)
    return fuzzwords

def string_to_function(expression_str, var_name="x"):
    def func(x):
        # Create a local dictionary with the variable
        local_dict = {var_name: x}
        return ne.evaluate(expression_str, local_dict=local_dict)

    return func

def get_real_value_dict(
    raw_value_dicts: Dict[ApiPosition, MutateValue],
    local_wordlib: Dict[int, Dict[ApiPosition, list[Any]]],
) -> Dict[ApiPosition, Any]:
    """
    获取真实值字典,用于ApiNode转为HTTPRequest
    """
    real_value_dict = {}
    for api_position, mutate_value in raw_value_dicts.items():
        if mutate_value.is_ref:
            api_index = mutate_value.api_index
            pos = mutate_value.pos
            if pos in local_wordlib[api_index]:
                real_value_dict[api_position] = local_wordlib[api_index][pos][0]
            else:
                logger.warning(
                    f"Cannot find value for {pos} in local_wordlib[{api_index}]"
                )
                real_value_dict[api_position] = "null"
        else:
            real_value_dict[api_position] = mutate_value.val
    return real_value_dict


def update_local_word_lib(
    local_word_lib: Any,
    api_index: int,
    api_pos_values: dict,
    resp_words: list[FuzzWord],
):
    """
    原地更新 local_word_lib，增加指定 api_index 的局部语料数据

    :param local_word_lib: dict[int, dict[Position, list]]
    :param api_index: int，从1开始递增的API编号
    :param api_pos_values: list of (ApiPosition, value)
    :param resp_pos_values: list of (ResponsePosition, value)
    """
    local_word_lib[api_index] = {}
    pos_value_dict = api_pos_values
    for word in resp_words:
        pos_value_dict[word.position] = word.value

    for position, value in pos_value_dict.items():
        if position not in local_word_lib[api_index]:
            local_word_lib[api_index][position] = []
        if value not in local_word_lib[api_index][position]:
            local_word_lib[api_index][position].append(value)
