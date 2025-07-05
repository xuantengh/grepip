import grepip.search as gs
import unittest

import asyncio
import aiohttp


async def is_url_accessible(url: str) -> bool:
    """Check if a URL is accessible."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200
    except Exception:
        return False


class TestGitHubSearch(unittest.IsolatedAsyncioTestCase):
    async def test_cupy(self):
        searcher = gs.gh.GitHubSearch()
        results: list[gs.gh.CodeResult] = await searcher.search(
            "cupy/cupy", "cudaMemcpy"
        )
        self.assertTrue(len(results) > 0, "cudaMemcpy must in cupy/cupy")

        semaphore = asyncio.Semaphore(5)  # rate limit
        tasks: list[asyncio.Task] = []
        async with semaphore, asyncio.TaskGroup() as tg:
            for result in results:
                task = tg.create_task(is_url_accessible(result.http_url))
                tasks.append(task)

        for i, task in enumerate(tasks):
            self.assertTrue(
                task.result(),
                f"URL {results[i].http_url} for file {results[i].path} is not accessible",
            )
