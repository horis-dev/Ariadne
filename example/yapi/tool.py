import pymongo
import requests
from docker import DockerClient
from basic.server_state import ServerState
from basic.table import Table


def get_state(container_name: str, http_port: int, db_port: int, save_tag = "demo") -> ServerState:

    MONGO_URI = f"mongodb://root:root@localhost:{db_port}" 
    client = pymongo.MongoClient(MONGO_URI)
    db = client["yapi"]
    collection_names = db.list_collection_names()
    used_by_fuzzer = set([
        "user",
        "group",
        "project",
        "interface",
        "interface_cat",
        "interface_col",
        "interface_case",
        "follow",
        "adv_mock"
    ])
    
    db_state = []
    for collection_name in collection_names:
        if collection_name not in used_by_fuzzer:
            continue
        
        collection = db[collection_name]
        cursor = collection.find()

        documents = list(cursor)
        
        if not documents:
            continue
            
        columns = set()
        generative_cols = [
            "_id",
            "__v",
            "project_id",
            "uid",
            "catid",
            "edit_uid",
        ]
        
        def extract_columns(obj, prefix=""):
            result = set()
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in generative_cols:
                        continue
                    
                    col_name = f"{prefix}{key}" if prefix else key
                    result.add(col_name)
                    
                    if isinstance(value, dict):
                        nested_columns = extract_columns(value, f"{col_name}.")
                        result.update(nested_columns)
            return result
                
        for doc in documents:
            columns.update(extract_columns(doc))
            
        for generative_col in generative_cols:
            if generative_col in columns:
                columns.remove(generative_col)
                
        columns = sorted(list(columns))

        rows = []
        for doc in documents:
            row = []
            
            def get_nested_value(obj, path):
                parts = path.split(".", 1)
                key = parts[0]
                
                if key not in obj:
                    return None
                
                value = obj[key]
                
                if len(parts) == 1:
                    return value
                
                if isinstance(value, dict):
                    return get_nested_value(value, parts[1])
                
                return None
                
            for col in columns:
                if "." in col:
                    value = get_nested_value(doc, col)
                else:
                    value = doc.get(col, None)
                
                if isinstance(value, (str, int, float, bool)) or value is None:
                    row.append(value)
                else:
                    row.append(str(value))
            rows.append(row)

        table = Table(
            table_name=collection_name,
            is_file=False,
            columns=columns,
            rows=rows
        )
        db_state.append(table)
    
    return ServerState(
        file_state=[],
        db_state=db_state
    )

def try_each(app_port: int, db_port: int, session: requests.Session):
    MONGO_URI = f"mongodb://root:root@localhost:{db_port}" 
    client = pymongo.MongoClient(MONGO_URI)
    db = client["yapi"]

    projects = list(db['project'].find())
    interfaces = list(db['interface'].find())
    project_id_path: list[tuple[int, str]] = []
    interface_path: list[str] = []
    # project
    for project in projects:
        project_id_path.append(
            (
                project['_id'],
                project['basepath']
            )
        )
    for interface in interfaces:
        print(interface)
        interface_path.append(interface['path'])

    # 忽略异常
    try:
        for project_id, basepath in project_id_path:
            for path in interface_path:
                rsp = session.get(
                    url=f"http://localhost:{app_port}/mock/{project_id}{basepath}{path}"
                )
                print(f"GET http://localhost:{app_port}/mock/{project_id}{basepath}{path} ---> " + str(rsp.status_code) + rsp.text)
    except:
        pass
    
    
def check_attack(port: int, container_id: str, session: requests.Session, db_port: int) -> bool:

    try_each(port, db_port, session)
    try:
        client = DockerClient.from_env()
        container = client.containers.get(container_id)
        exec_result = container.exec_run(
            cmd=["test", "-f", "/tmp/success"],
            demux=False,
            tty=False
        )
        return exec_result.exit_code == 0
        
    except Exception as e:
        print(f"{str(e)}")
        return False
    

def hc_single(scene) -> bool:
    try:
        http_port = scene.target_container['ports'][0]
        response = requests.get(f"http://localhost:{http_port}")
        #print(response.text)
        if response.status_code in set([200, 201, 203]):
            return True
        else:
            return False
    except:
        return False