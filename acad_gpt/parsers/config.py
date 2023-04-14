from typing import Optional

from pydantic import BaseModel


class PDFParserConfig(BaseModel):
    file_path_or_url: str
    file_title: Optional[str]


class GitHubMDParserConfig(BaseModel):
    github_username: str
