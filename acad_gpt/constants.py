# LLM Config related
"""
if OpenAI embedding model type is "*-001" the set max sequence length to `2046`,
otherwise for type "*-002" set `8191`
"""
MAX_ALLOWED_SEQ_LEN_001 = 2046
MAX_ALLOWED_SEQ_LEN_002 = 8191

# Github related
GITHUB_API_URL = "https://api.github.com"
GITHUB_REPO_META_FIELDS = [
    "name",
    "full_name",
    "avatar_url",
    "html_url",
    "stars",
    "license",
    "topics",
    "language",
    "forks",
    "watchers",
    "created_at",
    "updated_at",
]
SLEEP_TIME_ON_RATE_LIMIT = 60
