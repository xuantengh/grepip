import logging
import pathlib
import aiohttp

__all__ = [
    "get_cache_dir",
    "is_url_accessible",
    "GREPIP_RETRY_TIMES",
]

GREPIP_RETRY_TIMES = 3
_GREPIP_CACHE_DIR = pathlib.Path.home() / ".cache" / "grepip"


def get_cache_dir() -> pathlib.Path:
    global _GREPIP_CACHE_DIR
    if not _GREPIP_CACHE_DIR.exists():
        _GREPIP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _GREPIP_CACHE_DIR


async def is_url_accessible(url: str) -> bool:
    if not url or len(url) == 0:
        return False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200
    except Exception:
        return False


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(name)
