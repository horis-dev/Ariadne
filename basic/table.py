import copy
import csv
from typing import Any, List
import pandas as pd
import msgspec

from basic.exception import TableSubstractError


class Table(msgspec.Struct, tag="table"):
    table_name: str
    is_file: bool
    columns: List[str]
    rows: List[List[Any]]

    def __hash__(self) -> int:
        return hash((self.table_name, self.is_file))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Table):
            return False
        return (self.table_name, self.is_file) == (other.table_name, other.is_file)

    def __sub__(self, other) -> 'Table':
        if not isinstance(other, Table):
            raise TypeError(f"Unsupported operand type for -: 'Table' and '{type(other).__name__}'")
        if self.table_name != other.table_name:
            raise TableSubstractError(
                f"The tables being subtracted must have the same table name: {self.table_name} != {other.table_name}")
        other_rows_set = set(map(tuple, other.rows))
        new_rows = [copy.deepcopy(row) for row in self.rows if tuple(row) not in other_rows_set]
        return Table(
            table_name=self.table_name,
            is_file=self.is_file,
            columns=self.columns,
            rows=new_rows
        )

    @classmethod
    def from_csv(cls, csv_path: str, table_name: str):
        with open(csv_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            columns = next(reader)  # Read the first row as column names
            rows = [row for row in reader]  # Read remaining rows as data
        return cls(table_name=table_name, columns=columns, rows=rows, is_file=True)

    @classmethod
    # Convert from pandas DataFrame to Table
    def from_pd_dataframe(cls, df: pd.DataFrame, table_name: str):
        df_str = df.fillna("").astype(str)
        columns = list(df_str.columns)
        rows = df_str.values.tolist()
        return cls(
            table_name=table_name,
            columns=columns,
            rows=rows,
            is_file=False
        )
