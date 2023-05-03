import logging
from typing import Dict

import numpy as np
import requests
from bs4 import BeautifulSoup, Comment

from acad_gpt.llm_client.openai.embedding.embedding_client import EmbeddingClient
from acad_gpt.parsers.base_parser import BaseParser, Document, DocumentStatus, DocumentType
from acad_gpt.parsers.config import ParserConfig

logger = logging.getLogger(__name__)


class WebPageParser(BaseParser):
    def parse(self, config: ParserConfig) -> Dict:
        self.config = config

        # parse the webpage
        title = self.get_title()
        text = self.get_text()

        return {"title": title, "text": text, "url": self.config.file_url}

    def get_title(self):
        reqs = requests.get(self.config.file_url)
        soup = BeautifulSoup(reqs.text, "html.parser")

        for title in soup.find_all("title"):
            if title.get_text():
                return title.get_text()
            else:
                return ""

    def get_text(self):
        reqs = requests.get(self.config.file_url)
        soup = BeautifulSoup(reqs.text, "html.parser")
        texts = soup.findAll(text=True)
        visible_texts = filter(WebPageParser.tag_visible, texts)
        return " ".join(t.strip() for t in visible_texts)

    @staticmethod
    def tag_visible(element):
        if element.parent.name in ["style", "script", "head", "title", "meta", "[document]"]:
            return False
        if isinstance(element, Comment):
            return False
        return True

    def to_documents(
        self,
        web_contents: Dict,
        embed_client: EmbeddingClient,
        type: str = DocumentType.webpage,
        status: str = DocumentStatus.todo,
        **kwargs,
    ) -> Dict:
        document = {}

        url = web_contents.get("url", "")
        title = web_contents.pop("title", "")
        text = web_contents.pop("text", "")[:4500]
        embedding = embed_client.embed_documents(docs=[{"text": text}])[0].astype(np.float32).tobytes()
        document = Document(
            text=text,
            title=title,
            url=url,
            type=type,
            embedding=embedding,
            status=status,
        ).dict()

        return document
