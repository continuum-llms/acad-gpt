from pydantic import BaseModel


class ParserConfig(BaseModel):
    file_path: str
    file_url: str


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
