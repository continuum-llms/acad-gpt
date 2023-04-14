from typing import Dict, List, Union

from acad_gpt.parsers.base_parser import BaseParser
from acad_gpt.parsers.config import PDFParserConfig
from acad_gpt.utils.pdf_parser_utils import get_pdf_highlights, post_process_highlights, read_pdf


class PDFParser(BaseParser):
    def parse(self, config: Union[PDFParserConfig, List[PDFParserConfig]]) -> Dict:
        if not isinstance(config, List):
            config = [config]

        highlighted_content = {}
        for config_item in config:
            file_path = getattr(config_item, "file_path_or_url")
            file = read_pdf(file_path=file_path)

            for page_number in range(len(file)):
                highlighted_page_content = get_pdf_highlights(file[page_number])
                if len(highlighted_page_content):
                    highlighted_content[page_number] = post_process_highlights(highlighted_page_content)

        return highlighted_content
