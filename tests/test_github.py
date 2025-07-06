import grepip.search as gs
from grepip.utils import is_url_accessible
import unittest

import asyncio


class TestGitHubSearch(unittest.IsolatedAsyncioTestCase):
    async def test_cupy(self):
        searcher = gs.gh.GitHubSearch()
        results: list[gs.gh.CodeResult] = await searcher.search(
            "cupy/cupy", "cudaMemcpy"
        )
        self.assertTrue(len(results) > 0, "cudaMemcpy must in cupy/cupy")

        tasks: list[asyncio.Task] = []
        async with asyncio.TaskGroup() as tg:
            for result in results:
                task = tg.create_task(is_url_accessible(result.http_url))
                tasks.append(task)

        for i, task in enumerate(tasks):
            self.assertTrue(
                task.result(),
                f"URL {results[i].http_url} for file {results[i].path} is not accessible",
            )
