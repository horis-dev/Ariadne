from typing import Any, Self, Union, Optional
import msgspec

from basic.position import ApiPosition, TablePosition, ResponsePosition, FilePosition
from basic.table import Table

class MutateValue(msgspec.Struct, tag="mutate_value", frozen=True):
    val: Union[str, int, float, bool]
    is_ref: bool = False
    # Reference type, pointing to a local corpus of a specific API in the sequence
    api_index: int = -1
    pos: Optional[ApiPosition | ResponsePosition] = None

class FuzzWord(msgspec.Struct, tag="fuzz_word"):
    value: Any
    position: ApiPosition | TablePosition | ResponsePosition | FilePosition

class WordList(msgspec.Struct, tag="word_list"):
    dictionary: list[FuzzWord]

    @classmethod
    def from_table(cls, table: Table) -> Self:
        d: list[FuzzWord] = []
        for row in table.rows:
            for j, value in enumerate(row):
                if value == "None" or value == "null" or value == "NaN" or value == "":
                    continue
                if isinstance(value, str):
                    value = value[:1000]  # Truncate overly long values
                word = FuzzWord(
                    value=value,
                    position=TablePosition(
                        table.table_name,
                        table.columns[j]
                    )
                )
                d.append(word)
        return cls(dictionary=d)
