import pandas as pd
from sqlalchemy import create_engine
import requests 
from basic.server_state import ServerState

def hc_single(scene) -> bool:
    success = False
    try:

        http_port = scene.target_container['ports'][0]
        response = requests.get(f"http://localhost:{http_port}/index.php")
        #print(response.text)
        if response.status_code == 200 and "How CMSMS Works" in response.text:
            success = True

    except (StopIteration, requests.RequestException):
        return False
    
    return success

def get_state(container_name: str, http_port: int, db_port: int, save_tag = "demo") -> ServerState:
    from basic.table import Table

    conn_str = f"mysql+pymysql://root:root@localhost:{db_port}/cmsms?charset=utf8mb4"
    engine = create_engine(conn_str)

    #cms_layout_templates_df = pd.read_sql("SELECT * FROM cms_layout_templates WHERE id = 10 LIMIT 1", engine)
    cms_layout_templates_df = pd.read_sql("SELECT * FROM cms_layout_templates", engine)
    cms_layout_templates = Table.from_pd_dataframe(cms_layout_templates_df, 'cms_layout_templates')
    
    db_state = [cms_layout_templates]
    file_state = []

    cmsms_state = ServerState(file_state=file_state, db_state=db_state)
    return cmsms_state

def check_attack(http_port: int, container_id: str, session: requests.Session, db_port: int) -> bool:
    try:
        url = f"http://localhost:{http_port}/index.php"
        res = session.get(url)  
        if "ATTACK" in res.text:
                return True
        return False
    except:
        return False