import os

import dotenv

# Load environment variables from .env file
_TESTING = os.getenv("CHATGPT_MEMORY_TESTING", False)
if _TESTING:
    # for testing we use the .env.example file instead
    dotenv.load_dotenv(dotenv.find_dotenv(".env.example"))
else:
    dotenv.load_dotenv()

# Any remote API (OpenAI, Cohere etc.)
OPENAI_TIMEOUT = float(os.getenv("REMOTE_API_TIMEOUT_SEC", 30))
OPENAI_BACKOFF = float(os.getenv("REMOTE_API_BACKOFF_SEC", 10))
OPENAI_MAX_RETRIES = int(os.getenv("REMOTE_API_MAX_RETRIES", 5))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Cloud data store (Redis, Pinecone etc.)
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# HF Token
HF_TOKEN = os.getenv("HF_TOKEN")
assert (
    os.getenv("HF_REPO", None) is not None
), """
Environment variable `HF_REPO` should be set prior to running acad-gpt.
You'd need to create a new model on the huggingface hub using the url:
`https://huggingface.co/new`

then set `HF_REPO` variables value to: HF_REPO={hf_username}/{hf_model_name}
"""
HF_REPO = os.getenv("HF_REPO")
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://huggingface.co")

# API Config
DEFAULT_PATH = str(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples/paper_highlights/pdf")))
FILE_UPLOAD_PATH = os.getenv("FILE_UPLOAD_PATH", DEFAULT_PATH)
