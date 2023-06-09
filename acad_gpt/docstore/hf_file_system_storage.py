"""
Based on HuggingFace's File System API.

See https://huggingface.co/docs/huggingface_hub/v0.14.1/en/package_reference/hf_file_system#huggingface_hub.HfFileSystem
"""
import logging
import os
from typing import List, Optional

from huggingface_hub import HfFileSystem, login
from pydantic import BaseSettings, Field

from acad_gpt.docstore.base import DocStore

logger = logging.getLogger(__name__)


class HfFSDocStoreConfig(BaseSettings):
    repo: str = Field(..., env="HF_FS_REPO")
    """ The repository to use as a file system docstore. """
    endpoint: Optional[str] = Field(None, env="HF_ENDPOINT")
    """ The endpoint to use. If None, the default endpoint is used. """
    token: Optional[str] = Field(None, env="HF_TOKEN")
    """ The token to use. If None, the default stored token is used. """


class HfFSDocStore(DocStore):
    """
    A docstore that uses the HuggingFace File System API as the backend.

    Args:
        config (HfFSDocStoreConfig): The configuration to use.
    """

    def __init__(self, config: HfFSDocStoreConfig):
        self.config = config
        """ The config to use."""
        # fail early incase no token is set
        try:
            login(self.config.token)
        except ValueError as hf_value_error:
            logger.error(hf_value_error)

        self._hf_fs = HfFileSystem(**self.config.dict())

    @property
    def fs(self) -> HfFileSystem:
        return self._hf_fs

    def path_in_repo(self, file_name: str) -> str:
        return os.path.join(self.config.repo, file_name)

    def upload_from_filename(self, file_path: str, file_name: str) -> None:
        self.fs.put(lpath=file_path, rpath=self.path_in_repo(file_name))

    def download_to_filename(self, file_name: str, file_path: str) -> None:
        self.fs.get(rpath=self.path_in_repo(file_name), lpath=file_path)

    def upload_from_file(self, file, file_name: str) -> None:
        with self.fs.open(self.path_in_repo(file_name), "wb") as f:
            f.write(file.read())

    def download_to_file(self, file_name: str, file) -> None:
        with self.fs.open(self.path_in_repo(file_name), "rb") as f:
            file.write(f.read())

    def delete(self, file_name: str) -> None:
        self.fs.delete(self.path_in_repo(file_name))

    def list(self) -> List[str]:
        # 1. get files
        files = self.fs.ls(self.config.repo, detail=False)

        # 2. remove repo prefix for consistency with other API
        files = [file_name[len(self.config.repo) + 1 :] for file_name in files]

        return files

    def exists(self, file_name: str) -> bool:
        return self.fs.exists(self.path_in_repo(file_name))
