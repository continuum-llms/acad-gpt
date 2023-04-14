from enum import Enum

from pydantic import BaseModel


class FileType(str, Enum):
    md = "MD"
    pdf = "PDF"


class ParserConfig(BaseModel):
    file_path_or_url: str
    file_type: FileType
    extract_figures: bool = False
