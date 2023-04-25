import numpy as np

from acad_gpt.datastore import RedisDataStore, RedisDataStoreConfig

## set the following ENVIRONMENT Variables before running this script
# Import necessary modules
from acad_gpt.environment import OPENAI_API_KEY, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from acad_gpt.llm_client import EmbeddingClient, EmbeddingConfig
from acad_gpt.parsers import ParserConfig, PDFParser

if __name__ == "__main__":
    # Instantiate an EmbeddingConfig object with the OpenAI API key
    embedding_config = EmbeddingConfig(api_key=OPENAI_API_KEY)

    # Instantiate an EmbeddingClient object with the EmbeddingConfig object
    embed_client = EmbeddingClient(config=embedding_config)

    # Instantiate a RedisDataStoreConfig object with the Redis connection details
    redis_datastore_config = RedisDataStoreConfig(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
    )

    # Instantiate a RedisDataStore object with the RedisDataStoreConfig object
    redis_datastore = RedisDataStore(config=redis_datastore_config)

    parser = PDFParser()
    parser_config = ParserConfig(
        file_path_or_url="examples/paper_highlights/pdf/paper.pdf", file_type="PDF", extract_figures=True
    )
    results = parser.parse(config=parser_config)
    documents = parser.pdf_to_documents(pdf_contents=results, embed_client=embed_client, file_name="paper.pdf")
    redis_datastore.index_documents(documents)

    while True:
        query = input("Enter your query: ")
        query_vector = embed_client.embed_queries(queries=[query])[0].astype(np.float32).tobytes()
        print(redis_datastore.search_documents(query_vector=query_vector))
