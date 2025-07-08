import asyncio
import grepip.search as gs
import unittest
from tqdm.asyncio import tqdm


class TestGitHubSearch(unittest.IsolatedAsyncioTestCase):
    async def test_cupy(self):
        searcher = gs.gh.GitHubSearch()
        await searcher.fetch_release("https://github.com/cupy/cupy")
        results = searcher.zgrep("cudaMemcpy")

        self.assertIsNotNone(results)
        for line in results:
            self.assertIn("cudaMemcpy", line)

    async def test_tqdm(self):
        packages = [
            "numpy/numpy",
            "pandas-dev/pandas",
        ]
        searcher = gs.gh.GitHubSearch()
        tasks: list[asyncio.Task] = []
        with tqdm(total=len(packages), desc="Downloading and searching") as pbar:
            async with asyncio.TaskGroup() as tg:
                for package in packages:
                    url = f"https://github.com/{package}"
                    task = tg.create_task(
                        searcher.download_and_zgrep(url, "PyModule_Create")
                    )
                    task.add_done_callback(lambda _: pbar.update(1))
                    tasks.append(task)

        results = await asyncio.gather(*tasks)
        self.assertIsNotNone(results)
