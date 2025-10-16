import pandas as pd
from sqlalchemy import create_engine
import requests
from bs4 import BeautifulSoup  
from basic.server_state import ServerState
from docker import DockerClient
import os

def hc_single(scene) -> bool:
    success = False
    try:
        http_port = scene.target_container['ports'][0]
        response = requests.get(f"http://localhost:{http_port}/users/sign_in")
        #print(response.text)
        if response.status_code == 200 and "Sign in · GitLab" in response.text:
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

def get_state(container_name: str, http_port: int, db_port: int, save_tag = "demo") -> ServerState:

    from basic.file_data import FileData
    from basic.table import Table
    
    conn_str = f'postgresql+psycopg2://gitlab:password@localhost:{db_port}/gitlabhq_production'
    engine = create_engine(conn_str)

    users_df = pd.read_sql('SELECT * FROM users where id != 1', engine)
    projects_df = pd.read_sql('SELECT * FROM projects', engine)
    users_table = Table.from_pd_dataframe(users_df, 'users')
    projects_table = Table.from_pd_dataframe(projects_df, 'projects')
    db_state = [users_table, projects_table]

    file_path = "/tmp"
    files = get_files_from_docker(container_name, file_path)
    file_state = []
    for file in files:
        f = FileData(file_path=file_path, file_name=file['file_name'], file_content=file['content'])
        file_state.append(f)
    gitlab_state = ServerState(file_state=file_state, db_state=db_state)
    return gitlab_state

def check_attack(http_port: int, container_id: str, session: requests.Session, dp_port: int) -> bool:
    try:
        base_url = f"http://localhost:{http_port}"
        r8 = session.get(f"{base_url}/hacker/attack_project/import/new")  

        soup8 = BeautifulSoup(r8.text, "html.parser")
        panel_heading = soup8.find("div", class_="panel-heading")  
        panel_body = soup8.find("div", class_="panel-body")  
        pre_block = panel_body.find("pre") if panel_body else None

        if panel_heading and pre_block:  
            if "root:x" in str(panel_body):
                return True
        return False
    except:
        return False