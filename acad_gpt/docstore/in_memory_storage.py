from typing import List, Optional

from pydantic import BaseModel

from acad_gpt.docstore.base import DocStore


class InMemoryStorageConfig(BaseModel):
    mutable: bool = True
    """ Whether the storage is mutable. If mutable, the storage can be modified. If not, the storage is read-only. """
    max_size: Optional[int] = None
    """ The maximum size of the storage. If None, the storage has no maximum size. """


class InMemoryStorage(DocStore):
    """
    A docstore that uses an in-memory dictionary as the backend.

    Note:
        Primarily intended for testing purposes.

    Args:
        config (InMemoryStorageConfig): The configuration to use.
        storage (Optional[dict]): The storage to use. If None, an empty storage is initialized.
    """

    def __init__(self, config: InMemoryStorageConfig, storage: Optional[dict] = None):
        self.config = config
        self.mutable = config.mutable
        self.max_size = config.max_size
        if storage is None:
            storage = dict()
        self.storage = storage
        """ The in-memory storage. """

    def upload_from_filename(self, file_path: str, file_name: str) -> None:
        if not self.mutable:
            raise ValueError("The storage is not mutable.")
        if self.max_size is not None and len(self.storage) >= self.max_size:
            raise ValueError("The storage is full.")
        with open(file_path, "rb") as f:
            self.storage[file_name] = f.read()

    def download_to_filename(self, file_name: str, file_path: str) -> None:
        with open(file_path, "wb") as f:
            f.write(self.storage[file_name])

    def upload_from_file(self, file, file_name: str) -> None:
        if not self.mutable:
            raise ValueError("The storage is not mutable.")
        if self.max_size is not None and len(self.storage) >= self.max_size:
            raise ValueError("The storage is full.")
        self.storage[file_name] = file.read()

    def download_to_file(self, file_name: str, file) -> None:
        file.write(self.storage[file_name])

    def exists(self, file_name: str) -> bool:
        return file_name in self.storage

    def delete(self, file_name: str) -> None:
        if not self.mutable:
            raise ValueError("The storage is not mutable.")
        del self.storage[file_name]

    def list(self) -> List[str]:
        return list(self.storage.keys())
