from typing import Any, Optional, Callable
import asyncio
import aiohttp
import dataclasses
import pathlib
import json
import functools

__all__ = [
    "fetch_pypi_package_info",
    "PypiPackageInfo",
]

# TODO: rwlock
_pypi_cache_lock = asyncio.Lock()


def _pypi_cache(
    fn: Callable[..., "PypiPackageInfo"],
) -> Callable[..., "PypiPackageInfo"]:
    # TODO: use environment variable to disable cache behavior
    _GREPIP_CACHE_PATH = pathlib.Path.home() / ".cache" / "grepip" / "pypi.json"
    if not _GREPIP_CACHE_PATH.exists():
        _GREPIP_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_GREPIP_CACHE_PATH, "w") as f:
            json.dump({}, f)

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        async with _pypi_cache_lock:
            with open(_GREPIP_CACHE_PATH, "r") as f:
                cache_data = json.load(f)
        package_name = args[0] if args else kwargs.get("name")
        if package_name in cache_data and cache_data[package_name].get("source_url"):
            return PypiPackageInfo(
                name=package_name, source_url=cache_data[package_name].get("source_url")
            )
        else:
            result: PypiPackageInfo = await fn(*args, **kwargs)
            cache_data[package_name] = {"source_url": result.source_url}
            async with _pypi_cache_lock:
                with open(_GREPIP_CACHE_PATH, "w") as f:
                    json.dump(cache_data, f)
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
    possible_source_keys = ("source", "Source", "repository", "Source Code")
    for sk in possible_source_keys:
        source_url = meta["info"]["project_urls"].get(sk, None)
        if source_url:
            break

    # if not source_url:
    #     print(name, meta["info"]["project_urls"].keys())

    return PypiPackageInfo(name=name, source_url=source_url)
