import pytest

from acad_gpt.docstore.base import DocStore
from acad_gpt.docstore.in_memory_storage import InMemoryStorage, InMemoryStorageConfig


class TestDocStore:
    @pytest.fixture
    def storage(self) -> DocStore:
        config = InMemoryStorageConfig()
        return InMemoryStorage(config)

    def test_upload_from_filename_and_exists(self, tmp_path, storage: DocStore):
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        assert not storage.exists("test.txt")

        storage.upload_from_filename(str(file_path), "test.txt")

        assert storage.exists("test.txt")

    def test_upload_from_file_and_exists(self, tmp_path, storage: DocStore):
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        assert not storage.exists("test.txt")

        with open(str(file_path), "rb") as f:
            storage.upload_from_file(f, "test.txt")

        assert storage.exists("test.txt")

    def test_download_to_filename(self, tmp_path, storage: DocStore):
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        storage.upload_from_filename(str(file_path), "test.txt")
        other_file_path = tmp_path / "other_test.txt"
        assert not other_file_path.exists(), "other_test.txt should not exist"
        storage.download_to_filename("test.txt", str(other_file_path))

        assert other_file_path.read_text() == "test"

    def test_download_to_file(self, tmp_path, storage: DocStore):
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        storage.upload_from_filename(str(file_path), "test.txt")
        other_file_path = tmp_path / "other_test.txt"
        assert not other_file_path.exists(), "other_test.txt should not exist"
        with open(str(other_file_path), "wb") as f:
            storage.download_to_file("test.txt", f)

        assert other_file_path.read_text() == "test"

    def test_list(self, tmp_path, storage: DocStore):
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        storage.upload_from_filename(str(file_path), "test.txt")
        storage.upload_from_filename(str(file_path), "test2.txt")
        assert storage.list() == ["test.txt", "test2.txt"]

    def test_delete(self, tmp_path, storage: DocStore):
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        storage.upload_from_filename(str(file_path), "test.txt")
        assert storage.exists("test.txt")
        storage.delete("test.txt")
        assert not storage.exists("test.txt")
