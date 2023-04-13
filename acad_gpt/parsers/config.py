from enum import Enum
from typing import Optional

from pydantic import BaseModel


class FileType(str, Enum):
    md = "MD"
    pdf = "PDF"


class ParserConfig(BaseModel):
    file_path_or_url: str
    file_type: FileType
    file_title: Optional[str]
