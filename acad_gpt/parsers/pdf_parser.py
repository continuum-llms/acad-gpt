from typing import Any, Dict, List, Union

from acad_gpt.parsers.base_parser import BaseParser
from acad_gpt.parsers.config import ParserConfig
from acad_gpt.utils.pdf_parser_utils import get_paper_metadata, get_pdf_highlights, post_process_highlights, read_pdf


class PDFParser(BaseParser):
    def parse(self, config: Union[ParserConfig, List[ParserConfig]]) -> List:
        if not isinstance(config, List):
            config = [config]

        parsed_content = []
        for config_item in config:
            file_path = getattr(config_item, "file_path_or_url")
            file = read_pdf(file_path=file_path)

            paper_metadata = get_paper_metadata(file_path=file_path, extract_figures=config_item.extract_figures)
            highlighted_content: Dict[Union[int, str], Any] = {"metadata": paper_metadata}

            for page_number in range(len(file)):
                highlighted_page_content = get_pdf_highlights(file[page_number])
                if len(highlighted_page_content):
                    highlighted_content[page_number] = post_process_highlights(highlighted_page_content)
            parsed_content.append(highlighted_content)
        return parsed_content
