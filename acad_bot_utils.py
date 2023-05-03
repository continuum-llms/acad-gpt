import os

import requests

from acad_gpt.environment import FILE_UPLOAD_PATH
from acad_gpt.parsers import DocumentType
from acad_gpt.parsers.base_parser import DocumentStatus
from acad_gpt.parsers.config import ParserConfig
from acad_gpt.parsers.pdf_parser import PDFParser
from acad_gpt.parsers.webpage_parser import WebPageParser


def get_url_type(url):
    if url.split(".")[-1].strip() == "pdf":
        return DocumentType.pdf, url
    else:
        return DocumentType.webpage, url


def download(url: str):
    if not os.path.exists(FILE_UPLOAD_PATH):
        os.makedirs(FILE_UPLOAD_PATH)  # create folder if it does not exist

    filename = url.split("/")[-1].replace(" ", "_")  # be careful with file names
    file_path = os.path.join(FILE_UPLOAD_PATH, filename)

    r = requests.get(url, stream=True)
    is_saved = False
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
            is_saved = True
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))
    return is_saved, file_path


def process_url(
    url,
    type,
    embed_client,
    status=DocumentStatus.todo,
):
    document = None
    if type in [DocumentType.pdf, DocumentType.paper]:
        is_saved, file_path = download(url)
        if is_saved:
            parser = PDFParser()
            parser_config = ParserConfig(file_path=file_path, file_url=url)
            results = parser.parse(config=parser_config)
            document = parser.to_documents(
                pdf_contents=results,
                embed_client=embed_client,
                type=type,
                status=status,
            )
    else:
        parser = WebPageParser()
        parser_config = ParserConfig(file_path=url, file_url=url)
        results = parser.parse(config=parser_config)
        document = parser.to_documents(
            web_contents=results,
            embed_client=embed_client,
            type=type,
            status=status,
        )
    return document
