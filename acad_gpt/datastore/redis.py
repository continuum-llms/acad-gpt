import hashlib
import logging
from typing import Any, Dict, List

import redis
from redis.commands.search.field import TagField, TextField, VectorField
from redis.commands.search.query import Query

from acad_gpt.datastore.config import RedisDataStoreConfig
from acad_gpt.datastore.datastore import DataStore

logger = logging.getLogger(__name__)


class RedisDataStore(DataStore):
    def __init__(self, config: RedisDataStoreConfig, do_flush_data: bool = False, **kwargs):
        super().__init__(config=config)
        self.config = config
        self.do_flush_data = do_flush_data

        self.connect()
        self.create_index()

    def connect(self):
        """
        Connect to the Redis server.
        """
        connection_pool = redis.ConnectionPool(
            host=self.config.host, port=self.config.port, password=self.config.password
        )
        self.redis_connection = redis.Redis(connection_pool=connection_pool)

        # flush data only once after establishing connection
        if self.do_flush_data:
            self.flush_all_documents()
            self.do_flush_data = False

    def flush_all_documents(self):
        """
        Removes all documents from the redis index.
        """
        self.redis_connection.flushall()

    def create_index(self):
        """
        Creates a Redis index with a dense vector field.
        """
        try:
            self.redis_connection.ft().create_index(
                [
                    VectorField(
                        self.config.vector_field_name,
                        self.config.index_type,
                        {
                            "TYPE": "FLOAT32",
                            "DIM": self.config.vector_dimensions,
                            "DISTANCE_METRIC": self.config.distance_metric,
                            "INITIAL_CAP": self.config.number_of_vectors,
                            "M": self.config.M,
                            "EF_CONSTRUCTION": self.config.EF,
                        },
                    ),
                    TextField("text"),  # contains the original message
                    TextField("title"),
                    TagField("type"),
                    TagField("status"),
                    TextField("url"),
                ]
            )
            logger.info("Created a new Redis index for storing chat history")
        except redis.exceptions.ResponseError as redis_error:
            logger.info(f"Working with existing Redis index.\nDetails: {redis_error}")

    def index_documents(self, documents: List[Dict]):
        """
        Indexes the set of documents.

        Args:
            documents (List[Dict]): List of documents to be indexed.
        """
        redis_pipeline = self.redis_connection.pipeline(transaction=False)
        for document in documents:
            assert "text" in document and "url" in document, "Document must include the fields `text`, and `url`"
            sha = hashlib.sha256()
            sha.update(document.get("url").encode())
            redis_pipeline.hset(sha.hexdigest(), mapping=document)
        redis_pipeline.execute()

    def search_documents(self, query: bytes, topk: int = 5, **kwargs) -> List[Any]:
        """
        Searches the redis index using the query vector.

        Args:
            query_vector (np.ndarray): Embedded query vector.
            topk (int, optional): Number of results. Defaults to 5.

        Returns:
            List[Any]: Search result documents.
        """
        status = kwargs.get("status", None)
        type = kwargs.get("type", None)
        tag = "("
        if status:
            tag += f"@status:{{{status}}}"
        if type:
            tag += f"@type:{{{type}}}"
        tag += ")"
        # if no tags are selected
        if len(tag) < 3:
            tag = "*"
        query_obj = (
            Query(
                f"""{tag}=>[KNN {topk} \
                    @{self.config.vector_field_name} $vec_param AS vector_score]"""
            )
            .sort_by("vector_score")
            .paging(0, topk)
            .return_fields(
                "vector_score",
                "text",
                "title",
                "type",
                "status",
                "url",
            )
            .dialect(2)
        )
        params_dict = {"vec_param": query}
        try:
            result_documents = self.redis_connection.ft().search(query_obj, query_params=params_dict).docs
        except redis.exceptions.ResponseError as redis_error:
            logger.info(f"Details: {redis_error}")
        return result_documents

    def get_all_document_ids(self) -> List[str]:
        """
        Returns document titles of all documents.

        Returns:
            List[str]: List of document titles stored in redis.
        """
        query = Query("*").return_fields("title")
        result_documents = self.redis_connection.ft().search(query).docs

        document_ids: List[str] = []
        document_ids = list(set([getattr(result_document, "document_id") for result_document in result_documents]))

        return document_ids

    def delete_documents(self, document_id: str):
        """
        Deletes all documents for a given conversation id.

        Args:
            document_id (str): Id of the conversation to be deleted.
        """
        query = (
            Query(f"""(@document_id:{{{document_id}}})""")
            .return_fields(
                "id",
            )
            .dialect(2)
        )
        for document in self.redis_connection.ft().search(query).docs:
            document_id = getattr(document, "id")
            deletion_status = self.redis_connection.ft().delete_document(document_id, delete_actual_document=True)

            assert deletion_status, f"Deletion of the document with id {document_id} failed!"
