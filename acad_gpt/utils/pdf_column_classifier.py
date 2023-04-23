"""
This module contains a function for classifying a PDF as either single-column or two-column.

The classification is based on simple heuristics, and is not guaranteed to be accurate.

It is done as follows:
1. Convert the PDF to a list of images.
2. For each image, calculate the percentage of whitish pixels in the middle of the image.
3. If the percentage of whitish pixels in the middle of the image is greater than `VOTE_THRESHOLD`,
    then the image is two-column.
4. If the majority of the images in the PDF are classified as two-column, then the PDF is two-column.
"""
from pathlib import Path
from typing import List, Union

import numpy as np
import pdf2image
from PIL import Image, ImageFilter

__all__ = ["classify_pdf_from_path", "classify_pdf_from_bytes"]


DEFAULT_DPI = 50
DEFAULT_MIDDLE_COLUMN_WIDTH = 2

EROSION_KERNEL_SIZE = 5
VOTE_THRESHOLD = 0.7

MAX_PAGES = 5

PDF_CONVERSION_OPTIONS = dict(
    grayscale=True,
    hide_annotations=True,
    paths_only=True,
    last_page=MAX_PAGES,
)


def classify_pdf_from_path(pdf_path: Union[str, Path], dpi: int = DEFAULT_DPI) -> bool:
    """
    Classify a PDF as either single-column or two-column.

    Args:
        pdf_path: The PDF to classify.
        dpi: The DPI to use when converting the PDF to images. Defaults to DEFAULT_DPI (50).

    Returns:
        True if the PDF is two-column, False otherwise.
    """
    # first, convert the PDF to a list of images.
    imgs = pdf2image.convert_from_path(pdf_path, dpi=dpi, **PDF_CONVERSION_OPTIONS)
    return _classify_imgs(imgs)


def classify_pdf_from_bytes(pdf_bytes: bytes, dpi: int = DEFAULT_DPI) -> bool:
    """
    Classify a PDF as either single-column or two-column.

    Args:
        pdf_bytes: The PDF as bytes to classify.
        dpi: The DPI to use when converting the PDF to images. Defaults to DEFAULT_DPI (50).

    Returns:
        True if the PDF is two-column, False otherwise.
    """
    # first, convert the PDF to a list of images.
    imgs = pdf2image.convert_from_bytes(pdf_bytes, dpi=dpi, **PDF_CONVERSION_OPTIONS)
    return _classify_imgs(imgs)


def _classify_imgs(imgs: List[Image]) -> bool:
    """
    Classify a list of images as either single-column or two-column.

    Args:
        imgs: The images to classify.

    Returns:
        True if the images are two-column, False otherwise.
    """
    # classify each image in the PDF as either single-column or two-column.
    votes = []
    for img in imgs:
        # TODO: should we consider image pdfs? (we're not considering doing OCR anyways)
        # apply erosion to make the text more prominent
        if EROSION_KERNEL_SIZE > 1:
            img = img.filter(ImageFilter.MinFilter(EROSION_KERNEL_SIZE))

        # calculate the percentage of whitish pixels in the middle of the image
        percentage_whitish_in_middle = _calc_percentage_whitish_in_middle(img)

        # if the percentage of whitish pixels in the middle of the
        # image is greater than VOTE_THRESHOLD, then the image is two-column.
        vote = percentage_whitish_in_middle > VOTE_THRESHOLD

        # add the vote to list
        votes.append(vote)

    # if the majority of the images in the PDF are classified as two-column, then the PDF is two-column.
    return sum(votes) > len(votes) // 2


def _calc_percentage_whitish_in_middle(img: Image, middle_column_width: int = DEFAULT_MIDDLE_COLUMN_WIDTH) -> float:
    """
    Calculate the percentage of whitish pixels in the middle of the image.

    Args:
        img: The image to calculate the percentage of whitish pixels in the middle of.
        middle_column_width: The width of the middle column to calculate the percentage of whitish pixels in.
            Defaults to DEFAULT_MIDDLE_COLUMN_WIDTH (2).

    Returns:
        The percentage of whitish pixels in the middle of the image.
    """
    img = img.convert("L")
    middle_column = img.crop(
        (img.width // 2 - middle_column_width // 2, 0, img.width // 2 + middle_column_width // 2, img.height)
    )
    middle_column = middle_column.point(lambda x: 0 if x < 150 else 255, mode="1")
    return np.array(middle_column).mean()
