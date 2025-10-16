import os
import subprocess
from pathlib import Path
import time
import tomllib
import docker
import msgspec
import requests

from basic.file_data import FileData
from basic.http.http_request import HTTPRequest
from basic.http.request_sequence import RequestSequence
from basic.server_state import ServerState
from basic.table import Table
# from dataold import Table

from word_lib import WordLib


def get_files_from_docker(container_name, file_path):
    """
    Read the specified file content inside a Docker container and return the content as bytes.
    """
    cmd = ['docker', 'exec', container_name, 'cat', file_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        s = result.stdout
        return s.encode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"Read failed: {e}")
        return b''


import os
import docker


def get_recently_modified_files_and_folders(container_name, directory, modified_within_minutes=60):
    """
    Get recently modified files and directories from a Docker container.

    :param container_name: Container name or ID
    :param directory: Directory to traverse
    :param modified_within_minutes: Only include files/dirs modified within the last N minutes
    :return: List[Dict] containing file names and content (directory content is empty bytes)
    """
    client = docker.DockerClient.from_env()
    container = client.containers.get(container_name)

    # Check whether the directory exists
    check_cmd = f'ls "{directory}"'
    check_result = container.exec_run(check_cmd)
    if check_result.exit_code != 0:
        return []

    results = []

    # Get recently modified files
    file_cmd = f'find {directory} -maxdepth 1 -type f -mmin -{modified_within_minutes}'
    files = container.exec_run(file_cmd)
    file_list = files.output.decode().strip().split('\n')

    for file_path in file_list:
        if not file_path.strip():
            continue
        cat_cmd = f'cat "{file_path}"'
        file_content = container.exec_run(cat_cmd, demux=True)
        content_bytes = file_content.output[0] if file_content.output else b''
        file_name = os.path.basename(file_path)
        results.append({'file_name': file_name, 'content': content_bytes})

    # Get recently modified directories (excluding the directory itself)
    dir_cmd = (
        f'find {directory} -maxdepth 1 -type d ! -path "{directory}" -mmin -{modified_within_minutes}'
    )
    dirs = container.exec_run(dir_cmd)
    dir_list = dirs.output.decode().strip().split('\n')

    for dir_path in dir_list:
        if not dir_path.strip():
            continue
        dir_name = os.path.basename(dir_path)
        results.append({'file_name': dir_name, 'content': b''})

    return results


def get_files_and_folders_from_docker(container_name, directory):
    client = docker.DockerClient.from_env()
    container = client.containers.get(container_name)

    check_cmd = f'ls "{directory}"'
    check_result = container.exec_run(check_cmd)
    if check_result.exit_code != 0:
        return []

    # Get all files in the directory
    file_cmd = f'find {directory} -maxdepth 1 -type f'
    files = container.exec_run(file_cmd)
    file_list = files.output.decode().strip().split('\n')

    # Get all subdirectories (excluding the directory itself)
    dir_cmd = f'find {directory} -maxdepth 1 -type d ! -path {directory}'
    dirs = container.exec_run(dir_cmd)
    dir_list = dirs.output.decode().strip().split('\n')

    results = []

    # Files section
    for file_path in file_list:
        if not file_path.strip():
            continue
        cat_cmd = f'cat {file_path}'
        file_content = container.exec_run(cat_cmd, demux=True)
        content_bytes = file_content.output[0] if file_content.output else b''
        file_name = os.path.basename(file_path)
        results.append({'file_name': file_name, 'content': content_bytes})

    # Directories section, content marked as empty
    for dir_path in dir_list:
        if not dir_path.strip():
            continue
        dir_name = os.path.basename(dir_path)
        results.append({'file_name': dir_name, 'content': b''})

    return results


def get_state(container_name: str, http_port: int = 0, db_port: int = 0, save_tag="demo") -> ServerState:
    from basic.file_data import FileData

    file_path = "/var/www/html/include/taglib"
    files = get_recently_modified_files_and_folders(container_name, file_path)
    file_state = []
    for file in files:
        f = FileData(file_path=file_path, file_name=file['file_name'], file_content=file['content'])
        file_state.append(f)

    db_state = []
    # Container ID
    container_id = container_name

    # MySQL login info
    mysql_user = "root"
    mysql_password = "123456"
    database_name = "dedecmsv57utf8sp1"

    # SQL statement
    # sql = "SELECT userid FROM dede_admin;"
    sql = "SELECT logintime FROM dede_admin;"

    # Build docker exec command
    cmd = [
        "docker", "exec", container_id,
        "mysql", f"-u{mysql_user}", f"-p{mysql_password}",
        database_name, "-e", sql
    ]

    try:
        # Execute command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        raw_result = result.stdout.split('\n')
        result = [item for item in raw_result if item.strip()]
        column = result[0]
        if len(result) > 1:
            row = result[1]
        else:
            row = ''
        # table = Table('dede_admin',False,[column], [[row]])
        if row == '1622102347':
            row = 0
        else:
            row = 1
        table = Table('dede_admin', False, ['if_login'], [[row]])
        db_state.append(table)

    except subprocess.CalledProcessError as e:
        print("❌ Execution failed:")
        print(e.stderr)

    state = ServerState(file_state=file_state, db_state=db_state)
    return state


def hc_single(scene) -> bool:
    success = False
    try:
        # print('ports:',scene.target_container['ports'])
        # Get HTTP port
        # http_port = next(
        #     p for p in scene.target_container['ports']
        # )['host_port']
        http_port = scene.target_container['ports'][0]

        response = requests.get(f"http://localhost:{http_port}/dede/login.php")
        # print(response.text)
        if response.status_code == 200:
            return True

    except (StopIteration, requests.RequestException):
        return False

    return success


def get_state_old(container_name: str, http_port=None, save_tag=None) -> ServerState:
    file_path_list = [
        '/var/www/html/include/taglib/test.lib.php'
    ]
    db_path_list = [
    ]

    state = ServerState(file_state=[], db_state=[])

    # Files section
    for file_path in file_path_list:
        if not file_path.strip():
            continue
        file_content = get_files_from_docker(container_name, file_path)
        f = FileData(
            file_path=file_path,
            file_name=file_path,
            file_content=file_content
        )
        state.file_state.append(f)

    return state


# print(get_state('74ff9a1abd8c3f5d617ba553f4fe6a30829ca693a9bdc776c7ed8b68d4747e2b'))

def check_attack(http_port, container_name, seed_session, db_port):
    modified_within_minutes = 60
    directory = "/var/www/html/include/taglib/"
    client = docker.DockerClient.from_env()
    container = client.containers.get(container_name)
    aim_ip = "localhost"
    # aim_ip = "192.168.50.128"

    # Check whether the directory exists
    check_cmd = f'ls "{directory}"'
    check_result = container.exec_run(check_cmd)
    if check_result.exit_code != 0:
        return []

    # Get recently modified files
    file_cmd = f'find {directory} -maxdepth 1 -type f -mmin -{modified_within_minutes}'
    files = container.exec_run(file_cmd)
    file_list = files.output.decode().strip().split('\n')
    for file in file_list:
        # resp = seed_session.request(
        #     method='GET',
        #     url=f"http://localhost:{http_port}/{file}",
        # )
        file_name = os.path.basename(file)
        resp = requests.get(f'http://{aim_ip}:{http_port}/include/taglib/{file_name}')
        if resp.status_code == 200 and int(resp.headers.get('Content-Length')) > 100:
            return True
    return False
