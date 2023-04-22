"""
https://medium.com/@vinitvaibhav9/extracting-pdf-highlights-using-python-9512af43a6d
"""

import json
import os
import shutil
from typing import Any, Dict, List, Tuple, Union
from uuid import uuid4

import fitz
import numpy as np
import scipdf
from pydantic import BaseModel

from acad_gpt.environment import FILE_UPLOAD_PATH
from acad_gpt.llm_client.openai.embedding.embedding_client import EmbeddingClient
from acad_gpt.parsers.base_parser import BaseParser
from acad_gpt.parsers.config import ParserConfig


class Document(BaseModel):
    document_id: str
    text: str
    title: str
    type: str
    page: int
    regionBoundary: str
    section: str
    embedding: Any


class PDFParser(BaseParser):
    def parse(self, config: Union[ParserConfig, List[ParserConfig]]) -> Dict:
        if not isinstance(config, List):
            config = [config]

        parsed_content: Dict[str, Any] = {}
        for config_item in config:
            file_path = getattr(config_item, "file_path_or_url")
            file = PDFParser.read_pdf(file_path=file_path)

            paper_metadata, metadata_path = PDFParser.get_paper_metadata(
                file_path=file_path, extract_figures=config_item.extract_figures
            )
            parsed_content = {"metadata": paper_metadata, "metadata_path": metadata_path}
            parsed_content["highlights"] = []
            for page_number in range(len(file)):
                highlighted_page_content = PDFParser.get_pdf_highlights(file[page_number])
                if len(highlighted_page_content):
                    parsed_content["highlights"].append(
                        {"text": PDFParser.post_process_highlights(highlighted_page_content), "page": page_number + 1}
                    )
        return parsed_content

    @staticmethod
    def read_pdf(file_path: str):
        file = fitz.open(file_path)
        return file

    @staticmethod
    def get_pdf_highlights(page: Any) -> List:
        wordlist = page.get_text("words")  # list of words on page
        wordlist.sort(key=lambda w: (w[3], w[0]))  # ascending y, then x

        highlights = []
        annot = page.first_annot
        while annot:
            if annot.type[0] == 8:
                highlights.append(PDFParser.parse_highlight(annot, wordlist))
            annot = annot.next
        return highlights

    @staticmethod
    def parse_highlight(
        annot: fitz.Annot, wordlist: List[Tuple[float, float, float, float, str, int, int, int]]
    ) -> str:
        points = annot.vertices
        quad_count = int(len(points) / 4)
        sentences = []
        for i in range(quad_count):
            # where the highlighted part is
            r = fitz.Quad(points[i * 4 : i * 4 + 4]).rect

            words = [w for w in wordlist if fitz.Rect(w[:4]).intersects(r)]
            sentences.append(" ".join(w[4] for w in words))
        sentence = " ".join(sentences)
        return sentence

    @staticmethod
    def jaccard(a, b):
        c = a.intersection(b)
        return float(len(c)) / (len(a) + len(b) - len(c))

    @staticmethod
    def post_process_highlights(highights: List) -> str:
        post_processed_highlights = ""
        jaccard_score = 0.0
        for index in range(len(highights) - 1):
            highlight_i = set(highights[index][-60:].split())
            highlight_j = set(highights[index + 1].split()[: len(highlight_i)])

            jaccard_score = PDFParser.jaccard(highlight_i, highlight_j)
            if jaccard_score > 0.5:
                post_processed_highlights += " " + highights[index][:-60]
            else:
                post_processed_highlights += " " + highights[index]
        post_processed_highlights += " " + highights[-1]

        return post_processed_highlights

    @staticmethod
    def get_paper_metadata(file_path: str, extract_figures: bool = False, figures_directory: str = FILE_UPLOAD_PATH):
        paper_metadata = scipdf.parse_pdf_to_dict(file_path)
        if extract_figures:
            isExist = os.path.exists(figures_directory)
            if not isExist:
                # create the metadata directory because it does not exist
                os.makedirs(figures_directory)

            # folder should contain only PDF files
            scipdf.parse_figures(file_path, output_folder=figures_directory)
            # TODO: clean up extracted images after storing them in object storage
        return paper_metadata, figures_directory

    def pdf_to_documents(
        self, pdf_contents: Dict, embed_client: EmbeddingClient, file_name: str, clean_up: bool = True
    ) -> List[Dict]:
        title = ""
        metadata_path = pdf_contents.pop("metadata_path")
        documents = []
        document_id = uuid4().hex
        metadata = dict(pdf_contents.pop("metadata"))
        title = metadata.pop("title")
        sections = metadata.pop("sections")
        abstract = metadata.pop("abstract")
        embedding = (
            embed_client.embed_documents(docs=[{"text": f"{title} \n  Abstract: \n  {abstract}"}])[0]
            .astype(np.float32)
            .tobytes()
        )
        abstract_doc = Document(
            document_id=document_id,
            section="Abstract",
            text=f"{abstract}",
            title=title,
            type="Section",
            page=0,
            regionBoundary="",
            embedding=embedding,
        ).dict()

        documents = [abstract_doc]
        for section in sections:
            section_name = section.get("heading", "")
            text = section.get("text", "")
            embedding = (
                embed_client.embed_documents(docs=[{"text": f"{title} \n {section_name}: \n  {text}"}])[0]
                .astype(np.float32)
                .tobytes()
            )
            document = Document(
                document_id=document_id,
                section=section_name,
                text=text,
                title=title,
                type="section",
                page=0,
                embedding=embedding,
                regionBoundary="",
            )
            documents.append(document.dict())

        with open(f"{metadata_path}/data/{file_name}.json") as user_file:
            file_contents = user_file.read()

        for doc in json.loads(file_contents):
            text = doc.get("caption", "")
            embedding = (
                embed_client.embed_documents(docs=[{"text": f"{title} \n {text}"}])[0].astype(np.float32).tobytes()
            )
            document = Document(
                document_id=uuid4().hex,
                section="",
                text=text,
                title=title,
                type=doc.get("figType", ""),
                page=int(doc.get("page", "")),
                embedding=embedding,
                regionBoundary=str(doc.get("regionBoundary", "")),
            )
            documents.append(document.dict())

        for doc in pdf_contents["highlights"]:
            text = doc.get("text", "")
            embedding = (
                embed_client.embed_documents(docs=[{"text": f"{title} \n  {text}"}])[0].astype(np.float32).tobytes()
            )
            document = Document(
                document_id=uuid4().hex,
                section="",
                text=text,
                title=title,
                type="Highlight",
                page=int(doc.get("page", "")),
                embedding=embedding,
                regionBoundary="",
            )
            documents.append(document.dict())

            if clean_up and os.path.exists(FILE_UPLOAD_PATH):
                shutil.rmtree(FILE_UPLOAD_PATH)
        return documents
