from itertools import chain
from turtle import mode
from typing import List, Self, Union, Dict, Set
from dataclasses import dataclass, field

from loguru import logger
from basic.fuzzword import FuzzWord
from basic.position import ApiPosition, ResponsePosition, TablePosition, FilePosition
import msgspec
from interface.docable import Docable

WordPosition = Union[ApiPosition, ResponsePosition, TablePosition, FilePosition]
LocalWordlib = Dict[int, Dict[Union[ApiPosition, ResponsePosition], list[Union[str, int, float]]]]


@dataclass
class Word:
    value: Union[str, int, float, bool, None]
    weight: float

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Word):
            return False
        return self.value == other.value


@dataclass
class WordLib():
    position_map: Dict[
        WordPosition,
        Set[Word],
    ] = field(init=False)

    def __init__(self, words: List[FuzzWord]):
        # Position-to-domain mapping of the corpus; domain is a Set
        self.position_map = {}
        for word in words:
            self.insert_word(word)

    def __iter__(self):
        return iter(self.position_map.items())

    def brush(self, values: List[Union[str, int, float, bool]], weight: float = 1.0):
        """
        Adjust the weight of all words in the dictionary whose value matches any of the provided values.

        Args:
            values (List[Union[str, int, float, bool]]): Values to match in the dictionary.
            weight (float, optional): New weight for matching words. Defaults to 1.0.

        Returns:
            None

        Note:
            Iterates through all positions and words, updating the weight of any word
            whose value is in the provided list.
        """
        value_set = set(values)
        for pos, words in self.position_map.items():
            for word in words:
                if word.value in value_set:
                    logger.debug(f"brushed {word.value}")
                    word.weight = weight

    @classmethod
    def from_file(cls, input_file: str) -> Self:
        """Load the word library from a JSON file."""
        with open(input_file, "r") as f:
            fuzzwords = msgspec.json.decode(f.read().encode("utf-8"), type=list[FuzzWord])
        return cls(words=fuzzwords)

    @classmethod
    def from_bin(cls, input_file: str) -> 'WordLib':
        """Load the word library from a .bin file (msgpack format)."""
        with open(input_file, 'rb') as f:
            return msgspec.msgpack.decode(f.read(), type=WordLib)

    def show_position_map(self):
        """Print a human-readable view of the position-to-values map."""
        for pos, values in self.position_map.items():
            if isinstance(pos, ApiPosition):
                print(f"{pos.name}: {values}")
            elif isinstance(pos, TablePosition):
                print(f"{pos.table_name}.{pos.col_name}: {values}")
            elif isinstance(pos, ResponsePosition):
                print(f"{pos.where}: {values}") if pos.where != "RAW_RESPONSE" else print("RAW_RESPONSE: [...]")
            elif isinstance(pos, FilePosition):
                print(f"{pos.file_path}: {values}")
            else:
                print(f"Unknown position type: {pos}")

    def insert_word(self, word: FuzzWord):
        """Insert a new FuzzWord and update the domain set."""
        pos = word.position
        if pos not in self.position_map:
            self.position_map[pos] = set()
        try:
            # By default, words not brushed have weight 0
            self.position_map[pos].add(Word(word.value, 0))
        except Exception as e:
            logger.error(e)
            logger.error(f"Error: {word.value} cannot be added to position {pos}")

    def word_list(self) -> List[FuzzWord]:
        """Get all unique FuzzWord items from the word library."""
        fuzzwords = []
        for pos, words in self.position_map.items():
            for w in words:
                one_fuzzword = FuzzWord(
                    value=w.value,
                    position=pos,
                )
                fuzzwords.append(one_fuzzword)
        return fuzzwords

    def dump_bin(self, output_file: str):
        """Export the word library to a .bin file (msgpack format)."""
        with open(output_file, 'wb') as f:
            f.write(msgspec.msgpack.encode(self))

    def get_range(self, pos: WordPosition) -> List[Word]:
        """Get the domain (list of Word) for a given WordPosition."""
        return list(self.position_map.get(pos, set()))

    def get_all_similarities(self, target_pos) -> Dict[WordPosition, float]:
        """Compute Jaccard similarities between the target position's values and all other positions."""

        def norm(x):
            if isinstance(x, str):
                xl = x.lower()
                return xl if xl in ('true', 'false') else x
            return str(x)

        tgt_vals = {norm(w.value) for w in self.position_map.get(target_pos, set())}
        sims = {}
        for pos, words in self.position_map.items():
            if pos == target_pos:
                continue
            cur_vals = {norm(w.value) for w in words}
            u = tgt_vals | cur_vals
            i = tgt_vals & cur_vals
            s = len(i) / len(u) if u else 0.0
            if s > 0.0:
                sims[pos] = s
        return sims

    def get_fileposition_list(self) -> list[FilePosition]:
        """Get all FilePosition keys present in the word library."""
        filepositions = []
        for pos in self.position_map.keys():
            if isinstance(pos, FilePosition):
                filepositions.append(pos)
        return filepositions
