import aiohttp
import os
import dataclasses

from .base import CodeSearcher

__all__ = ["GitHubSearch", "CodeResult"]


@dataclasses.dataclass(frozen=True)
class CodeResult:
    file: str
    path: str
    http_url: str


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

    async def search(
        self,
        codebase: str,
        pattern: str,
        languages: list[str] | None = None,
    ) -> list[dict]:
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
