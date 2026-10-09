import logging
import time

import aiohttp
import discord

from constants import BOT_ID, NEW_GUILD_GRACE

logger = logging.getLogger(__name__)

VOTED_TTL = 60 * 60
NOT_VOTED_TTL = 60
REQUEST_TIMEOUT = 3


class VoteChecker:
    def __init__(self, token: str | None) -> None:
        self._token = token
        self._cache: dict[int, tuple[bool, float]] = {}

    async def has_voted(self, user_id: int) -> bool:
        now = time.monotonic()
        cached = self._cache.get(user_id)
        if cached is not None and cached[1] > now:
            return cached[0]
        if not self._token:
            return True

        voted = await self._fetch(user_id)
        if voted is None:
            return True
        self._cache[user_id] = (voted, now + (VOTED_TTL if voted else NOT_VOTED_TTL))
        self._prune(now)
        return voted

    async def _fetch(self, user_id: int) -> bool | None:
        url = f"https://top.gg/api/bots/{BOT_ID}/check"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params={"userId": str(user_id)},
                    headers={"Authorization": self._token},
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                ) as response:
                    if response.status != 200:
                        logger.warning("top.gg vote check for %s failed: HTTP %s", user_id, response.status)
                        return None
                    data = await response.json()
                    return bool(data.get("voted"))
        except Exception as e:
            logger.warning("top.gg vote check for %s failed: %r", user_id, e)
            return None

    def _prune(self, now: float) -> None:
        if len(self._cache) > 10_000:
            self._cache = {k: v for k, v in self._cache.items() if v[1] > now}


class UsageQuota:
    def __init__(self, uses: int, window: float) -> None:
        self.uses = uses
        self.window = window
        self._stamps: dict[int, list[float]] = {}

    def _recent(self, user_id: int, now: float) -> list[float]:
        stamps = [t for t in self._stamps.get(user_id, ()) if now - t < self.window]
        if stamps:
            self._stamps[user_id] = stamps
        else:
            self._stamps.pop(user_id, None)
        return stamps

    def retry_after(self, user_id: int) -> float:
        now = time.monotonic()
        stamps = self._recent(user_id, now)
        if len(stamps) < self.uses:
            return 0.0
        return self.window - (now - stamps[-self.uses])

    def consume(self, user_id: int) -> None:
        now = time.monotonic()
        self._recent(user_id, now)
        self._stamps.setdefault(user_id, []).append(now)
        if len(self._stamps) > 10_000:
            for key in list(self._stamps):
                self._recent(key, now)


def in_grace_period(guild: discord.Guild) -> bool:
    """True during the first ``NEW_GUILD_GRACE`` seconds after the bot joined ``guild``."""
    joined = guild.me.joined_at if guild.me is not None else None
    return joined is not None and (discord.utils.utcnow() - joined).total_seconds() < NEW_GUILD_GRACE
