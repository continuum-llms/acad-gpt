from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel

from acad_gpt.parsers.config import ParserConfig


class DocumentType(str, Enum):
    paper = "paper"
    code = "code"
    webpage = "webpage"
    pdf = "pdf"


class DocumentStatus(str, Enum):
    todo = "todo"
    done = "done"


class Document(BaseModel):
    text: str
    title: str
    type: str
    url: str
    embedding: Any
    status: str = DocumentStatus.todo


class BaseParser(ABC):
    """
    Abstract class for datastores.
    """

    @abstractmethod
    def parse(self, config: ParserConfig):
        raise NotImplementedError
