from typing import Dict, List

from acad_gpt.parsers.base_parser import BaseParser
from acad_gpt.parsers.config import GitHubMDParserConfig
from acad_gpt.utils.github_md_parser_utils import (
    extract_relevant_fields,
    fetch_github_readmes,
    fetch_github_stars_for_user,
)


class GitHubMDParser(BaseParser):
    def parse(self, config: GitHubMDParserConfig):
        user_starred_repos = self._get_user_stars(config.github_username)
        self._get_readmes(user_starred_repos)

    def _get_user_stars(self, github_username: str) -> List[Dict]:
        user_starred_repos = fetch_github_stars_for_user(github_username=github_username)
        user_starred_processed_repos = extract_relevant_fields(repos=user_starred_repos)
        return user_starred_processed_repos

    def _get_readmes(self, repos: List[Dict]) -> List[Dict]:
        fetch_github_readmes(repos=repos)
        return [{}]


if __name__ == "__main__":
    GitHubMDParser().parse(config=GitHubMDParserConfig(github_username="shahrukhx01"))
