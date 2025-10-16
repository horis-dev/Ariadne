import pandas as pd
from sqlalchemy import create_engine
import requests
from bs4 import BeautifulSoup  
from basic.server_state import ServerState
from docker import DockerClient
import subprocess
import pandas as pd
import io
import shlex
from typing import Optional 
from loguru import logger

def hc_single(scene) -> bool:
    success = False
    try:
        http_port = scene.target_container['ports'][0]
        response = requests.get(f"http://localhost:{http_port}/users/sign_in")
        if response.status_code == 200 and "Sign in · GitLab" in response.text:
            success = True

    except (StopIteration, requests.RequestException):
        return False
    
    return success

def query_gitlab_pg_via_docker(
    sql: str = "SELECT name, path FROM projects;",
    container: str = "gitlab14",
    db: str = "gitlabhq_production",
    user: str = "gitlab",
    password: Optional[str] = "gitlab",
    host: str = "127.0.0.1",
    use_tcp: bool = True,
    timeout: Optional[int] = None,
    encoding: str = "utf-8",
) -> pd.DataFrame:

    copy_sql = f"COPY ({sql.rstrip(';')}) TO STDOUT WITH CSV HEADER;"

    inner_cmd = ["psql", "-U", user, "-d", db, "-c", copy_sql]
    if use_tcp:
        inner_cmd[1:1] = ["-h", host]  # 在 -U 前插入 -h host

    if password is not None:
        inner_shell = f"PGPASSWORD={shlex.quote(password)} " + " ".join(
            shlex.quote(arg) for arg in inner_cmd
        )
    else:
        inner_shell = " ".join(shlex.quote(arg) for arg in inner_cmd)

    docker_cmd = ["docker", "exec", "-i", container, "bash", "-lc", inner_shell]

    proc = subprocess.run(
        docker_cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding=encoding,
    )

    if proc.returncode != 0:
        err = proc.stderr.strip()
        out = proc.stdout.strip()
        cmd_str = " ".join(shlex.quote(x) for x in docker_cmd)
        raise subprocess.CalledProcessError(
            proc.returncode,
            cmd_str,
            output=out,
            stderr=err or out,
        )

    csv_text = proc.stdout

    df = pd.read_csv(io.StringIO(csv_text))
    return df

def get_state(container_name: str, http_port: int, save_tag = "demo") -> ServerState:
    from basic.table import Table

    # 提取 users 表和 projects 表
    projects_df = query_gitlab_pg_via_docker(sql = "SELECT name, path FROM projects", container = container_name)
    projects_table = Table.from_pd_dataframe(projects_df, 'projects')

    fork_df = query_gitlab_pg_via_docker(sql = "SELECT project_id, forked_from_project_id  FROM fork_network_members", container = container_name)
    #处理fork_network_members表, 将id数值都转为str
    def _to_str_or_none(x):
        if pd.isna(x):
            return None
        return str(int(x)) if isinstance(x, float) and x.is_integer() else str(x)
    fork_df = fork_df.apply(lambda s: s.map(_to_str_or_none))
    fork_table = Table.from_pd_dataframe(fork_df, 'fork_network_members')

    db_state = [projects_table, fork_table]
    gitlab_state = ServerState(file_state=[], db_state=db_state)
    return gitlab_state

def get_fork_project_ids(container_name: str, http_port: int, db_port: int) -> list[str]:

    id_list = []
    #fork_df = query_gitlab_pg_via_docker(sql = "SELECT project_id FROM fork_network_members", container = container_name)
    fork_df = query_gitlab_pg_via_docker(sql = "SELECT id FROM projects WHERE id != 1", container = container_name)
    id_list = fork_df['id'].tolist()
    return id_list

def check_attack(http_port: int, container_id: str, session: requests.Session, dp_port: int) -> bool:
    try:
        # 获取项目 fork 关系的项目 id 列表
        id_list = get_fork_project_ids(container_id, http_port, dp_port)
        logger.warning(f"{id_list}")
        headers = {
            "Authorization": "Bearer z5DDDf8efs7dH_62qTfi"
        }
        # 将 id 列表中的项目两两进行fork, 检查500响应
        for i in range(len(id_list)):
            for j in range(len(id_list)):
                if id_list[i] == id_list[j]:
                    continue
                url = f"http://localhost:{http_port}/api/v4/projects/{id_list[i]}/fork/{id_list[j]}"
                response = requests.post(url, headers=headers)
                if response.status_code == 500:
                    logger.success(f"{url}")
                    return True
        return False
    except:
        return False