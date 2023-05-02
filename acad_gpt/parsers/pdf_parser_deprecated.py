# """
# pdfannots = "^0.4"
# PyMuPDF = "^1.18.13"
# pillow = "^9.5.0"
# pdf2image = "^1.16.3"
# """

# import json
# import logging
# import os
# import shutil
# from pathlib import Path
# from typing import Any, Dict, List, Union
# from uuid import uuid4

# import numpy as np
# import pdf2image
# import pdfannots
# import pdfminer
# import scipdf
# from PIL import Image, ImageFilter

# from acad_gpt.environment import FILE_UPLOAD_PATH
# from acad_gpt.llm_client.openai.embedding.embedding_client import EmbeddingClient
# from acad_gpt.parsers.base_parser import BaseParser, Document, DocumentType
# from acad_gpt.parsers.config import ParserConfig, PDFColumnClassifierConfig

# logger = logging.getLogger(__name__)


# class PDFParser(BaseParser):
#     def parse(self, config: Union[ParserConfig, List[ParserConfig]]) -> Dict:
#         if not isinstance(config, List):
#             config = [config]

#         parsed_content: Dict[str, Any] = {}
#         for config_item in config:
#             file_path = getattr(config_item, "file_path_or_url")
#             extract_highlights = getattr(config_item, "extract_highlights")
#             pdf_metadata, metadata_path = PDFParser.get_pdf_metadata(
#                 file_path=file_path, extract_figures=config_item.extract_figures
#             )
#             pdf_metadata["file_name"] = os.path.basename(file_path)
#             pdf_metadata["url"] = file_path
#             parsed_content = {
#                 "metadata": pdf_metadata,
#                 "metadata_path": metadata_path if config_item.extract_figures else None,
#             }
#             if extract_highlights:
#                 pdf_layout = 2 if PDFParser.classify_pdf_from_path(pdf_path=file_path) else 1
#                 parsed_content["highlights"] = PDFParser.get_pdf_highlights(file_path=file_path, pdf_layout=pdf_layout)

#         return parsed_content

#     @staticmethod
#     def get_pdf_highlights(file_path: str, pdf_layout: int) -> List[Dict]:
#         highlights: List[Dict] = []
#         path = Path(file_path)
#         laparams = pdfminer.layout.LAParams()
#         with path.open("rb") as f:
#             doc = pdfannots.process_file(f, columns_per_page=pdf_layout, laparams=laparams)
#         for page in doc.pages:
#             for annotation in page.annots:
#                 try:
#                     highlights.append(
#                         {
#                             "text": annotation.gettext(remove_hyphens=True),
#                             "page": annotation.pos.page.pageno + 1,
#                             "regionBoundary": [annotation.pos.x, annotation.pos.y],
#                         }
#                     )
#                 except Exception:
#                     continue
#         return highlights

#     @staticmethod
#     def get_pdf_metadata(file_path: str, extract_figures: bool = False, figures_directory: str = FILE_UPLOAD_PATH):
#         pdf_metadata = None
#         try:
#             pdf_metadata = scipdf.parse_pdf_to_dict(file_path)
#             if extract_figures:
#                 isExist = os.path.exists(figures_directory)
#                 if not isExist:
#                     # create the metadata directory because it does not exist
#                     os.makedirs(figures_directory)

#                 # folder should contain only PDF files
#                 scipdf.parse_figures(file_path, output_folder=figures_directory)
#                 # TODO: clean up extracted images after storing them in object storage
#         except Exception as error:
#             logger.error(error)
#         return pdf_metadata, figures_directory

#     def pdf_to_documents(
#         self,
#         pdf_contents: Dict,
#         embed_client: EmbeddingClient,
#         file_name: str,
#         clean_up: bool = True,
#         extract_highlights: bool = False,
#     ) -> List[Dict]:
#         metadata_path = pdf_contents.pop("metadata_path")
#         documents = []
#         metadata = dict(pdf_contents.pop("metadata")) if pdf_contents.get("metadata") else None
#         document_id = metadata.get("file_name") if metadata else None
#         url = metadata.get("file_name", "")
#         title = metadata.pop("title", "")
#         if metadata and metadata_path:
#             abstract = metadata.pop("abstract")
#             sections = "\n".join([section.get("text", "") for section in metadata.pop("sections", [])])
#             embedding = (
#                 embed_client.embed_documents(docs=[{"text": f"{title} \n  Abstract: \n  {abstract}"}])[0]
#                 .astype(np.float32)
#                 .tobytes()
#             )
#             abstract_doc = Document(
#                 text=f"{abstract} {sections}",
#                 title=title,
#                 type=DocumentType.paper,
#                 url=url,
#                 embedding=embedding,
#             ).dict()

#             documents = [abstract_doc]
#         if "highlights" in pdf_contents:
#             for section in sections:
#                 section_name = section.get("heading", "")
#                 text = section.get("text", "")
#                 embedding = (
#                     embed_client.embed_documents(docs=[{"text": f"{title} \n {section_name}: \n  {text}"}])[0]
#                     .astype(np.float32)
#                     .tobytes()
#                 )
#                 document = Document(
#                     document_id=document_id,
#                     section=section_name,
#                     text=text,
#                     title=title,
#                     type="Section",
#                     page=0,
#                     embedding=embedding,
#                     regionBoundary="",
#                 )
#                 documents.append(document.dict())

#             with open(f"{metadata_path}/data/{file_name}.json") as user_file:
#                 file_contents = user_file.read()

#             for doc in json.loads(file_contents):
#                 text = doc.get("caption", "")
#                 embedding = (
#                     embed_client.embed_documents(docs=[{"text": f"{title} \n {text}"}])[0].astype(np.float32).tobytes()
#                 )
#                 document = Document(
#                     document_id=uuid4().hex,
#                     section="",
#                     text=text,
#                     title=title,
#                     type=doc.get("figType", ""),
#                     page=int(doc.get("page", "")),
#                     embedding=embedding,
#                     regionBoundary=str(doc.get("regionBoundary", "")),
#                 )
#                 documents.append(document.dict())
#             for doc in pdf_contents["highlights"]:
#                 text = doc.get("text", "")
#                 embedding = (
#                     embed_client.embed_documents(docs=[{"text": f"{title} \n  {text}"}])[0].astype(np.float32).tobytes()
#                 )
#                 document = Document(
#                     document_id=uuid4().hex,
#                     section="",
#                     text=text,
#                     title=title,
#                     type="Highlight",
#                     page=int(doc.get("page", -1)),
#                     embedding=embedding,
#                     regionBoundary=str(doc.get("regionBoundary", "")),
#                 )
#                 documents.append(document.dict())
#         if clean_up and os.path.exists(f"{FILE_UPLOAD_PATH}"):
#             shutil.rmtree(FILE_UPLOAD_PATH)
#         return documents

#     @staticmethod
#     def classify_pdf_from_path(
#         pdf_path: Union[str, Path], config: PDFColumnClassifierConfig = PDFColumnClassifierConfig()
#     ) -> bool:
#         """
#         Classify a PDF as either single-column or two-column.

#         Args:
#             pdf_path: The PDF to classify.
#             config: The configuration to use when classifying the PDF. Uses the default configuration if not specified.

#         Returns:
#             True if the PDF is two-column, False otherwise.
#         """
#         # first, convert the PDF to a list of images.
#         imgs = pdf2image.convert_from_path(pdf_path, dpi=config.dpi, **config.pdf_conversion_options.dict())
#         return PDFParser._classify_imgs(imgs, config)

#     @staticmethod
#     def classify_pdf_from_bytes(
#         pdf_bytes: bytes, config: PDFColumnClassifierConfig = PDFColumnClassifierConfig()
#     ) -> bool:
#         """
#         Classify a PDF as either single-column or two-column.

#         Args:
#             pdf_bytes: The PDF as bytes to classify.
#             config: The configuration to use when classifying the PDF. Uses the default configuration if not specified.

#         Returns:
#             True if the PDF is two-column, False otherwise.
#         """
#         # first, convert the PDF to a list of images.
#         imgs = pdf2image.convert_from_bytes(pdf_bytes, dpi=config.dpi, **config.pdf_conversion_options.dict())
#         return PDFParser._classify_imgs(imgs, config)

#     @staticmethod
#     def _classify_imgs(imgs: List[Any], config: PDFColumnClassifierConfig) -> bool:
#         """
#         Classify a list of images as either single-column or two-column.

#         Args:
#             imgs: The images to classify.
#             config: The configuration to use when classifying the images.

#         Returns:
#             True if the images are two-column, False otherwise.
#         """
#         # classify each image in the PDF as either single-column or two-column.
#         votes = []
#         for img in imgs:
#             # apply erosion to make the text more prominent
#             if config.erosion_kernel_size > 1:
#                 img = img.filter(ImageFilter.MinFilter(config.erosion_kernel_size))

#             # calculate the percentage of whitish pixels in the middle of the image
#             percentage_whitish_in_middle = PDFParser._calc_percentage_whitish_in_middle(img, config.middle_column_width)

#             # if the percentage of whitish pixels in the middle of the
#             # image is greater than VOTE_THRESHOLD, then the image is two-column.
#             vote = percentage_whitish_in_middle > config.vote_threshold

#             # add the vote to list
#             votes.append(vote)

#         # if the majority of the images in the PDF are classified as two-column, then the PDF is two-column.
#         return sum(votes) > len(votes) // 2

#     @staticmethod
#     def _calc_percentage_whitish_in_middle(img: Image, middle_column_width: int) -> float:
#         """
#         Calculate the percentage of whitish pixels in the middle of the image.

#         Args:
#             img: The image to calculate the percentage of whitish pixels in the middle of.
#             middle_column_width: The width of the middle column to calculate the percentage of whitish pixels in.

#         Returns:
#             The percentage of whitish pixels in the middle of the image.
#         """
#         img = img.convert("L")
#         middle_column = img.crop(
#             (img.width // 2 - middle_column_width // 2, 0, img.width // 2 + middle_column_width // 2, img.height)
#         )
#         middle_column = middle_column.point(lambda x: 0 if x < 150 else 255, mode="1")
#         return np.array(middle_column).mean()
