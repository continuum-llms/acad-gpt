from abc import ABC, abstractmethod

from acad_gpt.parsers.config import ParserConfig


class BaseParser(ABC):
    """
    Abstract class for datastores.
    """

    @abstractmethod
    def parse(self, config: ParserConfig):
        raise NotImplementedError
