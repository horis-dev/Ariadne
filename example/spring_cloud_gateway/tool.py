from loguru import logger
import requests

from basic.server_state import ServerState

def hc_single(scene) -> bool:
    success = False
    try:

        http_port = scene.target_container['ports'][0]

        response = requests.get(f"http://localhost:{http_port}/actuator/health")
        #print(response.text)
        if response.json()["status"] == "UP":
            success = True

    except (StopIteration, requests.RequestException):
        return False
    
    return success

def get_state(container_name: str, http_port: int, save_tag: str = "demo") -> ServerState:

    from basic.table import Table
    
    base_url = f"http://localhost:{http_port}"
    file_state = []
    db_state = []

    try:
        routes_response = requests.get(f"{base_url}/actuator/gateway/routes")
        if routes_response.status_code == 200:
            routes_data = routes_response.json()
            logger.debug(f"routes_data={routes_data}")
            routes_rows = []
            filters_rows = []
            
            for route in routes_data:
                routes_rows.append([
                    route.get("route_id", ""),
                    route.get("predicate", ""),
                    route.get("uri", ""),
                    str(route.get("order", 0))
                ])
                
                route_id = route.get("route_id", "")
                filters = route.get("filters", [])
                for filter_item in filters:
                    filters_rows.append([str(filter_item), route_id])
            
            routes_table = Table(table_name="routes", is_file=False, columns=["id", "predicate", "uri", "order"], rows=routes_rows)
            db_state.append(routes_table)
            

            filters_table = Table(table_name="filters", is_file=False, columns=["value", "route_id"], rows=filters_rows)
            db_state.append(filters_table)

        metrics_response = requests.get(f"{base_url}/actuator/metrics")
        if metrics_response.status_code == 200:
            metrics_data = metrics_response.json()
            metrics_rows = []
            for metric_name in metrics_data.get("names", []):
                metrics_rows.append([metric_name])
            
            metrics_table = Table(table_name="metrics", is_file=False, columns=["name"], rows=metrics_rows)
            db_state.append(metrics_table)

        def flatten_json(data, parent_key='', sep='.'):

            items = []
            if isinstance(data, dict):
                for k, v in data.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_json(v, new_key, sep).items())
                    else:
                        items.append((new_key, str(v)))
            return dict(items)

        configs_response = requests.get(f"{base_url}/actuator/configprops")
        if configs_response.status_code == 200:
            configs_data = configs_response.json()
            flattened_configs = flatten_json(configs_data)
            configs_rows = [[k, v] for k, v in flattened_configs.items()]
            
            configs_table = Table(table_name="configs", is_file=False, columns=["key", "value"], rows=configs_rows)
            db_state.append(configs_table)


        env_response = requests.get(f"{base_url}/actuator/env")
        if env_response.status_code == 200:
            env_data = env_response.json()
            flattened_env = flatten_json(env_data)
            env_rows = [[k, v] for k, v in flattened_env.items()]
            
            envs_table = Table(table_name="envs", is_file=False, columns=["key", "value"], rows=env_rows)
            db_state.append(envs_table)

    except requests.RequestException as e:
        print(f"Error fetching data from {base_url}: {e}")

    return ServerState(file_state=file_state, db_state=db_state)
    
def check_attack(port: int, container_id: str, session: requests.Session) -> bool:
    response = session.get(f"http://localhost:{port}/actuator/gateway/routes/hacktest")
    if "uid=0(root) gid=0(root)" in response.text:
        return True
    return False