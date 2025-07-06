import aiohttp
import os

from .base import CodeSearcher, CodeResult

__all__ = ["GitHubSearch"]


class GitHubSearch(CodeSearcher):
    def __init__(self):
        super().__init__()
        self.token = self.get_github_token()
        assert self.token, "GitHub token is required for GitHub API access"

    @classmethod
    def get_github_token(cls) -> str:
        # TODO: more approaches to determine token
        if os.environ.get("GITHUB_TOKEN"):
            return os.environ["GITHUB_TOKEN"]

    @classmethod
    def is_acceptable(cls, codebase_url: str) -> bool:
        if not codebase_url or len(codebase_url) == 0:
            return False
        # TODO: need a more fine-grained check, e.g., owner/repo format
        return "github.com" in codebase_url

    @classmethod
    def extract_codebase(cls, codebase_url: str) -> str:
        ss = codebase_url.strip("/").split("/")
        owner, repo = ss[-2], ss[-1]
        return f"{owner}/{repo}"

    async def search(
        self,
        codebase: str,
        pattern: str,
        languages: list[str] | None = None,
    ) -> list[CodeResult]:
        """
        Search code in a GitHub repository.
        Args:
            codebase (str): The GitHub repository in the format "owner/repo".
            pattern (str): The search pattern to look for in the code.
            languages (list[str], optional): List of programming languages to filter results.

        The rate limit is 10 requests per minute for authenticated users.
        See more at:
        https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-code
        """

        query = f"q={pattern}+in:file+repo:{codebase}"
        if languages:
            for lang in languages:
                query += f"+language:{lang}"

        url = f"https://api.github.com/search/code?{query}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(
                        f"GitHub API error: {response.status}, {response.reason}"
                    )
                data = await response.json()
                return [
                    CodeResult(
                        file=item["name"],
                        path=item["path"],
                        http_url=item["html_url"],
                    )
                    for item in data.get("items", [])
                ]
