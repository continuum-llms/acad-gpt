# AcadGPT

<<<<<<< HEAD
A service for distilling papers, github repos, youtube tutorials and much more using the power of LLMs.
=======
Allows to scale the ChatGPT API to multiple simultaneous sessions with infinite contextual and adaptive memory powered by GPT and Redis datastore.

## Getting Started

1. Create your free `Redis` datastore [here](https://redis.com/try-free/).
2. Get your `OpenAI` API key [here](https://platform.openai.com/overview).
3. Run the GROBID using the given bash script before parsing PDF

```bash
bash serve_grobid.sh
```

### Usage

Set the required environment variables before running the script. This is optional but recommended.
You can use a `.env` file for this. See the `.env.example` file for an example.

```python
from chatgpt_memory.environment import OPENAI_API_KEY, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
```

Create an instance of the `RedisDataStore` class with the `RedisDataStoreConfig` configuration.

```python
from chatgpt_memory.datastore import RedisDataStoreConfig, RedisDataStore

redis_datastore_config = RedisDataStoreConfig(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
)
redis_datastore = RedisDataStore(config=redis_datastore_config)
```

Create an instance of the `EmbeddingClient` class with the `EmbeddingConfig` configuration.

```python
from chatgpt_memory.llm_client import EmbeddingConfig, EmbeddingClient

embedding_config = EmbeddingConfig(api_key=OPENAI_API_KEY)
embed_client = EmbeddingClient(config=embedding_config)
```

Create an instance of the `MemoryManager` class with the Redis datastore and Embedding client instances, and the `topk` value.

```python
from chatgpt_memory.memory.manager import MemoryManager

memory_manager = MemoryManager(datastore=redis_datastore, embed_client=embed_client, topk=1)
```

Create an instance of the `ChatGPTClient` class with the `ChatGPTConfig` configuration and the `MemoryManager` instance.

```python
from chatgpt_memory.llm_client import ChatGPTClient, ChatGPTConfig

chat_gpt_client = ChatGPTClient(
    config=ChatGPTConfig(api_key=OPENAI_API_KEY, verbose=True), memory_manager=memory_manager
)
```

Start the conversation by providing user messages to the converse method of the `ChatGPTClient` instance.

```python
conversation_id = None
while True:
    user_message = input("\n Please enter your message: ")
    response = chat_gpt_client.converse(message=user_message, conversation_id=conversation_id)
    conversation_id = response.conversation_id
    print(response.chat_gpt_answer)
```

This will allow you to talk to the AI assistant and extend its memory by using an external Redis datastore.

TODOS:

- [ ] Add first version of REST API
- [ ] Refactor entire code base to make it more maintainable
- [ ] Add contribution guide
- [ ] Add readthedocs page post-refactor
- [ ] Add CI/CD pipeline
- [ ] Add Pypi package
- [ ] Add docker image file and free built image on dockerhub
- [ ] Integrate with paperswithcode and connected papers' APIs
- [ ] Add latex based dense vector search
- [ ] Add voice to conversation interface
>>>>>>> ab5e874 (feat: add repo todos)
