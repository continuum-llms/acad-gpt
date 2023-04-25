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


class PDF2ImageConversionOptions(BaseModel):
    grayscale: bool = True
    hide_annotations: bool = True
    paths_only: bool = True
    last_page: int = 5


class PDFColumnClassifierConfig(BaseModel):
    dpi: int = 50
    middle_column_width: int = 2
    erosion_kernel_size: int = 5
    vote_threshold: float = 0.7

    pdf_conversion_options: PDF2ImageConversionOptions = PDF2ImageConversionOptions()
