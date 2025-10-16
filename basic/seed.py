import msgspec
from api.api_node import ApiNode

from basic.fuzzword import MutateValue
from basic.position import ApiPosition
from word_lib import LocalWordlib


class SeedInput(msgspec.Struct, tag="seed_input_new_dev"):
    # finished_time: int  # Last time fuzzing finished
    # started_time: int   # Last time fuzzing started
    # min_distance: int   # Minimum distance to the target state during fuzzing
    # max_distance: int   # Maximum distance to the target state during fuzzing

    _next_id = 0
    seed_id: int = 0
    api_num: int = 0  # Number of APIs currently in the seed
    api_list: list[ApiNode] = []
    value_dicts: list[dict[ApiPosition, MutateValue]] = []
    local_wordlib: LocalWordlib = {}

    was_fuzzed: int = 0
    perf_score: float = 100

    def __post_init__(self):
        self.seed_id = SeedInput._next_id
        SeedInput._next_id += 1

    def __eq__(self, other):
        if isinstance(other, SeedInput):
            return (
                    self.api_list == other.api_list
                    and self.value_dicts == other.value_dicts
            )
        return False

    def __hash__(self):
        api_list_tuple = tuple(self.api_list)
        value_dicts_tuple = tuple(
            tuple(d.items()) for d in self.value_dicts
        )
        return hash((api_list_tuple, value_dicts_tuple))


BLANK_SEED_INPUT = SeedInput(
    api_list=[],
    value_dicts=[],
)
