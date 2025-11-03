from loguru import logger
import pandas as pd
from sqlalchemy import create_engine
import requests 
from basic.server_state import ServerState

def hc_single(scene) -> bool:
    success = False
    try:

        http_port = scene.target_container['ports'][0]
        response = requests.get(f"http://localhost:{http_port}/auth/signup")
        #print(response.text)
        if response.status_code == 200 and "Sign Up - Appwrite" in response.text:
            success = True
    except (StopIteration, requests.RequestException):
        return False
    return success

def get_state(container_name: str, http_port: int, db_port: int, save_tag = "demo") -> ServerState:
    from basic.table import Table
    
    host = "localhost"
    db = "appwrite"
    db_user = "appwrite"
    db_password = "appwrite"
    

    conn_str = f"mysql+pymysql://{db_user}:{db_password}@{host}:{db_port}/{db}?charset=utf8mb4"
    engine = create_engine(conn_str)

    relevant_tables = [
        'users', 'sessions', 'teams', 'memberships', 
        'projects', 'functions', 'keys', 'tokens'
    ]
    
    all_tables_df = pd.read_sql("SHOW TABLES", engine)
    all_table_names = all_tables_df.iloc[:, 0].tolist()
    
    db_state = []
    
    for table_name in relevant_tables:
        try:
            matching_tables = [
                t for t in all_table_names 
                if t.endswith(f"_{table_name}") or t.endswith(f"_{table_name}_perms")
            ]
            matching_tables = [t for t in matching_tables if not t.endswith("_perms")]
            
            if not matching_tables:
                print(f"Warning: No tables found for {table_name}")
                continue
            
            all_dfs = []
            columns = None
            for actual_table_name in matching_tables:
                try:
                    df = pd.read_sql(f"SELECT * FROM {actual_table_name}", engine)
                    if columns is None:
                        columns = df.columns.tolist()
                    if not df.empty:
                        all_dfs.append(df)
                except Exception as e:
                    print(f"Warning: Failed to read table {actual_table_name}: {e}")
                    continue
            
            if all_dfs:
                merged_df = pd.concat(all_dfs, ignore_index=True)
                merged_df = merged_df.drop_duplicates()
                table = Table.from_pd_dataframe(merged_df, table_name)
                db_state.append(table)
            elif columns is not None:
                empty_df = pd.DataFrame(columns=columns)
                table = Table.from_pd_dataframe(empty_df, table_name)
                db_state.append(table)
                print(f"Info: Created empty table for {table_name}")
            else:
                print(f"Warning: No data and no schema found for table {table_name}")
                
        except Exception as e:
            print(f"Warning: Failed to process table {table_name}: {e}")
            continue
    
    appwrite_state = ServerState(file_state=[], db_state=db_state)
    return appwrite_state

def check_attack(http_port: int, container_id: str, session: requests.Session, db_port: int) -> bool:

    attack_string = "alert(document.location)"
    host = "localhost"
    db = "appwrite"
    db_user = "appwrite"
    db_password = "appwrite"

    try:
        conn_str = f"mysql+pymysql://{db_user}:{db_password}@{host}:{db_port}/{db}?charset=utf8mb4"
        engine = create_engine(conn_str)

        all_tables_df = pd.read_sql("SHOW TABLES", engine)
        all_table_names = all_tables_df.iloc[:, 0].tolist()

        candidate_user_tables = [
            t for t in all_table_names
            if t.startswith("_") and t.endswith("_users") and t != "_console_users"
        ]

        if not candidate_user_tables:
            logger.error("Info: No project-level _<projectid>_users tables found.")
            return False

        for tbl in candidate_user_tables:
            try:
                df = pd.read_sql(f"SELECT * FROM `{tbl}`", engine)
            except Exception as read_err:
                logger.warning(f"Warning: Failed to read table {tbl}: {read_err}")
                continue

            if df.empty:
                continue

            try:
                for row in df.itertuples(index=False):
                    for val in row:
                        if val is None:
                            continue
                        if attack_string in str(val):
                            logger.success(f"Attack detected in table {tbl}: {val}")
                            return True
            except Exception as scan_err:
                logger.warning(f"Warning: Failed scanning table {tbl}: {scan_err}")
                continue

        return False
    except Exception as e:
        logger.error(f"Error in check_attack: {e}")
        return False