import abc
from typing import List


class DocStore(abc.ABC):
    @abc.abstractmethod
    def upload_from_filename(self, file_path: str, file_name: str) -> None:
        """
        Uploads a file to the docstore from a local file path.

        Args:
            file_path: The path to the file to upload.
            file_name: The name to give the file in the docstore.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def download_to_filename(self, file_name: str, file_path: str) -> None:
        """
        Downloads a file from the docstore to a local file path.

        Args:
            file_name: The name of the file in the docstore.
            file_path: The path to save the file to.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def upload_from_file(self, file, file_name: str) -> None:
        """
        Uploads a file to the docstore from a file object.

        Args:
            file: The file object to upload.
            file_name: The name to give the file in the docstore.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def download_to_file(self, file_name: str, file) -> None:
        """
        Downloads a file from the docstore to a byte array.

        Args:
            file_name: The name of the file in the docstore.
            file: The file object to save the file to.

        Returns:
            The bytes of the file.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, file_name: str) -> None:
        """
        Deletes a file from the docstore.

        Args:
            file_name: The name of the file in the docstore.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> List[str]:
        """
        Lists all files in the docstore.

        Returns:
            A list of file names.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self, file_name: str) -> bool:
        """
        Checks if a file exists in the docstore.

        Args:
            file_name: The name of the file in the docstore.

        Returns:
            True if the file exists, False otherwise.
        """
        raise NotImplementedError
