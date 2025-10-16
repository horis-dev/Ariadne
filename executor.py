import concurrent.futures
import importlib
import json
import os
import subprocess
import threading
import time
from typing import Callable
import requests

import msgspec
from docker import DockerClient
from loguru import logger
from tqdm import tqdm

from basic.exception import Api2HTTPRequestError
from basic.seed import SeedInput
from basic.server_state import ServerState
from code_cov_calc import Code_Coverage
from util.util import response2fuzzwords, update_local_word_lib, get_real_value_dict
from word_lib import LocalWordlib

# from logcapture import start_sysdig_log, kill_sysdig_processes, analysis_sysdig

client = DockerClient.from_env()


class ExecuteResult(msgspec.Struct, tag="execute_result_new_dev"):
    seed_id: int
    local_wordlib: LocalWordlib = {}
    current_state: ServerState = None
    distance_delta: float = 0.0
    code_coverage_delta: float = 0.0
    new_response_delta: float = 0.0
    finish_time: float = time.time()
    is_attack_success: bool = False
    is_2xx_response: bool = False


class sa_ExecuteResult(msgspec.Struct, tag="sa_execute_result"):
    seed_id: int
    orig_perf_score: float
    new_perf_score: float
    code_coverage_delta: float
    new_response_delta: float
    is_2xx_response: bool
    cur_weight: float
    current_state: ServerState


global_lock = threading.Lock()
global_stop = False


class Scene:
    def __init__(self, compose_path, project_name, target_service: str = "solr", hc_pre_wait=5, hc_max_retries=30,
                 hc_interval=3):
        self.compose_path = compose_path
        self.project_name = project_name
        self.target_service = target_service  # target service keyword
        self.status = "available"
        self.lock = threading.Lock()
        self.event = threading.Event()
        self.target_container = None  # store target container info
        self.example_module_path = f"example.{self.target_service.split('-')[0]}.tool"
        self.health_check_func: Callable = None
        self.tool_module = None
        self.hc_pre_wait = hc_pre_wait
        self.hc_max_retries = hc_max_retries
        self.hc_interval = hc_interval
        self._load_health_check()
        # self.start()

    def start(self):
        """Start the scene and perform a health check"""
        with self.lock:
            self.status = "starting"

        try:
            # start docker-compose services
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    self.compose_path,
                    "-p",
                    self.project_name,
                    "up",
                    "-d",
                ],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # fetch container info
            self._update_container_info()

            if "airflow" in self.target_service:
                self.reset_airflow()

            # perform health check
            success = self._perform_health_check()

            with self.lock:
                self.status = "available" if success else "pending_reset"
            return True
        except subprocess.CalledProcessError as e:
            logger.exception(f"[{self.project_name}] start exception: {e}")
            with self.lock:
                self.status = "pending_reset"
            return False

    def _load_health_check(self):
        """Dynamically load the health check function"""
        try:
            # dynamically import target module
            module = importlib.import_module(self.example_module_path)
        except ModuleNotFoundError:
            raise RuntimeError(f"Example module not found: {self.example_module_path}")

        try:
            # import health check function
            self.health_check_func = getattr(module, "hc_single")
            self.tool_module = module
        except AttributeError:
            raise RuntimeError(f"Health check function not found in module {self.example_module_path}")

    def _perform_health_check(self):
        """Run health checks"""
        for _ in range(self.hc_max_retries):
            if not self.target_container:
                self.event.wait(self.hc_interval)
                continue
            success = self.health_check_func(scene=self)
            if success:
                return True
            if _ == 0:
                self.event.wait(self.hc_pre_wait)
            else:
                self.event.wait(self.hc_interval)
        return False

    def reset(self):
        """Reset the scene"""
        try:
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    self.compose_path,
                    "-p",
                    self.project_name,
                    "kill",
                ],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    self.compose_path,
                    "-p",
                    self.project_name,
                    "down",
                    "-v",
                ],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            global global_lock, global_stop

            with global_lock:
                if global_stop:
                    return

            subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    self.compose_path,
                    "-p",
                    self.project_name,
                    "up",
                    "-d",
                ],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._update_container_info()
        except subprocess.CalledProcessError:
            logger.exception(f"[{self.project_name}] reset failed")

    def reset_airflow(self):
        """Reset airflow-related services"""
        try:
            subprocess.run(
                [
                    "docker", "compose",
                    "-f", self.compose_path,
                    "-p", self.project_name,
                    "stop",
                    "airflow-webserver",
                    "airflow-scheduler",
                    "airflow-worker"
                ],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                [
                    "docker", "compose",
                    "-f", self.compose_path,
                    "-p", self.project_name,
                    "run", "--rm", "reset"
                ],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                [
                    "docker", "compose",
                    "-f", self.compose_path,
                    "-p", self.project_name,
                    "restart",
                    "airflow-webserver",
                    "airflow-scheduler",
                    "airflow-worker"
                ],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._update_container_info()
        except subprocess.CalledProcessError:
            logger.exception(f"[{self.project_name}] airflow reset failed")

    def _update_container_info(self, prewaitime=2.5):
        """Update target scene info"""
        self.event.wait(prewaitime)
        try:
            containers = client.containers.list(
                filters={"label": f"com.docker.compose.project={self.project_name}"}
            )

            # filter containers that contain the target keyword
            target_containers = [c for c in containers if self.target_service in c.name]

            if not target_containers:
                logger.warning(
                    f"[{self.project_name}] target scene with keyword {self.target_service} not found"
                )
                return

            container = target_containers[0]
            container.reload()

            # web service port mappings
            ports = set()
            ports_info = container.attrs["NetworkSettings"]["Ports"]
            for host_ports in ports_info.values():
                if host_ports:
                    for host_port_info in host_ports:
                        ports.add(host_port_info["HostPort"])
            ports = list(ports)

            # database port mappings (if any)
            db_keywords = ('mysql', 'postgres', 'mongo')  # customizable
            db_containers = [
                c for c in containers
                if any(k in c.name.lower() for k in db_keywords)
            ]

            self.target_container = {
                "name": container.name,
                "id": container.id[:12],
                "ports": ports
            }
            db_container_id = None
            db_port = None
            if db_containers:
                db_container = db_containers[0]
                db_container.reload()
                db_container_id = db_container.id

                db_ports_info = db_container.attrs["NetworkSettings"]["Ports"]
                common_db_ports = ('3306', '5432', '27017')
                for container_port, host_ports in db_ports_info.items():
                    port_num = container_port.split("/")[0]
                    if port_num in common_db_ports and host_ports:
                        db_port = host_ports[0]["HostPort"]  # take the first mapping only
                        break
                self.target_container["db_id"] = db_container_id[:12]
                self.target_container["db_port"] = db_port

        except Exception as e:
            logger.exception(f"[{self.project_name}] failed to update scene info: {e}")


class ResetController(threading.Thread):
    def __init__(self, scenes: list[Scene]):
        super().__init__(daemon=True)
        self.scenes = scenes
        self._stop_event = threading.Event()
        self._wait_event = threading.Event()

    def run(self, rollback_interval=2):
        while not self._stop_event.is_set():
            for scene in self.scenes:
                with scene.lock:
                    if scene.status == "pending_reset":
                        logger.debug(f"[{scene.project_name}] starting reset...")
                        scene.status = "resetting"

                        threading.Thread(
                            target=self._do_reset, args=(scene,), daemon=True
                        ).start()
            self._wait_event.wait(rollback_interval)

    def stop(self, release_scenes=False):
        """Stop the ResetController thread"""
        global global_lock, global_stop

        with global_lock:
            global_stop = True

        self._stop_event.set()

        if release_scenes:
            for scene in self.scenes:
                subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        scene.compose_path,
                        "-p",
                        scene.project_name,
                        "kill",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        scene.compose_path,
                        "-p",
                        scene.project_name,
                        "down",
                        "-v",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

    def _do_reset(self, scene: Scene):
        try:
            if "airflow" in scene.target_service:
                scene.reset_airflow()
            else:
                scene.reset()
            success = False
            # health check logic
            success = scene._perform_health_check()

            with scene.lock:
                scene.status = "available" if success else "pending_reset"
                logger.debug(
                    f"[{scene.project_name}] reset {'succeeded' if success else 'failed'}"
                )

        except Exception as e:
            logger.exception(f"[{scene.project_name}] reset exception: {str(e)}")
            with scene.lock:
                scene.status = "pending_reset"


class ExecutorPool:
    def __init__(
            self,
            docker_compose_path: str,
            n_workers: int, cve_name: str = "solr",
            status_code_2xx_only: bool = True,
            hc_pre_wait: int = 5,
            hc_max_retries: int = 30,
            hc_interval: int = 3
    ):
        self.cve_name = cve_name
        self.status_code_2xx_only = status_code_2xx_only
        self.scenes = [
            Scene(
                compose_path=docker_compose_path,
                project_name=f"scene_{i + 1}",
                target_service=cve_name,  # target service keyword
                hc_pre_wait=hc_pre_wait,
                hc_max_retries=hc_max_retries,
                hc_interval=hc_interval,
            )
            for i in range(n_workers)
        ]
        self.cov_model = Code_Coverage(service_name=cve_name, service_lang="java")

        logger.info(f"Starting {n_workers} scenes in parallel...")
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=n_workers
        ) as thread_executor:
            futures = {
                thread_executor.submit(scene.start): scene for scene in self.scenes
            }
            for future in tqdm(
                    concurrent.futures.as_completed(futures), total=len(futures)
            ):
                scene = futures[future]
                try:
                    _ = future.result()
                except Exception as e:
                    logger.exception(f"[{scene.project_name}] start exception: {str(e)}")
        # filter available scenes
        available_scenes = [s for s in self.scenes if s.status == "available"]
        logger.info(
            f"Successfully started {len(available_scenes)}/{len(self.scenes)} scenes, beginning to execute request sequences..."
        )
        if len(available_scenes) == 0:
            logger.error("All scenes failed to start. Please check whether the configuration file is valid.")
            raise RuntimeError("Error in starting scenes")
        self.reset_controller = ResetController(self.scenes)
        self.reset_controller.start()

    def process_new_dev(
            self, scene_module, scene_info: dict, seed: SeedInput, fuzz_range: int = 0
    ) -> ExecuteResult:
        aim_ip = "localhost"
        http_port = scene_info["ports"][0]
        container_id = scene_info["id"]
        db_port = scene_info.get("db_port", None)

        seed_validation_flag = True
        seed.local_wordlib = {}
        seed_session = requests.Session()
        seed_id = seed.seed_id
        # execute request sequence
        api_num = seed.api_num
        if api_num != len(seed.api_list):
            logger.error(f"Seed {seed_id} api_num mismatch with actual number of requests, please check the seed")
        if api_num <= 0:
            logger.warning(f"Seed {seed_id} api_num is 0, empty seed")

        for i in range(api_num):
            api_i = seed.api_list[i]
            api_byte = msgspec.msgpack.encode(api_i)
            value_dict = get_real_value_dict(seed.value_dicts[i], seed.local_wordlib)
            request = api_i.to_request(value_dict)
            try:
                if not request:
                    raise Api2HTTPRequestError(
                        f"{api_i.path} cannot be converted to request with the provided parameters")
                response = request.session_send(aim_ip, http_port, seed_session)
                logger.info(f"[{response.status_code}] Seed {seed_id} request #{i + 1} {request.show()}")

                # Save seed information to file
                seed_name = f"seeds/{fuzz_range}/seed_{seed_id}"
                os.makedirs(os.path.dirname(seed_name), exist_ok=True)
                with open(seed_name, "a") as f:
                    f.write("\n" + json.dumps(request.show(), indent=4))

                if self.status_code_2xx_only:
                    # status-code-based validation
                    if not str(response.status_code).startswith("2"):
                        seed_validation_flag = False
                        logger.warning(
                            f"Seed {seed_id} request #{i + 1} returned status {response.status_code}, marking invalid")

                    # CMSMS-specific check
                    if ((not (api_i.method == "GET" and api_i.path == "/admin/login.php")) and (
                            "Login to CMS Made Simple" in response.text)):
                        seed_validation_flag = False
                        logger.warning(f"Seed {seed_id} request #{i + 1} detected CMSMS login page, marking invalid")

                    # YAPI-specific check: errcode field
                    try:
                        real_code = response.json()["errcode"]
                        if not str(real_code).startswith("2") and not str(real_code).startswith("0"):
                            seed_validation_flag = False
                            logger.warning(
                                f"Seed {seed_id} request #{i + 1} returned errcode {real_code}, marking invalid")
                    except:
                        pass

                    # ADD SEED VALIDATION CHECK HERE

                    if seed_validation_flag is False:
                        break
            except Exception as e:
                logger.exception(f"Seed {seed_id} request #{i + 1} send failed: {str(e)}")
                seed_validation_flag = False
                continue
            response_words = response2fuzzwords(response, api_byte)
            update_local_word_lib(seed.local_wordlib, i + 1, value_dict, response_words)

        # code coverage delta (placeholder; compute externally if needed)
        code_coverage_delta = 0.0
        # get current state
        tag_state = (
                container_id
                + "-state-"
                + time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
        )
        get_state_func = getattr(scene_module, "get_state")
        if db_port is None:
            cur_state = get_state_func(container_id, http_port, save_tag=tag_state)
        else:
            cur_state = get_state_func(container_id, http_port, db_port, save_tag=tag_state)

        if cur_state is None:
            logger.error(f"Failed to get current state for seed {seed_id}, returning empty State")
            cur_state = ServerState([], [])

        # execute the final attack step to verify success
        check_attack_func = getattr(scene_module, "check_attack")
        is_attack_success = check_attack_func(http_port, container_id, seed_session, db_port)
        seed_session.close()

        one_ExecuteResult = ExecuteResult(
            seed_id=seed_id,
            local_wordlib=seed.local_wordlib,
            distance_delta=0.0,
            code_coverage_delta=code_coverage_delta,
            new_response_delta=0.0,
            current_state=cur_state,
            is_attack_success=is_attack_success,
            is_2xx_response=seed_validation_flag,
        )
        return one_ExecuteResult

    def execute(self, task_id: int, seed_input: SeedInput, fuzz_range: int = 0) -> ExecuteResult:
        """Request sequence executor"""
        while True:
            for scene in self.scenes:
                if scene.lock.acquire(blocking=False):
                    try:
                        if scene.status == "available":
                            logger.debug(
                                f"[Task-{task_id}] acquired scene {scene.project_name}"
                            )
                            scene.status = "occupied"

                            try:  # execute the seed after acquiring a scene
                                if not scene.target_container:
                                    continue

                                one_ExecuteResult = self.process_new_dev(
                                    scene.tool_module,
                                    scene.target_container,
                                    seed_input,
                                    fuzz_range
                                )

                            except Exception as e:
                                logger.exception(f"[Task-{task_id}] request exception: {str(e)}")
                                one_ExecuteResult = ExecuteResult(seed_input.seed_id)
                            finally:
                                scene.status = "pending_reset"
                            return one_ExecuteResult
                    finally:
                        scene.lock.release()
            time.sleep(2)

    def stop(self, is_release_scenes=False):
        """Stop the FuzzExecutor thread"""
        self.reset_controller.stop(release_scenes=is_release_scenes)
        os.system(f"sudo rm -rf ./example/{self.cve_name}/coverage-reports/*")


def main_multiply(cve_name: str = "solr"):
    max_scenes = 2
    docker_compose_file = f"./example/{cve_name}/compose.yaml"
    fuzzexecutor = ExecutorPool(docker_compose_file, max_scenes, cve_name)
    from basic.seed import BLANK_SEED_INPUT
    seedinput_example = BLANK_SEED_INPUT  # use blank seed as an example
    results = []
    # execute n seeds
    n = 4
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as thread_executor:
        futures = [
            thread_executor.submit(fuzzexecutor.execute, i + 1, seedinput_example)
            for i in range(n)
        ]

        for future in tqdm(
                concurrent.futures.as_completed(futures), total=len(futures)
        ):
            result = future.result()
            results.append(result)

    fuzzexecutor.stop()
    logger.info("All seeds executed")
    return results


# Main function below will only be called when running `python executor.py` directly.
if __name__ == "__main__":
    execute_results = main_multiply("couchdb")

    # Save results to JSON file
    output_file = "./ExecuteResults.json"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(msgspec.json.encode(execute_results).decode("utf-8"))
    print(f"ExecuteResults is saved to {output_file}")
