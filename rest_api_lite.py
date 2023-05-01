"""
add deps
TODO: pip install discord requests validators bs4 elasticsearch==7.0.0

# TODO:
add timestamps for:
1. when bookmark webpage itself was actually created (optional)
2. when bookmark was last updated
"""


import hashlib
import os
from typing import List, Optional

import discord
import requests
import validators
from bs4 import BeautifulSoup
from bs4.element import Comment
from discord import app_commands
from elasticsearch import Elasticsearch, RequestsHttpConnection

# configure discord bot
DISCORD_BOOKMARK_BOT_TOKEN = os.environ["DISCORD_BOOKMARK_TOKEN"]
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Subscribe to the 'guilds' and 'members' intents
GUILD_ID = 1102572400761114704
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# configure elastic search
DISCORD_BOOKMARK_ES_URL = os.environ["DISCORD_BOOKMARK_ES_URL"]
DISCORD_BOOKMARK_ES_USERNAME = os.environ["DISCORD_BOOKMARK_ES_USERNAME"]
DISCORD_BOOKMARK_ES_PASSWORD = os.environ["DISCORD_BOOKMARK_ES_PASSWORD"]
DISCORD_BOOKMARK_ES_INDEX = "discord-bookmark"


es = Elasticsearch(
    DISCORD_BOOKMARK_ES_URL,
    port=443,
    connection_class=RequestsHttpConnection,
    http_auth=(DISCORD_BOOKMARK_ES_USERNAME, DISCORD_BOOKMARK_ES_PASSWORD),
    use_ssl=True,
    verify_certs=False,
)
DISCORD_BOOKMARK_ES_INDEX_MAPPING = {
    "properties": {
        "title": {"type": "text"},
        "text": {"type": "text"},
        "url": {"type": "text"},
        "status": {"type": "keyword"},
    }
}

if not es.indices.exists(DISCORD_BOOKMARK_ES_INDEX):
    es.indices.create(index=DISCORD_BOOKMARK_ES_INDEX, body={"mappings": DISCORD_BOOKMARK_ES_INDEX_MAPPING})


def retrieve_bookmarks(query, k=5, status=None):
    filter = [{"match": {"text": query}}]
    if status:
        filter.append({"match": {"status": status}})
    es_query = {
        "query": {"bool": {"must": filter}},
        "size": k,
    }
    topk_hits = []
    es_response = es.search(index=DISCORD_BOOKMARK_ES_INDEX, body=es_query)
    for inter_res in es_response["hits"]["hits"]:
        topk_hits.append(inter_res["_source"])
    return topk_hits


def index_bookmark(title, text, url, status="todo"):
    doc = {"title": title, "text": text, "url": url, "status": status}
    sha = hashlib.sha256()
    sha.update(url.encode())

    res = es.update(index=DISCORD_BOOKMARK_ES_INDEX, id=sha.hexdigest(), body={"doc": doc, "doc_as_upsert": True})
    return res["result"]


def get_title(url):
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, "html.parser")

    for title in soup.find_all("title"):
        if title.get_text():
            return title.get_text()
        else:
            return ""


def tag_visible(element):
    if element.parent.name in ["style", "script", "head", "title", "meta", "[document]"]:
        return False
    if isinstance(element, Comment):
        return False
    return True


def get_text(url):
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, "html.parser")
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return " ".join(t.strip() for t in visible_texts)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    print("{0.author}: {0.content}".format(message))

    if validators.url(message.content):
        title = get_title(message.content)
        text = get_text(message.content)
        index_bookmark(title, text, message.content)
        await message.channel.send("Bookmark saved!")

    elif "todo" in message.content.lower() and "todo" in message.content:
        title = get_title(message.content)
        text = get_text(message.content)
        index_bookmark(title, text, message.content)
        await message.channel.send("Bookmark saved!")
    else:
        await message.channel.send("Something went wrong!")


@tree.command(name="search", description="To search indexed content", guild=discord.Object(id=GUILD_ID))
async def search(interaction, query: str, status: Optional[str] = None):
    topk_hits = retrieve_bookmarks(query, status=status)
    if len(topk_hits) > 0:
        response = f"Here are the top {len(topk_hits)} results for your query: `{query}`\n"
        response += "\n".join([f"{idx+1}. {hit['title']}\n<{hit['url']}>" for idx, hit in enumerate(topk_hits)])
        await interaction.response.send_message(response)
    else:
        await interaction.response.send_message(f"Sorry, no results found for your query: {query}")


@tree.command(name="update", description="To update indexed content", guild=discord.Object(id=GUILD_ID))
async def update(interaction, url: str, status: str):
    title = get_title(url)
    text = get_text(url)
    index_bookmark(title, text, url, status=status)
    await interaction.response.send_message(f"Bookmark for <{url}> is set to {status} status!")


@update.autocomplete("status")
async def fruits_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    statuses = ["todo", "done"]
    return [app_commands.Choice(name=status, value=status) for status in statuses if current.lower() in status.lower()]


client.run(DISCORD_BOOKMARK_BOT_TOKEN)
