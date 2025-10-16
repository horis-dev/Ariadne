import os
from pathlib import Path
import time
import tomllib
import msgspec
import requests

from basic.http.http_request import HTTPRequest
from basic.server_state import ServerState

def hc_single(scene) -> bool:
    success = False
    try:
        http_port = scene.target_container['ports'][0]

        response = requests.get(f"http://localhost:{http_port}")
        #print(response.text)
        if "\"couchdb\":\"Welcome\"" in response.text:
            success = True

    except (StopIteration, requests.RequestException):
        return False
    
    return success

def get_state(container_name: str, http_port: int, db_port: int = -1, save_tag: str = "demo") -> ServerState:

    import json
    from basic.file_data import FileData
    from basic.table import Table
    
    base_url = f"http://localhost:{http_port}"
    file_state = []
    db_state = []


    
    try:
        try:
            config_response = requests.get(f"{base_url}/_config/query_servers")
            query_server_rows = []
            if config_response.status_code == 200:
                query_servers = config_response.json()
                for name, content in query_servers.items():
                    query_server_rows.append([name, f"\"{content}\""])
            
            query_server_table = Table(
                table_name="query_server",
                is_file=False,
                columns=["name", "content"],
                rows=query_server_rows
            )
            db_state.append(query_server_table)
        except requests.RequestException:
            query_server_table = Table(
                table_name="query_server",
                is_file=False,
                columns=["name", "content"],
                rows=[]
            )
            db_state.append(query_server_table)
        
        database_rows = []
        document_rows = []
        kv_rows = []
        
        try:
            dbs_response = requests.get(f"{base_url}/_all_dbs")
            if dbs_response.status_code == 200:
                all_databases = dbs_response.json()
                
                for db_name in all_databases:
                    database_rows.append([db_name])
                    
                    if db_name.startswith('_'):
                        continue
                    
                    try:
                        docs_response = requests.get(f"{base_url}/{db_name}/_all_docs?include_docs=true")
                        if docs_response.status_code == 200:
                            docs_data = docs_response.json()
                            
                            for doc_row in docs_data.get('rows', []):
                                doc_id = doc_row.get('id', '')
                                doc_key = doc_row.get('key', '')
                                doc_rev = doc_row.get('value', {}).get('rev', '')
                                
                                document_full_name = f"{db_name}.{doc_id}"
                                
                                document_rows.append([document_full_name, db_name, doc_id, doc_rev])
                                
                                doc_content = doc_row.get('doc', {})
                                if doc_content:
                                    for key, value in doc_content.items():
                                        if key.startswith('_'):
                                            continue
                                        
                                        value_str = json.dumps(value) if not isinstance(value, str) else value
                                        
                                        kv_rows.append([key, value_str, document_full_name])
                                        
                    except requests.RequestException:
                        continue
                        
        except requests.RequestException:
            pass
        
        database_table = Table(
            table_name="database",
            is_file=False,
            columns=["database_name"],
            rows=database_rows
        )
        db_state.append(database_table)
        
        document_table = Table(
            table_name="document",
            is_file=False,
            columns=["document_full_name", "database", "document_id", "revision"],
            rows=document_rows
        )
        db_state.append(document_table)
        
        kv_table = Table(
            table_name="kv",
            is_file=False,
            columns=["key", "value", "document"],
            rows=kv_rows
        )
        db_state.append(kv_table)
        
    except requests.RequestException as e:
        print(f"无法连接到CouchDB服务器: {e}")
        
        empty_tables = [
            Table("query_server", False, ["name", "content"], []),
            Table("database", False, ["database_name"], []),
            Table("document", False, ["document_full_name", "database", "document_id", "revision"], []),
            Table("kv", False, ["key", "value", "document"], [])
        ]
        db_state.extend(empty_tables)
        
    return ServerState(
        file_state=file_state,
        db_state=db_state
    )
    
def check_attack(http_port: int, container_id: str, session: requests.Session, db_port: int) -> bool:

    time.sleep(1)
    import subprocess
    try:
        session.post(
            url=f"http://localhost:{http_port}/vultest/_temp_view?limit=10",
            json={
                "language": "cmd",
                "map": ""
            }
        )
        result = subprocess.run(
            ["docker", "exec", container_id, "test", "-f", "/tmp/success"],
            capture_output=True,
            timeout=10
        )
        
        return result.returncode == 0
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return False
