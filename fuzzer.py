import concurrent.futures
import os
from pathlib import Path
import random
import shutil
from typing import Literal, Optional, List, Dict, Tuple, Any

from loguru import logger
import msgspec
from tqdm import tqdm

from basic.server_state import ServerState
import cal_weight
import sa_score
from basic.seed import SeedInput, BLANK_SEED_INPUT
from executor import (
    ExecutorPool,
    sa_ExecuteResult,
    ExecuteResult,
)
from key_dependency_model import KeyDependencyModel
from loader import InitData
from seedpool import SeedPool, calculate_mutate_times
from util import util
from word_lib import WordLib
from thread_pool import get_global_thread_pool

StageInfo = Literal["Approach", "Info"]
pool = get_global_thread_pool()


def save_seeds_background(seeds: list[SeedInput], rounds: int):
    seed_info_to_print = []
    for seed in seeds:
        assert isinstance(seed, SeedInput)
        for i, api in enumerate(seed.api_list):
            req = api.to_request(seed.value_dicts[i])
            if not req:
                continue
            seed_info_to_print.append(
                {
                    "method": req.method,
                    "path": req.path,
                    "params": req.params,
                    "data": req.data,
                    "json": req.json,
                    "files": req.files,
                }
            )

    with open(f"{rounds}.seed.json", "wb") as f:
        f.write(msgspec.json.encode(seed_info_to_print))


class Fuzzer:
    def __init__(self, init_data: InitData, docker_compose_path):
        self.config = init_data.config
        self.depended_state = init_data.depended_state
        self.attack_data = init_data.attack_data
        self.batch_size = init_data.config.fuzz_batch_size
        self.max_executor_numbers = init_data.config.max_executor_numbers
        self.seed_queue = init_data.init_seeds
        self.seed_pool = SeedPool(init_data.init_seeds)  # not used?
        self.executors = ExecutorPool(
            docker_compose_path=docker_compose_path,
            n_workers=self.max_executor_numbers,
            cve_name=init_data.config.cve_name,
            status_code_2xx_only=init_data.config.status_code_200_only,
            hc_pre_wait=init_data.config.hc_pre_wait,
            hc_max_retries=init_data.config.hc_max_retries,
            hc_interval=init_data.config.hc_interval,
        )
        self.global_word_lib = WordLib([])
        self.target_word_lib = init_data.target_wordlib
        self.api_dependency_model = init_data.api_dependency_model
        self.key_dependency_model = KeyDependencyModel(
            init_data.key_dependency_model_data
        )
        self.seed_hash_set = set()  # for deduplicating seeds
        # Initial seeds must also be added to the hash set
        for seed in self.seed_queue:
            self.seed_hash_set.add(hash(seed))
        self.seed_results: dict[int, sa_ExecuteResult] = {}
        self.min_weight = init_data.config.min_weight
        self.max_weight = init_data.config.max_weight
        self.start_time = sa_score.get_cur_time()
        self.cooling_schedule = init_data.config.cooling_schedule
        self.t_x = init_data.config.t_x
        self.MAX_FACTOR = init_data.config.MAX_FACTOR

    def mutate(
        self,
        father_seed: SeedInput,
        current_state: Optional[ServerState] = None,
        max_retries: int = 10,
    ) -> SeedInput:
        # Try up to `max_retries` times
        for _ in range(max_retries):
            mutate_methods = [
                "ADD NEW API",
                "MODIFY LAST API",
            ]

            if father_seed.api_num > 0:
                last_api = father_seed.api_list[-1]
                if len(last_api.positions) == 0:
                    mutate_method = "ADD NEW API"
                else:
                    mutate_method = random.choice(mutate_methods)
            else:
                mutate_method = "ADD NEW API"

            if mutate_method == "ADD NEW API":

                ############################################################################
                # Compute satisfiability (range 0–1) for all ApiPositions and return Dict[ApiPosition, float]
                api_pos_satisfiability = (
                    self.key_dependency_model.get_position_satisfiability(
                        father_seed.local_wordlib
                    )
                )
                filtered_items = [
                    (k, v) for k, v in api_pos_satisfiability.items() if v < 0.5
                ][:10]
                log_dict = {k.name: f"{v:.4f}" for k, v in filtered_items}
                logger.debug(
                    f"ApiPosition satisfiability (lower values): {log_dict}"
                )
                ############################################################################

                new_api = self.api_dependency_model.infer(
                    # new_api = self.api_dependency_model.infer_NoSelect(
                    api_sequence=father_seed.api_list,
                    api_pos_satisfiability=api_pos_satisfiability,
                    ratio=self.config.ratio,
                    h=util.str2func(self.config.h),
                    b=self.config.b,
                    static_state_satisfiability=self.config.static_state_satisfiability,
                    current_state=current_state,
                    depended_state=self.depended_state,
                    seed=father_seed,
                )
                api_list = father_seed.api_list + [new_api]
                value_dicts = self.key_dependency_model.mutate_key_value(
                    father_seed, api_list, self.global_word_lib
                )
            else:
                api_list = father_seed.api_list
                value_dicts = self.key_dependency_model.mutate_key_value(
                    father_seed, api_list, self.global_word_lib
                )
            new_seed = SeedInput(
                api_num=len(api_list),
                api_list=api_list,
                value_dicts=value_dicts,
            )
            # Use the hash of API sequence + param sequence for deduplication
            seed_hash = hash(new_seed)
            if seed_hash not in self.seed_hash_set:
                self.seed_hash_set.add(seed_hash)
                logger.info(
                    {
                        "mutate_method": mutate_method,
                        "PRE_seed_id": father_seed.seed_id,
                        "NEW_seed_id": new_seed.seed_id,
                        "api_num": new_seed.api_num,
                        "api_list": [
                            f"{api.method.value} {api.path}"
                            for api in new_seed.api_list
                        ],
                    }
                )
                return new_seed
            else:
                SeedInput._next_id -= 1
                logger.warning(
                    f"Seed {father_seed.seed_id} produced a duplicate seed; re-mutating..."
                )
                logger.debug(
                    f"Duplicate produced from seed {father_seed.seed_id}, seed details:"
                )
                logger.debug(
                    {
                        "seed_id": new_seed.seed_id,
                        "api_num": new_seed.api_num,
                        "api_list": [
                            f"{api.method.value} {api.path}"
                            for api in new_seed.api_list
                        ],
                    }
                )
        # If all attempts produce duplicates, return the original father_seed
        logger.warning(
            f"Consecutive duplicate mutations from seed {father_seed.seed_id}; returning original seed"
        )
        return father_seed

    def execute_seed(
        self, new_seed: SeedInput, fuzz_range: int = 0
    ) -> tuple[SeedInput, ExecuteResult]:
        # Execute requests in parallel
        execute_result = self.executors.execute(new_seed.seed_id, new_seed, fuzz_range)
        return new_seed, execute_result

    def update_for_next_round(
        self,
        current_round_seeds: List[SeedInput],
        current_seed_results: Dict[int, sa_ExecuteResult],
    ):
        """
        Update the seed pool for the next round based on new rules.

        Args:
            current_round_seeds (List[SeedInput]): All successful seeds in the current round.
            current_seed_results (Dict[int, sa_ExecuteResult]): Execution results of mutated seeds in the current round.
        """
        logger.info("\n--- Updating seed pool for next round ---")
        logger.info(f"Successful seeds this round: {len(current_round_seeds)}")
        logger.info(f"Current seed pool size: {len(self.seed_queue)}")

        next_seeds_queue = []

        # Rule 3: If there are no seeds this round, keep the current seed pool unchanged.
        if not current_round_seeds:
            logger.warning("No successful seeds this round; keeping the current seed pool unchanged.")
            # next_seeds_queue remains empty; finalization keeps self.seed_queue as-is
            pass

        # Check whether scores are “identical”
        elif current_round_seeds:
            precision = 3
            unique_formatted_weights = {
                f'{current_seed_results[seed.seed_id].cur_weight:.{precision}f}'
                for seed in current_round_seeds
            }
            scores_are_identical = len(unique_formatted_weights) <= 1

            # Rule 0: If all seed scores are identical, keep all as next-round seeds.
            if scores_are_identical:
                current_round_seeds = current_round_seeds[:16]  # take the first 16 seeds
                # Merge new and existing seeds with deduplication
                combined_seeds_map = {seed.seed_id: seed for seed in self.seed_queue}
                for seed in current_round_seeds:
                    combined_seeds_map[seed.seed_id] = seed
                next_seeds_queue = list(combined_seeds_map.values())

            # Rule 2: Scores differ but fewer than 20 seeds; keep all and merge with current pool.
            elif len(current_round_seeds) < 20:
                combined_seeds_map = {seed.seed_id: seed for seed in self.seed_queue}
                for seed in current_round_seeds:
                    combined_seeds_map[seed.seed_id] = seed
                next_seeds_queue = list(combined_seeds_map.values())

            # Rule 1: ≥ 20 seeds and scores differ; filter.
            else:  # len(current_round_seeds) >= 20 and not scores_are_identical
                logger.warning(
                    f"Rule [1] triggered: successful seeds ≥ 20 ({len(current_round_seeds)}) and scores differ; filtering..."
                )
                merged_map = {s.seed_id: s for s in self.seed_queue}  # put old seeds
                for s in current_round_seeds:
                    merged_map[s.seed_id] = s  # then new seeds
                merged_seeds = list(merged_map.values())

                def get_result(seed):
                    return current_seed_results.get(seed.seed_id) or self.seed_results.get(seed.seed_id)

                merged_seeds_with_score = [
                    s for s in merged_seeds
                    if (r := get_result(s)) is not None and getattr(r, "cur_weight", None) is not None
                ]

                if not merged_seeds_with_score:
                    logger.warning("Rule [1] failed: no usable seeds.")
                    next_seeds_queue = []
                else:
                    # Sort by weight descending
                    sorted_seeds = sorted(
                        merged_seeds_with_score,
                        key=lambda s: get_result(s).cur_weight,
                        reverse=True,
                    )
                    top_16_seeds = sorted_seeds[:16]
                    remaining_seeds = sorted_seeds[16:]
                    # If remaining seeds fewer than 4, take all of them
                    num_to_sample = min(4, len(remaining_seeds))
                    randomly_selected_seeds = random.sample(remaining_seeds, num_to_sample)
                    next_seeds_queue = top_16_seeds + randomly_selected_seeds

        # --- Finalization Step ---
        # Only update when `next_seeds_queue` has content; otherwise keep as-is (Rule 3)
        if next_seeds_queue:
            self.seed_queue = next_seeds_queue

            # Maintain seed_results for next round
            new_seed_results = {}
            for seed in self.seed_queue:
                if seed.seed_id in current_seed_results:
                    new_seed_results[seed.seed_id] = current_seed_results[seed.seed_id]
                else:
                    new_seed_results[seed.seed_id] = self.seed_results[seed.seed_id]

            self.seed_results = new_seed_results

        logger.warning(f"Update complete! Next round will mutate {len(self.seed_queue)} seeds.")
        logger.warning(f"Next round seed IDs: {sorted([s.seed_id for s in self.seed_queue])}")

    def calculate_stage_max(self, doing_det, perf_score, havoc_div):
        """
        Compute AFL fuzzing mutation count (stage_max).

        :param doing_det: Whether in deterministic mutation stage (bool)
        :param perf_score: Performance score determining mutation intensity
        :param havoc_div: Mainly affected by target program execution speed
        :param HAVOC_CYCLES_INIT: Base cycles for deterministic mutation (default 1024)
        :param HAVOC_CYCLES: Base cycles for non-deterministic mutation (default 8192)
        :return: Calculated mutation count stage_max
        """
        HAVOC_CYCLES_INIT = 20
        HAVOC_CYCLES = 40
        base_cycles = HAVOC_CYCLES_INIT if doing_det else HAVOC_CYCLES
        stage_max = (base_cycles * perf_score) // (havoc_div * 100)
        return max(1, stage_max)  # ensure at least one mutation

    def judge_seed(
        self,
        exec_result: sa_ExecuteResult,
        stage,
    ) -> list[SeedInput]:
        # TODO: Evaluate seed quality to decide pruning or keeping

        # Seeds for the next fuzzing round
        next_round_seeds = []

        # Approach stage
        if stage == "Approach":
            if exec_result.new_perf_score > exec_result.orig_perf_score:
                return True
            else:
                random_score = random.randint(0, 70)
                logger.info(
                    f"[*] Seed {exec_result.seed_id} probabilistic score: {exec_result.new_perf_score} | random threshold: {random_score}"
                )
                if exec_result.new_perf_score > random_score:
                    return True

        # Info stage: compute a score (simple non-negative check here)
        elif stage == "Info":
            if exec_result.code_coverage_delta >= 0 and exec_result.new_response_delta >= 0:
                return True

        return False

    def fuzz(self):
        def find_file(root_dir, filename):
            """
            Find a specific file under root_dir (recursively).
            Return the full path if found; None if not found; raise if multiple found.
            """
            matches = []
            for dirpath, dirnames, filenames in os.walk(root_dir):
                if filename in filenames:
                    matches.append(os.path.join(dirpath, filename))

            if len(matches) == 0:
                return None
            elif len(matches) == 1:
                return matches[0]
            else:
                raise FileExistsError(f"Multiple files with the same name found: {matches}")

        StageInfo = ["Approach", "Info"]
        start_time = sa_score.get_cur_time()
        t_x = 10
        stage_time = t_x / 10
        fuzz_range = 0

        # step 1. Execute initial seed sequences
        if not self.seed_queue or len(self.seed_queue) == 0:
            mutate_times = 5
            logger.info(f"Initial seed pool is empty; pre-mutate {mutate_times} seeds")
            blank_seed = BLANK_SEED_INPUT
            for _ in range(mutate_times):
                mutate_seed = self.mutate(blank_seed)
                self.seed_queue.append(mutate_seed)
        else:  # Seed pool is not empty; use directly
            logger.info(f"Successfully imported {len(self.seed_queue)} initial seeds")

        is_attack_success = False
        success_seed: Optional[SeedInput] = None

        for seed in self.seed_queue:
            result = self.executors.execute(seed.seed_id, seed)
            # logger.debug(f"Seed {seed.seed_id} local wordlib:{seed.local_wordlib}")
            cur_weight = cal_weight.calculate_distance(
                (
                    result.current_state if result.current_state else ServerState([], [])
                ),
                self.attack_data.depended_state,
            )
            logger.info("min_weight:", self.min_weight, "max_weight:", self.max_weight)
            if cur_weight < self.min_weight:
                self.min_weight = cur_weight
            if cur_weight > self.max_weight:
                self.max_weight = cur_weight
            cur_ms = sa_score.get_cur_time()
            new_perf_score = sa_score.calculate_score(
                self.cooling_schedule,
                cur_ms,
                self.start_time,
                self.t_x,
                cur_weight,
                self.min_weight,
                self.max_weight,
                seed.perf_score,
                self.MAX_FACTOR,
            )
            orig_perf_socre = seed.perf_score
            seed.perf_score = new_perf_score
            logger.info(
                f"[*] Seed {result.seed_id} probabilistic score: {new_perf_score} | original: {orig_perf_socre}"
            )

            seed_result = sa_ExecuteResult(
                seed_id=result.seed_id,
                orig_perf_score=orig_perf_socre,
                new_perf_score=new_perf_score,
                code_coverage_delta=result.code_coverage_delta,
                new_response_delta=result.new_response_delta,
                is_2xx_response=result.is_2xx_response,
                cur_weight=cur_weight,
                current_state=result.current_state,
            )

            self.seed_results[seed.seed_id] = seed_result
            if result.is_attack_success:
                is_attack_success = True
                success_seed = seed
                logger.success("Seed {} succeeded in attack", seed.seed_id)
                result_path = find_file("seeds", f"seed_{seed.seed_id}")
                assert result_path
                shutil.copy2(result_path, f"success/seed_{seed.seed_id}")
                break
            else:
                logger.info("Seed {} attack failed", seed.seed_id)

        rounds = 0
        while True:
            # Save the seed pool at the beginning of each round
            os.makedirs(f"seeds/{fuzz_range}", exist_ok=True)
            if is_attack_success:
                assert success_seed
                logger.success(f"Seed {success_seed.seed_id} attack succeeded, details:")
                for i in range(success_seed.api_num):
                    api = success_seed.api_list[i]
                    value_dict = success_seed.value_dicts[i]
                    result_dict = {}
                    result_dict["API"] = f"{api.method.value} {api.path}"
                    for key, value in value_dict.items():
                        result_dict[key.name] = value
                    logger.success(result_dict)

                self.executors.stop(is_release_scenes=True)
                exit(0)

            fuzz_range += 1
            logger.info(f"Fuzz round {fuzz_range}")

            # --- 1. Select seeds to mutate for this batch ---
            seed_queue_old = self.seed_queue.copy()
            logger.info("Calculating mutation counts")
            select_seeds: dict[SeedInput, int] = {}
            select_seeds = calculate_mutate_times(
                seed_queue_old,
                self.seed_results,
                total_mutations=2 * len(seed_queue_old) + 1,
            )
            logger.info(
                "[+] Mutation counts computed: "
                + ", ".join(f"Seed {seed.seed_id}: {count}" for seed, count in select_seeds.items())
            )

            current_time = sa_score.get_cur_time()
            internal = int(((current_time - start_time) / 1000) % (stage_time * 60))
            stage = StageInfo[internal % 2]
            logger.info(f"Current fuzzing stage: {stage}")

            mutate_seeds: list[SeedInput] = []
            next_round_seeds = []
            logger.info("Mutating to generate new seeds")
            for seed, mutation_times in select_seeds.items():
                for _ in range(int(mutation_times)):
                    mutate_seed = self.mutate(
                        father_seed=seed,
                        current_state=self.seed_results[seed.seed_id].current_state,
                    )
                    mutate_seeds.append(mutate_seed)
            logger.info(f"Newly mutated seeds: {[seed.seed_id for seed in mutate_seeds]}")

            # --- 2. Execute new seeds ---
            temp_seed_results: dict[int, sa_ExecuteResult] = {}
            logger.info("Executing new seeds")
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_executor_numbers
            ) as thread_executor:
                futures: list[
                    concurrent.futures.Future[tuple[SeedInput, ExecuteResult]]
                ] = []
                for new_seed in mutate_seeds:
                    futures.append(
                        thread_executor.submit(self.execute_seed, new_seed, fuzz_range)
                    )
                for future in tqdm(
                    concurrent.futures.as_completed(futures), total=len(futures)
                ):
                    new_seed, result = future.result()
                    new_seed.local_wordlib = result.local_wordlib  # save seed's local wordlib
                    # logger.debug(f"Seed {new_seed.seed_id} local wordlib:{new_seed.local_wordlib}")
                    if result.is_attack_success:
                        is_attack_success = True
                        success_seed = new_seed
                        logger.success("Seed {} succeeded in attack", new_seed.seed_id)
                        result_path = find_file("seeds", f"seed_{new_seed.seed_id}")
                        assert result_path
                        result_path = Path(result_path)
                        dst_dir = Path("success") / f"seed_{new_seed.seed_id}"
                        dst_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(result_path, dst_dir / result_path.name)
                        shutil.copy2(result_path, f"success/seed_{new_seed.seed_id}")
                        break
                    else:
                        logger.info("Seed {} attack failed", new_seed.seed_id)
                    cur_weight = cal_weight.calculate_distance(
                        (
                            result.current_state if result.current_state else ServerState([], [])
                        ),
                        self.attack_data.depended_state,
                    )
                    logger.info("min_weight:", self.min_weight, "max_weight:", self.max_weight)
                    if cur_weight < self.min_weight:
                        self.min_weight = cur_weight
                    if cur_weight > self.max_weight:
                        self.max_weight = cur_weight

                    cur_ms = sa_score.get_cur_time()
                    new_perf_score = sa_score.calculate_score(
                        self.cooling_schedule,
                        cur_ms,
                        self.start_time,
                        self.t_x,
                        cur_weight,
                        self.min_weight,
                        self.max_weight,
                        new_seed.perf_score,
                        self.MAX_FACTOR,
                    )

                    orig_perf_socre = new_seed.perf_score
                    new_seed.perf_score = new_perf_score
                    logger.info(
                        f"[*] Seed {result.seed_id} probabilistic score: {new_perf_score} | original: {orig_perf_socre}"
                    )

                    seed_result = sa_ExecuteResult(
                        seed_id=result.seed_id,
                        orig_perf_score=orig_perf_socre,
                        new_perf_score=new_perf_score,
                        code_coverage_delta=result.code_coverage_delta,
                        new_response_delta=result.new_response_delta,
                        is_2xx_response=result.is_2xx_response,
                        cur_weight=cur_weight,
                        current_state=result.current_state,
                    )
                    temp_seed_results[new_seed.seed_id] = seed_result
                    if self.judge_seed(seed_result, stage):
                        next_round_seeds.append(new_seed)
            if is_attack_success:
                continue

            # Append accepted seeds to the seed queue and update results
            for seed in next_round_seeds:
                if temp_seed_results[seed.seed_id].is_2xx_response is False:
                    continue
                self.seed_queue.append(seed)
                self.seed_results[seed.seed_id] = temp_seed_results[seed.seed_id]
            ################################################
            next_seeds = [seed for seed in self.seed_queue]
            pool.submit(save_seeds_background, next_seeds, rounds)
            logger.debug("Next-round seed IDs: {}", [seed.seed_id for seed in next_seeds])
            rounds += 1
