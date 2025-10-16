from dataclasses import dataclass
from enum import Enum

import msgspec

from api.api_node import ApiNode

class EdgeType(str, Enum):
    DATABASE = "DATABASE"
    FILE = "FILE"
    RESPONSE = "RESPONSE"


class Edge(msgspec.Struct, tag="edge"):
    src: ApiNode
    dst: ApiNode
    typ: EdgeType
    w: float

    def __hash__(self) -> int:
        return hash((self.src, self.dst, self.typ))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return False
        return self.src == other.src and self.dst == other.dst and self.typ == other.typ
