from abc import ABC, abstractmethod
from typing import Any


class BaseParser(ABC):
    """
    Abstract class for datastores.
    """

    @abstractmethod
    def parse(self, config: Any):
        raise NotImplementedError
