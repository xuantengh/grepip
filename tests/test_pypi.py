import unittest
import asyncio

import grepip.pypi as gp


class TestPypiPackageInfo(unittest.IsolatedAsyncioTestCase):
    interested_packages = {
        "numpy": "https://github.com/numpy/numpy",
        "requests": "https://github.com/psf/requests",
        "flask": "https://github.com/pallets/flask",
        "django": "https://github.com/django/django",
        "pandas": "https://github.com/pandas-dev/pandas",
        "cupy": "https://github.com/cupy/cupy",
    }

    async def test_func_wrap(self):
        target_fn = gp.fetch_pypi_package_info
        self.assertEqual(target_fn.__name__, "fetch_pypi_package_info")
        self.assertEqual(target_fn.__module__, "grepip.pypi")

    async def test_fetch_pypi_package_info(self):
        tasks: list[asyncio.Task] = []
        async with asyncio.TaskGroup() as tg:
            for pkg in self.interested_packages:
                tasks.append(tg.create_task(gp.fetch_pypi_package_info(pkg)))  # noqa: F405
        for i, (pkg, url) in enumerate(self.interested_packages.items()):
            package_info: gp.PypiPackageInfo = tasks[i].result()  # noqa: F405

            self.assertIsNotNone(package_info)
            self.assertEqual(package_info.name, pkg)
            self.assertEqual(package_info.source_url.strip("/"), url)

    async def test_fetch_pypi_popular_packages(self):
        # https://hugovk.github.io/top-pypi-packages/
        popular_packages: list[str] = await gp.fetch_popular_pypi_packages()
        self.assertTrue(len(popular_packages) > 0, "No popular PyPI packages found")

        num_url_accessible = 300
        self.assertLessEqual(num_url_accessible, len(popular_packages))
        semaphore = asyncio.Semaphore(10)
        tasks: list[asyncio.Task] = []
        async with semaphore, asyncio.TaskGroup() as tg:
            for pkg in popular_packages[:num_url_accessible]:
                task = tg.create_task(gp.fetch_pypi_package_info(pkg))
                tasks.append(task)
