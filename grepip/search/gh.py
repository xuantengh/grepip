import enum
import pathlib
import aiohttp
import aiofiles
import subprocess
import os

import aiohttp.client_exceptions

from grepip.utils import get_cache_dir, GREPIP_RETRY_TIMES
from .base import CodeSearcher


__all__ = ["GitHubSearch"]


class ArtifactType(enum.Enum):
    RELEASE = enum.auto()
    TAG = enum.auto()


class GitHubSearch(CodeSearcher):
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

    async def fetch_release(self, codebase_url: str) -> bool:
        """
        Fetch the latest release from the GitHub repository.
        """
        owner_repo = self.extract_codebase(codebase_url)
        release_endpoint = f"https://api.github.com/repos/{owner_repo}/releases"
        tag_endpoint = f"https://api.github.com/repos/{owner_repo}/tags"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + self.get_github_token(),
            "X-GitHub-Api-Version": "2022-11-28",
        }
        release_save_path = (
            get_cache_dir()
            / "github"
            / f"{owner_repo.replace('/', '.')}.release.tar.gz"
        )
        tag_save_path = (
            get_cache_dir() / "github" / f"{owner_repo.replace('/', '.')}.tag.tar.gz"
        )
        for p in (release_save_path, tag_save_path):
            if not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
            if p.exists() and p.stat().st_size > 0:
                self.artifact_path = p
                return

        async def download_tarball(
            session: aiohttp.ClientSession,
            endpoint: str,
            save_path: pathlib.Path,
            artifact_type: ArtifactType = ArtifactType.RELEASE,
        ) -> None:
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    artifacts = await response.json()
                    if len(artifacts) == 0:
                        return
                    latest_artifact: dict = artifacts[0]
                    tarball_url = latest_artifact.get("tarball_url", None)

                    for _ in range(GREPIP_RETRY_TIMES):
                        try:
                            async with session.get(tarball_url) as response:
                                if response.status != 200:
                                    continue
                                async with aiofiles.open(save_path, "wb") as f:
                                    await f.write(await response.read())

                        except aiohttp.client_exceptions.ClientError:
                            # TODO: log warning here
                            if save_path.exists():
                                os.remove(save_path)
                            continue

                        if save_path.exists() and save_path.stat().st_size > 0:
                            break
                        else:
                            os.remove(save_path)

                    if save_path.exists() and save_path.stat().st_size > 0:
                        self.artifact_path = save_path

        async with aiohttp.ClientSession() as session:
            await download_tarball(
                session, release_endpoint, release_save_path, ArtifactType.RELEASE
            )
            if self.artifact_path is None:
                await download_tarball(
                    session, tag_endpoint, tag_save_path, ArtifactType.TAG
                )
        return self.artifact_path is not None

    def zgrep(self, pattern: str) -> list[str]:
        cmd = ["zgrep", "-H", "-w", "-a", "-n", pattern, str(self.artifact_path)]
        cmd = " ".join(cmd)
        try:
            p = subprocess.run(
                cmd,
                text=True,
                check=True,
                shell=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            # zgrep exists with 1 if no matches found
            return []

        return [s for s in p.stdout.splitlines() if s.strip()]

    async def download_and_zgrep(self, codebase_url: str, pattern: str) -> list[str]:
        """
        Download the latest release or tag from the GitHub repository and search for the pattern.
        """
        if await self.fetch_release(codebase_url):
            return self.zgrep(pattern)
        else:
            return []
