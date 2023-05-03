import hashlib
import logging
from typing import Any, Dict, List

from elasticsearch import Elasticsearch, RequestsHttpConnection

from acad_gpt.datastore.config import ElasticSearchStoreConfig
from acad_gpt.datastore.datastore import DataStore

logger = logging.getLogger(__name__)


class ElasticSearchDataStore(DataStore):
    def __init__(self, config: ElasticSearchStoreConfig, **kwargs):
        super().__init__(config=config)
        self.config = config

        self.connect()
        self.create_index()

    def connect(self):
        """
        Connect to the ES server.
        """
        self.es_connection = Elasticsearch(
            self.config.host,
            port=self.config.port,
            connection_class=RequestsHttpConnection,
            http_auth=(self.config.username, self.config.password),
            use_ssl=True,
            verify_certs=False,
        )

    def create_index(self):
        """
        Creates a ES index.
        """
        try:
            ES_INDEX_MAPPING = {
                "properties": {
                    "title": {"type": "text"},
                    "text": {"type": "text"},
                    "url": {"type": "text"},
                    "status": {"type": "keyword"},
                    "type": {"type": "keyword"},
                }
            }
            if not self.es_connection.indices.exists(self.config.index_name):
                self.es_client.indices.create(index=self.config.index_name, body={"mappings": ES_INDEX_MAPPING})
            logger.info("Created a new ES index")
        except Exception as es_error:
            logger.info(f"Working with existing ES index.\nDetails: {es_error}")

    def index_documents(self, documents: List[Dict]):
        """
        Indexes the set of documents.

        Args:
            documents (List[Dict]): List of documents to be indexed.
        """
        for document in documents:
            try:
                assert "text" in document and "url" in document, "Document must include the fields `text` and `url`"
                sha = hashlib.sha256()
                sha.update(document.get("url").encode())

                self.es_connection.update(
                    index=self.config.index_name, id=sha.hexdigest(), body={"doc": document, "doc_as_upsert": True}
                )
            except Exception as es_error:
                logger.info(f"Error in indexing document.\nDetails: {es_error}")

    def search_documents(self, query: str, topk: int = 5, **kwargs) -> List[Any]:
        """
        Searches the redis index using the query vector.

        Args:
            query_vector (np.ndarray): Embedded query vector.
            topk (int, optional): Number of results. Defaults to 5.

        Returns:
            List[Any]: Search result documents.
        """
        filter = [{"match": {"text": query}}]
        status = kwargs.get("status")
        if status:
            filter.append({"match": {"status": status}})
        es_query = {
            "query": {"bool": {"must": filter}},
            "size": topk,
        }
        topk_hits = []
        es_response = self.es_connection.search(index=self.config.index_name, body=es_query)
        for inter_res in es_response["hits"]["hits"]:
            topk_hits.append(inter_res["_source"])
        return topk_hits

    def delete_document(self, url: str):
        """
        Deletes all documents for a given conversation id.

        Args:
            document_id (str): Id of the conversation to be deleted.
        """
        sha = hashlib.sha256()
        sha.update(url.encode())
        try:
            self.es_connection.delete(index=self.es_connection, id=sha.hexdigest())
        except Exception as es_error:
            logger.info(f"Error in deleting document.\nDetails: {es_error}")
