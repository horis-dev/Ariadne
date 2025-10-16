from abc import ABC, abstractmethod
from typing import Set

from api.api_node import ApiNode

class Docable(ABC):
    @abstractmethod
    def get_nodes(self) -> Set[ApiNode]:
        pass