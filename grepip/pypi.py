from typing import Any, Optional, Callable
import asyncio
import aiohttp
import aiofiles
import dataclasses
import pathlib
import json
import functools

__all__ = [
    "fetch_pypi_package_info",
    "PypiPackageInfo",
]

_GREPIP_CACHE_DIR = pathlib.Path.home() / ".cache" / "grepip"

# TODO: rwlock
_pypi_cache_lock = asyncio.Lock()


def _pypi_cache(
    fn: Callable[..., "PypiPackageInfo"],
) -> Callable[..., "PypiPackageInfo"]:
    # TODO: use environment variable to disable cache behavior
    cache_file = _GREPIP_CACHE_DIR / "pypi.json"
    if not cache_file.exists():
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump({}, f)

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        async with _pypi_cache_lock:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
        package_name = args[0] if args else kwargs.get("name")
        if package_name in cache_data and cache_data[package_name].get("source_url"):
            return PypiPackageInfo(
                name=package_name, source_url=cache_data[package_name].get("source_url")
            )
        else:
            result: PypiPackageInfo = await fn(*args, **kwargs)
            async with _pypi_cache_lock:
                # we need to load again under lock to obtain the latest changes
                async with aiofiles.open(cache_file, "r") as f:
                    cache_data = json.loads(await f.read())
                cache_data[package_name] = {"source_url": result.source_url}
                async with aiofiles.open(cache_file, "w") as f:
                    await f.write(json.dumps(cache_data))
            return result

    return wrapper


@dataclasses.dataclass(frozen=True)
class PypiPackageInfo:
    name: str
    source_url: Optional[str]


async def _fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()


@_pypi_cache
async def fetch_pypi_package_info(name: str) -> PypiPackageInfo:
    # https://docs.pypi.org/api/
    pypi_endpoint_url = f"https://pypi.org/pypi/{name}/json"
    meta: dict[str, Any] = await _fetch_json(pypi_endpoint_url)
    source_url = None
    possible_source_keys = (
        "source",
        "Source",
        "Code",
        "Source code",
        "repository",
        "Repository",
        "GitHub",
        "Source Code",
        "Homepage",
    )
    for sk in possible_source_keys:
        try:
            source_url = meta["info"]["project_urls"].get(sk, None)
        except AttributeError:
            source_url = None
        if source_url:
            break

    return PypiPackageInfo(name=name, source_url=source_url)


_DEFAULT_ENDPOINT_URL = (
    "https://hugovk.github.io/top-pypi-packages/top-pypi-packages.min.json"
)


async def fetch_popular_pypi_packages(
    endpoint_url: str = _DEFAULT_ENDPOINT_URL,
) -> list[str]:
    data = None
    popular_json = _GREPIP_CACHE_DIR / "top-pypi-packages.min.json"
    # TODO: set cache TTL
    if popular_json.exists():
        async with aiofiles.open(popular_json, "r") as f:
            data = json.loads(await f.read())
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint_url) as response:
                response.raise_for_status()
                data = await response.json()
            async with aiofiles.open(popular_json, "w") as f:
                await f.write(json.dumps(data))

    assert data, "Failed to open popular PyPI packages data"
    return [item["project"] for item in data["rows"]]
