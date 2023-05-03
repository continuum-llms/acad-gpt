from enum import Enum

from pydantic import BaseModel


class RedisIndexType(str, Enum):
    hnsw = "HNSW"
    flat = "FLAT"


class DataStoreConfig(BaseModel):
    host: str
    port: int
    password: str


class RedisDataStoreConfig(DataStoreConfig):
    index_type: str = RedisIndexType.hnsw
    vector_field_name: str = "embedding"
    vector_dimensions: int = 1024
    distance_metric: str = "L2"
    number_of_vectors: int = 686
    M: int = 40
    EF: int = 200


class ElasticSearchStoreConfig(DataStoreConfig):
    username: str
    index_name: str
