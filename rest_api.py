import enum
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, List

import numpy as np
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from acad_gpt.datastore import RedisDataStore, RedisDataStoreConfig
from acad_gpt.environment import FILE_UPLOAD_PATH, OPENAI_API_KEY, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from acad_gpt.llm_client import EmbeddingClient, EmbeddingConfig
from acad_gpt.parsers import ParserConfig, PDFParser


class DocumentType(str, enum.Enum):
    Table = "Table"
    Figure = "Figure"
    Highlight = "Highlight"
    Section = "Section"


class SearchPayload(BaseModel):
    query: str
    k: int = 5
    document_type: DocumentType = DocumentType.Section


class Response(BaseModel):
    file_id: str
    message: str


app = FastAPI()

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
redis_datastore = RedisDataStore(config=redis_datastore_config, do_flush_data=True)


@app.post("/file-upload")
def upload_file(
    files: List[UploadFile] = File(...),
):
    response = []
    for file in files:
        try:
            file_name = f"{uuid.uuid4().hex}_{file.filename}"
            file_path = Path(FILE_UPLOAD_PATH) / file_name

            isExist = os.path.exists(FILE_UPLOAD_PATH)
            if not isExist:
                # create the metadata directory because it does not exist
                os.makedirs(FILE_UPLOAD_PATH)

            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                parser = PDFParser()
                parser_config = ParserConfig(file_path_or_url=str(file_path), file_type="PDF", extract_figures=True)
                results = parser.parse(config=parser_config)
                documents = parser.pdf_to_documents(
                    pdf_contents=results, embed_client=embed_client, file_name=file_name.replace(".pdf", "")
                )
                redis_datastore.index_documents(documents)
                response.append(
                    Response(
                        file_id=file_name,
                        message=f"File `{file_name}` has been indexed with {len(documents)} passages.",
                    )
                )
        finally:
            file.file.close()

    return response


@app.post("/search/")
async def search(search_payload: SearchPayload) -> List[Any]:
    query_vector = embed_client.embed_queries(queries=[search_payload.query])[0].astype(np.float32).tobytes()
    search_result = redis_datastore.search_documents(query_vector=query_vector, topk=search_payload.k)
    return search_result
