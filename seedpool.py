import random
import math
from basic.seed import SeedInput
from basic.server_state import DependedState

from executor import ExecutorPool, sa_ExecuteResult
import cal_weight

# from fuzzer import Fuzzer
# import sql


def calculate_stage_max(
    doing_det, perf_score, havoc_div, HAVOC_CYCLES_INIT=2, HAVOC_CYCLES=8
):
    """
    Compute AFL fuzzing mutation count (stage_max).

    :param doing_det: Whether in deterministic mutation stage (bool)
    :param perf_score: Performance score that determines mutation intensity
    :param havoc_div: havoc_div is mainly influenced by the target program's execution speed
    :param HAVOC_CYCLES_INIT: Base cycles for deterministic mutations (default 1024)
    :param HAVOC_CYCLES: Base cycles for non-deterministic mutations (default 8192)
    :return: Calculated mutation count stage_max
    """
    base_cycles = HAVOC_CYCLES_INIT if doing_det else HAVOC_CYCLES
    stage_max = (base_cycles * perf_score) // (havoc_div * 100)
    return max(1, stage_max)  # Ensure at least 1 mutation


def softmax(x):
    """Standard softmax; sums to 1 and is numerically stable for negative values."""
    max_x = max(x)
    exps = [math.exp(val - max_x) for val in x]  # prevent overflow
    sum_exps = sum(exps)
    return [exp_i / sum_exps for exp_i in exps]


def calculate_mutate_times(
    seed_queue: list[SeedInput],
    seed_results: dict[int, sa_ExecuteResult],
    total_mutations=10,
):
    """
    Web_Fuzz: compute mutation counts per seed.

    :param seed_queue: Seed queue
    :param seed_results: Seed execution results
    :param total_mutations: Total number of mutations to distribute
    :return: Dict of {seed: mutation_count}
    """
    selected_seeds: dict[SeedInput, int] = {}
    score_list: list[float] = []
    for seed in seed_queue:
        result = seed_results[seed.seed_id]
        score_list.append(result.cur_weight)
    # Step 1: softmax-normalize weights
    sm_probs = softmax(score_list)

    # Step 2: proportionally assign fractional counts
    raw_counts = [prob * total_mutations for prob in sm_probs]

    # Step 3: floor + remainder distribution to ensure sum equals total_mutations
    int_counts = [int(count) for count in raw_counts]
    diff = total_mutations - sum(int_counts)
    # Give the remaining diff to the largest fractional parts in raw_counts
    decimals = [
        (raw - intc, idx) for idx, (raw, intc) in enumerate(zip(raw_counts, int_counts))
    ]
    decimals.sort(reverse=True)  # largest first
    for i in range(diff):
        idx = decimals[i][1]
        int_counts[idx] += 1

    # Step 4: build output dict
    for idx, seed in enumerate(seed_queue):
        selected_seeds[seed] = int_counts[idx]
    return selected_seeds


class SeedPool:
    def __init__(self, init_seeds: list[SeedInput]):
        # TODO
        self.init_seeds = init_seeds
        pass

    def get_best_seed(
        self,
        executors: ExecutorPool,
        BATCH_ID: int,
        depended_state: DependedState,
        min_weight,
        max_weight,
    ) -> dict[SeedInput, int]:
        # TODO
        # return seed input and how many mutations will be generated

        fuzz_seeds_result = {}
        # print(self.init_seeds)
        best_seed, seed_weight = {}, {}
        max_score = 0
        max_seed = None
        for init_seed in self.init_seeds:
            init_seed_result = executors.execute(BATCH_ID, init_seed)
            current_state = init_seed_result.current_state
            weight = cal_weight.calculate_distance(current_state, depended_state)

            # print(distance)
            # fuzz_seeds_result.update({init_seed.seed_id: {'min_weight': -1, 'max_weight': -1,
            #                                               'cur_weight': weight, 'cur_ms': datetime.now()}})
            if weight > max_score:
                max_score = weight
                # max_seed_id = init_seed.seed_id
                max_seed = init_seed
            seed_weight.update({init_seed: weight})

            if weight > max_weight:
                max_weight = weight
            if weight < min_weight:
                min_weight = weight

            # sql.insert_batch(BATCH_ID, init_seed, current_state, weight)

        # Record the highest-scoring seed
        assert max_seed
        best_seed.update({max_seed: random.randint(1, 5)})

        # Give lower-scoring seeds a chance as well
        random_weight = random.uniform(min_weight, max_weight)
        random_best_seeds = [k for k, v in seed_weight.items() if v > random_weight]
        for random_best_seed in random_best_seeds:
            best_seed.update({random_best_seed: random.randint(1, 5)})

        # with open('fuzz_seeds_result.txt', "w") as f:
        #     f.write(str(fuzz_seeds_result))

        return best_seed, min_weight, max_weight
