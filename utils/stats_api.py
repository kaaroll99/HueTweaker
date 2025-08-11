import asyncio
import logging
import random

import aiohttp

from utils.data_loader import load_json, load_yml

token_file = load_yml('assets/token.yml')

MAX_RETRIES = 3
BASE_BACKOFF = 1.0 
MAX_BACKOFF = 8.0
JITTER = 0.3 


async def post_data(url: str, headers: dict, data: dict, message: str = "server count") -> dict:
    """Single HTTP POST with timeout and error handling (no retries)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if 200 <= response.status < 300:
                    logging.info("Posted %s to %s (status=%s)", message, url, response.status)
                    return {"status": response.status, "success": True}
                else:
                    text = await response.text()
                    logging.warning("Failed post %s to %s: %s %s | body=%s", message, url, response.status, response.reason, text[:200])
                    return {"status": response.status, "success": False, "reason": response.reason}
    except asyncio.TimeoutError:
        logging.error("Request timeout posting %s to %s", message, url)
        return {"status": None, "success": False, "reason": "Timeout"}
    except Exception as e:
        logging.error("Error posting %s to %s: %s", message, url, e, exc_info=True)
        return {"status": None, "success": False, "reason": str(e)}


async def post_with_retry(url: str, headers: dict, data: dict, message: str) -> dict:
    """POST with exponential backoff + jitter. Returns final attempt result."""
    for attempt in range(1, MAX_RETRIES + 1):
        result = await post_data(url, headers, data, message)
        if result.get("success"):
            return result
        if attempt < MAX_RETRIES:
            backoff = min(MAX_BACKOFF, BASE_BACKOFF * (2 ** (attempt - 1)))
            # jitter
            jitter_factor = 1 + random.uniform(-JITTER, JITTER)
            sleep_for = backoff * jitter_factor
            logging.debug("Retrying %s (attempt %d/%d) in %.2fs", message, attempt + 1, MAX_RETRIES, sleep_for)
            await asyncio.sleep(sleep_for)
    return result  # last result


async def api_request(server_count: int, user_count: int) -> None:
    """Send stats to external listing APIs with isolation of failures."""
    tasks = []

    # top.gg
    tasks.append(asyncio.create_task(post_with_retry(
        'https://top.gg/api/bots/1209187999934578738/stats',
        {
            'Authorization': token_file['TOP_GG_TOKEN'],
            'Content-Type': 'application/json'
        },
        {'server_count': server_count, 'shard_count': 2},
        'stats to Top.gg'
    )))

    # discordlist.gg
    tasks.append(asyncio.create_task(post_with_retry(
        'https://api.discordlist.gg/v0/bots/1209187999934578738/guilds',
        {
            'Authorization': f"Bearer {token_file['DISCORDLIST_GG_TOKEN']}",
            'Content-Type': 'application/json; charset=utf-8'
        },
        {'count': server_count},
        'stats to discordlist.gg'
    )))

    # discordbotlist.com stats
    tasks.append(asyncio.create_task(post_with_retry(
        'https://discordbotlist.com/api/v1/bots/1209187999934578738/stats',
        {
            'Content-Type': 'application/json',
            'Authorization': token_file['DISCORDBOTLIST_TOKEN']
        },
        {'users': user_count, 'guilds': server_count},
        'stats to discordbotlist.com'
    )))

    # discordbotlist.com commands list
    tasks.append(asyncio.create_task(post_with_retry(
        'https://discordbotlist.com/api/v1/bots/1209187999934578738/commands',
        {
            'Authorization': token_file['DISCORDBOTLIST_TOKEN'],
            'Content-Type': 'application/json'
        },
        load_json('assets/commands_list.json'),
        'command list'
    )))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Summarize
    failures = [r for r in results if isinstance(r, Exception) or (isinstance(r, dict) and not r.get('success'))]
    if failures:
        logging.warning("API stats update finished with %d failure(s)", len(failures))
