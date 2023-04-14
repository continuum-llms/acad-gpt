from acad_gpt.datastore import RedisDataStore, RedisDataStoreConfig

## set the following ENVIRONMENT Variables before running this script
# Import necessary modules
from acad_gpt.environment import OPENAI_API_KEY, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from acad_gpt.llm_client import ChatGPTClient, ChatGPTConfig, EmbeddingClient, EmbeddingConfig
from acad_gpt.memory import MemoryManager
from acad_gpt.parsers import PDFParser, PDFParserConfig

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

    # Instantiate a MemoryManager object with the RedisDataStore object and EmbeddingClient object
    memory_manager = MemoryManager(datastore=redis_datastore, embed_client=embed_client, topk=1)

    # Instantiate a ChatGPTConfig object with the OpenAI API key and verbose set to True
    chat_gpt_config = ChatGPTConfig(api_key=OPENAI_API_KEY, verbose=False)

    # Instantiate a ChatGPTClient object with the ChatGPTConfig object and MemoryManager object
    chat_gpt_client = ChatGPTClient(config=chat_gpt_config, memory_manager=memory_manager)

    parser = PDFParser()
    parser_config = PDFParserConfig(file_path_or_url="examples/paper_highlights/whisper.pdf")

    prompt = f"""
    Please convert the following context to bullet points,
    only use the information given in the following paragraphs
    {parser.parse(config=parser_config)[0]}
    """

    # Use the ChatGPTClient object to generate a response
    response = chat_gpt_client.converse(message=prompt, conversation_id=None)
    print("\n\n\n \033[92m Summary of the highlighted content in the Whisper Paper by OpenAI: \n\n\n")
    print("\033[96m" + response.chat_gpt_answer)
