"""
add deps
TODO: pip install discord requests validators bs4 elasticsearch==7.0.0

# TODO:
- add timestamps for:
    1. when bookmark webpage itself was actually created (optional)
    2. when bookmark was last updated
- annotated file `upload` command

Collaboration:
- add clear roadmap for how to add new commands based on other modalities
- target for mid may to release to public
"""


from typing import List, Optional

import discord
import validators
from discord import app_commands

from acad_bot_utils import get_url_type, process_url
from acad_gpt.datastore import ElasticSearchDataStore, ElasticSearchStoreConfig, RedisDataStore, RedisDataStoreConfig
from acad_gpt.environment import (
    DISCORD_BOOKMARK_BOT_GUILD_ID,
    DISCORD_BOOKMARK_BOT_TOKEN,
    ES_INDEX,
    ES_PASSWORD,
    ES_PORT,
    ES_URL,
    ES_USERNAME,
    OPENAI_API_KEY,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
)
from acad_gpt.llm_client import EmbeddingClient, EmbeddingConfig
from acad_gpt.llm_client.openai.conversation.chatgpt_client import ChatGPTClient
from acad_gpt.llm_client.openai.conversation.config import ChatGPTConfig
from acad_gpt.memory.manager import MemoryManager

# Instantiate an EmbeddingClient object with the EmbeddingConfig object
embedding_config = EmbeddingConfig(api_key=OPENAI_API_KEY)
embed_client = EmbeddingClient(config=embedding_config)

# Instantiate a RedisDataStore object with the RedisDataStoreConfig object
redis_datastore_config = RedisDataStoreConfig(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
)
redis_datastore = RedisDataStore(config=redis_datastore_config, do_flush_data=True)

# Instantiate an ElasticSearchDataStore object with the ElasticSearchStoreConfig object
es_datastore_config = ElasticSearchStoreConfig(
    host=ES_URL,
    port=ES_PORT,
    username=ES_USERNAME,
    password=ES_PASSWORD,
    index_name=ES_INDEX,
)
es_datastore = ElasticSearchDataStore(config=es_datastore_config)

# Instantiate a MemoryManager object with the RedisDataStore object and EmbeddingClient object
memory_manager = MemoryManager(datastore=redis_datastore, embed_client=embed_client, topk=1)
chat_gpt_config = ChatGPTConfig(api_key=OPENAI_API_KEY, verbose=False)
chat_gpt_client = ChatGPTClient(config=chat_gpt_config, memory_manager=memory_manager)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=DISCORD_BOOKMARK_BOT_GUILD_ID))
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    print("{0.author}: {0.content}".format(message))

    if validators.url(message.content):
        type, url = get_url_type(message.content)
        document = process_url(url, type, embed_client)
        redis_datastore.index_documents(documents=[document])
        es_datastore.index_documents(documents=[document])
        await message.channel.send(f"`{type}` Bookmark saved!")

    else:
        await message.channel.send("Something went wrong!")


@tree.command(
    name="search", description="To search indexed content", guild=discord.Object(id=DISCORD_BOOKMARK_BOT_GUILD_ID)
)
async def search(
    interaction, query: str, status: Optional[str] = None, topk: Optional[int] = 5, ask_gpt: Optional[bool] = False
):
    if ask_gpt:
        await interaction.response.defer()
        chat_result = (
            f"`{client.user}`: {query}\n`ChatGPT`: {chat_gpt_client.converse(query, topk=topk).chat_gpt_answer}"
        )
        await interaction.followup.send(chat_result)
    else:
        topk_hits = es_datastore.search_documents(query, status=status, topk=topk)
        if len(topk_hits) > 0:
            response = f"Here are the top {len(topk_hits)} results for your query: `{query}`\n"
            response += "\n".join([f"{idx+1}. {hit['title']}\n<{hit['url']}>" for idx, hit in enumerate(topk_hits)])
            await interaction.response.send_message(response)
        else:
            await interaction.response.send_message(f"Sorry, no results found for your query: {query}")


@tree.command(
    name="update", description="To update indexed content", guild=discord.Object(id=DISCORD_BOOKMARK_BOT_GUILD_ID)
)
async def update(interaction, url: str, status: str):
    if validators.url(url):
        type, url = get_url_type(url)
        document = process_url(url, type, embed_client, status=status)
        redis_datastore.index_documents(documents=[document])
        document.pop("embedding")
        es_datastore.index_documents(documents=[document])
        await interaction.response.send_message(f"Bookmark for <{url}> is set to {status} status!")
    else:
        await interaction.response.send_message("Something went wrong!")


@update.autocomplete("status")
@search.autocomplete("status")
async def status_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    statuses = ["todo", "done"]
    return [app_commands.Choice(name=status, value=status) for status in statuses if current.lower() in status.lower()]


client.run(DISCORD_BOOKMARK_BOT_TOKEN)
