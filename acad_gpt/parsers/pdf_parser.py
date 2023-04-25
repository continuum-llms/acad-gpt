from pathlib import Path
from typing import Dict, List, Union

import numpy as np
import pdf2image
from PIL import Image, ImageFilter

from acad_gpt.parsers.base_parser import BaseParser
from acad_gpt.parsers.config import ParserConfig, PDFColumnClassifierConfig
from acad_gpt.utils.pdf_parser_utils import get_pdf_highlights, post_process_highlights, read_pdf


class PDFParser(BaseParser):
    def parse(self, config: Union[ParserConfig, List[ParserConfig]]) -> Dict:
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

    @staticmethod
    def classify_pdf_from_path(
        pdf_path: Union[str, Path], config: PDFColumnClassifierConfig = PDFColumnClassifierConfig()
    ) -> bool:
        """
        Classify a PDF as either single-column or two-column.

        Args:
            pdf_path: The PDF to classify.
            config: The configuration to use when classifying the PDF. Uses the default configuration if not specified.

        Returns:
            True if the PDF is two-column, False otherwise.
        """
        # first, convert the PDF to a list of images.
        imgs = pdf2image.convert_from_path(pdf_path, dpi=config.dpi, **config.pdf_conversion_options.dict())
        return PDFParser._classify_imgs(imgs, config)

    @staticmethod
    def classify_pdf_from_bytes(
        pdf_bytes: bytes, config: PDFColumnClassifierConfig = PDFColumnClassifierConfig()
    ) -> bool:
        """
        Classify a PDF as either single-column or two-column.

        Args:
            pdf_bytes: The PDF as bytes to classify.
            config: The configuration to use when classifying the PDF. Uses the default configuration if not specified.

        Returns:
            True if the PDF is two-column, False otherwise.
        """
        # first, convert the PDF to a list of images.
        imgs = pdf2image.convert_from_bytes(pdf_bytes, dpi=config.dpi, **config.pdf_conversion_options.dict())
        return PDFParser._classify_imgs(imgs, config)

    @staticmethod
    def _classify_imgs(imgs: List[Image], config: PDFColumnClassifierConfig) -> bool:
        """
        Classify a list of images as either single-column or two-column.

        Args:
            imgs: The images to classify.
            config: The configuration to use when classifying the images.

        Returns:
            True if the images are two-column, False otherwise.
        """
        # classify each image in the PDF as either single-column or two-column.
        votes = []
        for img in imgs:
            # apply erosion to make the text more prominent
            if config.erosion_kernel_size > 1:
                img = img.filter(ImageFilter.MinFilter(config.erosion_kernel_size))

            # calculate the percentage of whitish pixels in the middle of the image
            percentage_whitish_in_middle = PDFParser._calc_percentage_whitish_in_middle(img, config.middle_column_width)

            # if the percentage of whitish pixels in the middle of the
            # image is greater than VOTE_THRESHOLD, then the image is two-column.
            vote = percentage_whitish_in_middle > config.vote_threshold

            # add the vote to list
            votes.append(vote)

        # if the majority of the images in the PDF are classified as two-column, then the PDF is two-column.
        return sum(votes) > len(votes) // 2

    @staticmethod
    def _calc_percentage_whitish_in_middle(img: Image, middle_column_width: int) -> float:
        """
        Calculate the percentage of whitish pixels in the middle of the image.

        Args:
            img: The image to calculate the percentage of whitish pixels in the middle of.
            middle_column_width: The width of the middle column to calculate the percentage of whitish pixels in.

        Returns:
            The percentage of whitish pixels in the middle of the image.
        """
        img = img.convert("L")
        middle_column = img.crop(
            (img.width // 2 - middle_column_width // 2, 0, img.width // 2 + middle_column_width // 2, img.height)
        )
        middle_column = middle_column.point(lambda x: 0 if x < 150 else 255, mode="1")
        return np.array(middle_column).mean()
