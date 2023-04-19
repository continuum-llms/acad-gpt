from typing import Dict, List, Optional

from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
from pydantic import BaseModel

from acad_gpt.docstore.base import DocStore


class GoogleCloudStorageConfig(BaseModel):
    bucket_name: str
    """ The name of the bucket to use. """
    credentials: Optional[service_account.Credentials] = None
    """ The credentials to use. If None, the default credentials are used."""
    project: Optional[str] = None
    """ The project to use. If None, the default project is used."""
    client_options: Optional[Dict] = None
    """ The client options to use. If None, the default client options are used. """
    location: Optional[str] = None
    """ The location to use. If None, the default location is used."""
    storage_class: Optional[str] = None
    """ The storage class to use. If None, the default storage class is used."""


class GoogleCloudStorage(DocStore):
    """
    A docstore that uses Google Cloud Storage as the backend.

    Args:
        config (GoogleCloudStorageConfig): The configuration to use.
    """

    def __init__(self, config: GoogleCloudStorageConfig):
        self.config = config
        self.bucket_name = config.bucket_name
        self.credentials = config.credentials
        self.project = config.project
        self.client_options = config.client_options
        self.location = config.location
        self.storage_class = config.storage_class

        self.client = storage.Client(
            credentials=self.credentials,
            project=self.project,
            client_options=self.client_options,
        )

        self.bucket = self.client.bucket(self.bucket_name)

    def upload_from_filename(self, file_path: str, file_name: str) -> None:
        blob = self.bucket.blob(file_name)
        blob.upload_from_filename(file_path)

    def download_to_filename(self, file_name: str, file_path: str) -> None:
        blob = self.bucket.blob(file_name)
        blob.download_to_filename(file_path)

    def upload_from_file(self, file, file_name: str) -> None:
        blob = self.bucket.blob(file_name)
        blob.upload_from_file(file)

    def download_to_file(self, file_name: str, file) -> None:
        blob = self.bucket.blob(file_name)
        blob.download_to_file(file)

    def delete(self, file_name: str) -> None:
        blob = self.bucket.blob(file_name)
        blob.delete()

    def list(self) -> List[str]:
        return [blob.name for blob in self.bucket.list_blobs()]

    def exists(self, file_name: str) -> bool:
        try:
            self.bucket.get_blob(file_name)
            return True
        except NotFound:
            return False
