import pandas as pd
import requests
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
        inner_cmd[1:1] = ["-h", host]


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

    projects_df = query_gitlab_pg_via_docker(sql = "SELECT name, path FROM projects;", container = container_name)
    projects_table = Table.from_pd_dataframe(projects_df, 'projects')

    keys_df = query_gitlab_pg_via_docker(sql = "SELECT key, title FROM keys;", container = container_name)
    keys_table = Table.from_pd_dataframe(keys_df, 'keys')

    db_state = [projects_table, keys_table]
    gitlab_state = ServerState(file_state=[], db_state=db_state)
    return gitlab_state

def get_key_titles(container_name: str, http_port: int, db_port: int) -> list[str]:

    title_list = []
    keys_df = query_gitlab_pg_via_docker(sql = "SELECT key, title FROM keys;", container = container_name)
    title_list = keys_df['title'].tolist()
    return title_list

def check_attack(http_port: int, container_id: str, session: requests.Session, dp_port: int) -> bool:
    try:
        title_list = get_key_titles(container_id, http_port, dp_port)
        for title in (title_list):
            if "<script>alert(document.domain)</script>" in title:
                return True
        return False
    except Exception as e:
        return False