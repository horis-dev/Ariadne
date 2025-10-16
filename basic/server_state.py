import copy
from pathlib import Path
import msgspec

from basic.table import Table
from basic.fuzzword import WordList
from basic.file_data import FileData

class ServerState(msgspec.Struct, tag="server_state"):
    file_state: list[FileData]
    db_state: list[Table]

    def __sub__(self, other) -> 'ServerState':
        if not isinstance(other, ServerState):
            raise TypeError(f"Unsupported operand type for -: 'ServerState' and '{type(other).__name__}'")
        other_file_state_set = set(other.file_state)
        new_file_state = [file_state for file_state in self.file_state if file_state not in other_file_state_set]
        other_db_state_dict = {
            hash(t): t for t in other.db_state
        }
        new_db_state = []
        for table in self.db_state:
            if hash(table) not in other_db_state_dict:
                if table.rows:
                    new_db_state.append(copy.deepcopy(table))
            else:
                table_diff = table - other_db_state_dict[hash(table)]
                if table_diff.rows:
                    new_db_state.append(table_diff)
        return ServerState(
            file_state=new_file_state,
            db_state=new_db_state
        )

    def to_wordlist(self) -> WordList:
        total = WordList([])
        for table in self.db_state:
            w = WordList.from_table(table)
            total.dictionary += w.dictionary
        for file in self.file_state:
            w = file.to_fuzzword()
            total.dictionary += w
        return total
    
    def dump_bin(self, output: str):
        Path(output).write_bytes(msgspec.msgpack.encode(self))
            
class DependedState(ServerState):
    pass