from dataclasses import dataclass
from functools import cached_property
from loguru import logger
from pathlib import Path
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
import tomllib

from dataclasses_json import DataClassJsonMixin
import msgspec

from api.api_dependency_model import APIDependencyModel
from basic.attack_data import AttackData
from basic.position import ApiPosition
from basic.seed import BLANK_SEED_INPUT, SeedInput
from basic.server_state import ServerState
from key_dependency_model import KeyDependencyModelData
from word_lib import WordLib


@dataclass
class Config(DataClassJsonMixin):
    cve_name: str

    # Predefined files
    final_attack: str  # The final attack step
    server_state: str  # Target state
    depended_state: str  # State that the final attack depends on
    api_dependency: str  # API dependency graph
    seed_input: str  # Initial seeds
    init_wordlib: str  # Initial word library
    target_wordlib: str  # Target word library

    # Executor parameters
    max_executor_numbers: int
    status_code_200_only: bool
    hc_pre_wait: int  # Wait time before starting a scenario
    hc_max_retries: int  # Max retries when scenario startup fails
    hc_interval: int  # Retry interval when scenario startup fails

    # Fuzz parameters
    fuzz_batch_size: int

    # Field dependency graph parameters
    optional_api_mutation_probability: (
        float  # (Legacy mutation, to be deprecated) mutate non-required API params with this probability
    )
    init_wordlib_mutation_probability: (
        float
    # (Legacy mutation, to be deprecated) choose value ranges from the initial word library with this probability
    )
    p_use_dependency: float  # Probability of selecting Position from dependency graph (otherwise choose itself)
    p_local_wordlib: float  # Priority coefficient for choosing values from local word library during mutation (max 1)
    p_target_wordlib: float  # Priority coefficient for values from target word library (max 1)

    # Seed evaluation parameters
    HAVOC_CYCLES_INIT: int
    HAVOC_CYCLES: int
    min_weight: int
    max_weight: int
    cooling_schedule: str
    t_x: float
    MAX_FACTOR: int
    SKIP_TO_NEW_PROB: int  # Assume skip probability is 99%
    havoc_div: int

    # API dependency graph parameters
    h: str
    b: float
    ratio: str
    static_state_satisfiability: str

    # Additional parameters
    cve_path: str = ""


@dataclass
class InitData:
    attack_data: AttackData
    init_seeds: list[SeedInput]
    target_wordlib: WordLib  # Collects request corpus of the final attack and State corpus
    depended_state: ServerState
    api_dependency_model: APIDependencyModel
    key_dependency_model_data: KeyDependencyModelData  # Save initial word library to build field dependency graph
    config: Config


@dataclass
class Loader:
    config_path: str

    @cached_property
    def config(self):
        with open(self.config_path, "rb") as f:
            toml_dict = tomllib.load(f)
        config = Config.from_dict(toml_dict)
        config.cve_path = self.config_path.split("/")[-2]
        return config

    def load_attack_data(self) -> AttackData:
        """
        final_attack_bin = Path(
            f"example/{self.config.cve_path}/{self.config.final_attack}"
        ).read_bytes()
        final_attack = msgspec.msgpack.decode(final_attack_bin, type=RequestSequence)
        """
        server_state_bin = Path(
            f"example/{self.config.cve_path}/{self.config.server_state}"
        ).read_bytes()
        server_state = msgspec.msgpack.decode(server_state_bin, type=ServerState)

        depended_state_bin = Path(
            f"example/{self.config.cve_path}/{self.config.depended_state}"
        ).read_bytes()
        depended_state = msgspec.msgpack.decode(depended_state_bin, type=ServerState)

        return AttackData(
            # final_attack is included in the target corpus and is no longer used
            final_attack=None,  # type:ignore
            server_state=server_state,
            depended_state=depended_state,
        )

    def load_depended_state(self) -> ServerState:
        return msgspec.msgpack.decode(
            Path(
                f"example/{self.config.cve_path}/{self.config.depended_state}"
            ).read_bytes(),
            type=ServerState,
        )

    def get_target_wordlib(self) -> WordLib:
        try:
            target_lib = WordLib.from_bin(
                f"./example/{self.config.cve_path}/{self.config.target_wordlib}"
            )
            logger.info(f"Loaded predefined target word library successfully: {self.config.target_wordlib}")
        except Exception:
            logger.info("Building the target word library from target state and final_attack")
            target_state_bin = Path(
                f"example/{self.config.cve_path}/{self.config.server_state}"
            ).read_bytes()
            target_state = msgspec.msgpack.decode(target_state_bin, type=ServerState)
            target_lib = WordLib(
                target_state.to_wordlist().dictionary
            )  # Return the highlighted target word library
        return target_lib

    def load_api_dependency_model(self) -> APIDependencyModel:
        # logger.debug(f"example/{self.config.cve_path}/{self.config.api_dependency}")
        dependency_bin = Path(
            f"example/{self.config.cve_path}/{self.config.api_dependency}"
        ).read_bytes()
        model = msgspec.msgpack.decode(dependency_bin, type=APIDependencyModel)
        return model

    def load_key_dependency_model_data(
            self, target_wordlib: WordLib
    ) -> KeyDependencyModelData:
        if self.config.init_wordlib.endswith(".bin"):
            init_lib = WordLib.from_bin(
                f"example/{self.config.cve_path}/{self.config.init_wordlib}"
            )
        elif self.config.init_wordlib.endswith(".json"):
            init_lib = WordLib.from_file(
                f"example/{self.config.cve_path}/{self.config.init_wordlib}"
            )
        else:
            logger.error(
                f"The init_wordlib file extension must be .bin or .json: {self.config.init_wordlib}"
            )
            raise ValueError(f"Invalid init_wordlib file format: {self.config.init_wordlib}")

        # Get the number of positions across word libraries
        init_pos = init_lib.position_map.keys()
        target_pos = target_wordlib.position_map.keys()
        merge_pos = init_pos | target_pos
        logger.info(f"Number of positions in word libraries: {len(merge_pos)}")

        all_words = init_lib.word_list()
        api_positions = set()
        for word in all_words:
            if isinstance(word.position, ApiPosition):
                api_positions.add(word.position)
        api_positions = list(api_positions)
        # print(api_positions)
        return KeyDependencyModelData(
            all_api_positions=api_positions,
            init_word_lib=init_lib,
            target_word_lib=target_wordlib,
            p_local_wordlib=self.config.p_local_wordlib,
            p_target_wordlib=self.config.p_target_wordlib,
            p_use_dependency=self.config.p_use_dependency,
            # optional_api_mutation_probability=self.config.optional_api_mutation_probability,
            # init_wordlib_mutation_probability=self.config.init_wordlib_mutation_probability,
        )

    def load_init_seeds(self) -> list[SeedInput]:
        try:
            seeds_bin = Path(
                f"example/{self.config.cve_path}/{self.config.seed_input}"
            ).read_bytes()
            return msgspec.msgpack.decode(seeds_bin, type=list[SeedInput])
        except Exception as e:
            logger.info("Initial seed file not found; using blank seed")
            return [BLANK_SEED_INPUT]  # Blank seed

    def load(self) -> InitData:
        final_attack_data = self.load_attack_data()
        init_seeds = self.load_init_seeds()

        target_wordlist = self.get_target_wordlib()

        api_dependency_model_data = self.load_api_dependency_model()
        key_dependency_model_data = self.load_key_dependency_model_data(target_wordlist)

        depended_state = self.load_depended_state()

        return InitData(
            attack_data=final_attack_data,
            init_seeds=init_seeds,
            target_wordlib=target_wordlist,
            depended_state=depended_state,
            api_dependency_model=api_dependency_model_data,
            key_dependency_model_data=key_dependency_model_data,
            config=self.config,
        )
