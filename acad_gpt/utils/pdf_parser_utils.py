import os
from typing import Any, List, Tuple

import fitz
import scipdf

"""
https://medium.com/@vinitvaibhav9/extracting-pdf-highlights-using-python-9512af43a6d
"""


def read_pdf(file_path: str):
    file = fitz.open(file_path)
    return file


def get_pdf_highlights(page: Any) -> List:
    wordlist = page.get_text("words")  # list of words on page
    wordlist.sort(key=lambda w: (w[3], w[0]))  # ascending y, then x

    highlights = []
    annot = page.first_annot
    while annot:
        if annot.type[0] == 8:
            highlights.append(_parse_highlight(annot, wordlist))
        annot = annot.next
    return highlights


def _parse_highlight(annot: fitz.Annot, wordlist: List[Tuple[float, float, float, float, str, int, int, int]]) -> str:
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


def jaccard(a, b):
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))


def post_process_highlights(highights: List) -> str:
    post_processed_highlights = ""
    jaccard_score = 0.0
    for index in range(len(highights) - 1):
        highlight_i = set(highights[index][-60:].split())
        highlight_j = set(highights[index + 1].split()[: len(highlight_i)])

        jaccard_score = jaccard(highlight_i, highlight_j)
        if jaccard_score > 0.5:
            post_processed_highlights += " " + highights[index][:-60]
        else:
            post_processed_highlights += " " + highights[index]
    post_processed_highlights += " " + highights[-1]

    return post_processed_highlights


def get_paper_metadata(
    file_path: str, extract_figures: bool = False, figures_directory: str = "/examples/paper_highlights/pdf/figures"
):
    paper_metadata = scipdf.parse_pdf_to_dict(file_path)

    if extract_figures:
        # folder should contain only PDF files
        scipdf.parse_figures(file_path, output_folder=f"{os.getcwd()}{figures_directory}")
        # TODO: clean up extracted images after storing them in object storage
    return paper_metadata
