import logging
import aiohttp


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
