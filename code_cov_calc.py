import pandas as pd
import numpy as np
import os
from docker import DockerClient

class Code_Coverage:
    def __init__(self, service_name: str, service_lang: str):
        self.service_name = service_name
        self.service_lang = service_lang  # "java"
        self.global_code_cov: np.ndarray = None
        self.dclient = DockerClient.from_env()

    def run_docker_container_command(self, container_name: str, command: str) -> bool:
        try:
            exec_command = self.dclient.containers.get(container_name).exec_run(command)
        # print(f"Execute command: {command}")
        # print(exec_command.output.decode())
        except Exception as e:
            print(f"Command execution failed: {e}")
            return False
        return True

    def process_dump_java_coverages(self, name: str, tag: str) -> bool:
        webapp_name = name  # container name
        jacoco_command = (
            f'java -jar /opt/solr/server/jacococli.jar dump --address localhost '
            f'--port 6066 --destfile /jacoco-reports/jacoco-{tag}.exec'
        )
        try:
            self.run_docker_container_command(container_name=webapp_name, command=jacoco_command)
        except Exception as e:
            print(f"Failed to execute command {jacoco_command}: {e}")
            return False
        return True

    def process_get_java_coverages_report(self, name: str, tag_start: str, tag_end: str) -> float:
        webapp_name = name  # container name
        # Read jacoco.exec files and compute code coverage
        try:
            jacoco_command = (
                f'java -jar /opt/solr/server/jacococli.jar report '
                f'/jacoco-reports/jacoco-{tag_start}.exec '
                f'--classfiles /opt/solr/server/solr-webapp/webapp/WEB-INF/lib/solr-core-8.2.0.jar '
                f'--csv /jacoco-reports/jacoco-{tag_start}.csv'
            )
            self.run_docker_container_command(container_name=webapp_name, command=jacoco_command)
            jacoco_command = (
                f'java -jar /opt/solr/server/jacococli.jar report '
                f'/jacoco-reports/jacoco-{tag_end}.exec '
                f'--classfiles /opt/solr/server/solr-webapp/webapp/WEB-INF/lib/solr-core-8.2.0.jar '
                f'--csv /jacoco-reports/jacoco-{tag_end}.csv'
            )
            self.run_docker_container_command(container_name=webapp_name, command=jacoco_command)

            csv_file_start = f'./example/solr/coverage-reports/jacoco-{tag_start}.csv'
            csv_file_end = f'./example/solr/coverage-reports/jacoco-{tag_end}.csv'
            df_start = pd.read_csv(csv_file_start, usecols=["INSTRUCTION_COVERED"])
            df_end = pd.read_csv(csv_file_end, usecols=["INSTRUCTION_COVERED"])

            np1 = df_start["INSTRUCTION_COVERED"].to_numpy(dtype=np.int64)
            np2 = df_end["INSTRUCTION_COVERED"].to_numpy(dtype=np.int64)
            diff = np2 - np1
            os.system(f"sudo rm -rf ./example/solr/coverage-reports/*{tag_start}*")
            os.system(f"sudo rm -rf ./example/solr/coverage-reports/*{tag_end}*")
            return self.code_cov_delta_percent(diff)

        except Exception as e:
            print(f"Failed to execute command {jacoco_command}: {e}")
            return None

    def code_cov_delta_percent(self, cur_code_cov: np.ndarray) -> float:
        "Compute the incremental percentage of current code coverage compared to the global code coverage"
        if cur_code_cov is None:
            return 0.0
        if self.global_code_cov is None:  # first update
            self.global_code_cov = cur_code_cov
            return 100.0

        assert len(self.global_code_cov) == len(cur_code_cov)

        new_global_np = np.maximum(self.global_code_cov, cur_code_cov)
        # Compute incremental percentage
        delta_np = new_global_np - self.global_code_cov
        if delta_np.sum() == 0:
            return 0.0
        if self.global_code_cov.sum() == 0:
            return 100.0
        code_cov_delta = delta_np.sum() / self.global_code_cov.sum() * 100

        self.global_code_cov = new_global_np  # update global code coverage
        return float(code_cov_delta)

if __name__ == '__main__':
    global_code_cov = np.array([10, 20, 30, 40, 50])
    cur_code_cov = np.array([0, 0, 0, 0, 60])
    cov_model = Code_Coverage(service_name='solr', service_lang='java')
    cov_model.global_code_cov = global_code_cov
    code_cov_delta = cov_model.code_cov_delta_percent(cur_code_cov)
    print(code_cov_delta)
