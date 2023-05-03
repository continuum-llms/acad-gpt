import logging
import os
import shutil
from typing import Any, Dict, List, Union

import numpy as np
import scipdf

from acad_gpt.environment import FILE_UPLOAD_PATH
from acad_gpt.llm_client.openai.embedding.embedding_client import EmbeddingClient
from acad_gpt.parsers.base_parser import BaseParser, Document, DocumentStatus, DocumentType
from acad_gpt.parsers.config import ParserConfig

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    def parse(self, config: Union[ParserConfig, List[ParserConfig]]) -> Dict:
        if not isinstance(config, List):
            config = [config]

        parsed_content: Dict[str, Any] = {}
        for config_item in config:
            file_path = getattr(config_item, "file_path")

            pdf_metadata = PDFParser.get_pdf_metadata(file_path=file_path)
            pdf_metadata["file_name"] = os.path.basename(file_path)
            pdf_metadata["url"] = getattr(config_item, "file_url")

            parsed_content = {
                "metadata": pdf_metadata,
            }

        return parsed_content

    @staticmethod
    def get_pdf_metadata(file_path: str, figures_directory: str = FILE_UPLOAD_PATH):
        pdf_metadata = None

        try:
            pdf_metadata = scipdf.parse_pdf_to_dict(file_path)
        except Exception as error:
            logger.error(error)

        return pdf_metadata

    def to_documents(
        self,
        pdf_contents: Dict,
        embed_client: EmbeddingClient,
        type: str = DocumentType.pdf,
        status: str = DocumentStatus.todo,
        **kwargs,
    ) -> Dict:
        document = {}
        clean_up = bool(kwargs.get("clean_up", True))

        metadata = dict(pdf_contents.pop("metadata")) if pdf_contents.get("metadata") else None
        url = metadata.get("url", "")
        title = metadata.pop("title", "")

        if metadata:
            abstract = metadata.pop("abstract")
            sections = "\n".join([section.get("text", "") for section in metadata.pop("sections", [])])
            embedding = (
                embed_client.embed_documents(docs=[{"text": f"{title} \n  {abstract} \n  {sections}"}])[0]
                .astype(np.float32)
                .tobytes()
            )
            document = Document(
                text=abstract,
                title=title,
                type=type,
                url=url,
                status=status,
                embedding=embedding,
            ).dict()

        if clean_up and os.path.exists(f"{FILE_UPLOAD_PATH}"):
            shutil.rmtree(FILE_UPLOAD_PATH)

        return document
