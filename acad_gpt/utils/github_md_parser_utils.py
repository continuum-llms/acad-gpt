import base64
import logging
from time import sleep
from typing import Dict, List

import requests

from acad_gpt.constants import GITHUB_API_URL, GITHUB_REPO_META_FIELDS, SLEEP_TIME_ON_RATE_LIMIT

logger = logging.getLogger(__name__)


def fetch_github_stars_for_user(github_username: str) -> List[Dict]:
    # TODO: add reflection with exponential backoff
    page = 1
    repos = []

    while True:
        response = requests.get(f"{GITHUB_API_URL}/users/{github_username}/starred?page={page}")
        repos += response.json()
        page += 1

        if response.status_code != 200:
            logging.warn(f"Hit rate limit, sleeping {SLEEP_TIME_ON_RATE_LIMIT} seconds...")
            sleep(SLEEP_TIME_ON_RATE_LIMIT)
            continue
        print(response)
    return repos


def extract_relevant_fields(repos: List[Dict]) -> List[Dict]:
    processed_repos = []
    for repo in repos:
        processed_repo = {key: repo[key] for key in GITHUB_REPO_META_FIELDS if key in repo}
        processed_repos.append(processed_repo)
    print(len(processed_repos))
    return processed_repos


def fetch_github_readmes(repos: List[Dict]) -> List[Dict]:
    for idx, repo in enumerate(repos):
        if "full_name" not in repo:
            repos[idx]["readme"] = ""
            continue
        response = requests.get(f"{GITHUB_API_URL}/repos/{repo['full_name']}/contents/README.md")
        repos[idx]["readme"] = base64.b64decode(response.json().get("content", "")).decode("utf-8")
    print(len(repos))
    return repos
