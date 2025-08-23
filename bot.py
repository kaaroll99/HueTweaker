import asyncio
import logging
from typing import Any, Dict, Set

import discord
from discord import Locale
from discord.ext import commands, tasks

from database import database
from utils.console_logger import setup_logger
from utils.data_loader import load_yml
from utils.stats_api import api_request

setup_logger()
logger = logging.getLogger("bot")
logger.info("Log file has been created.")


class MyBot(commands.AutoShardedBot):
    def __init__(self, *, config: Dict[str, Any], db: database.Database, messages: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.default_locale = Locale.american_english
        self.config = config
        self.db = db
        self.messages = messages
        self._guild_role_locks: Dict[int, asyncio.Lock] = {}
        self._ready_shards: Set[int] = set()

    async def load_cogs(self) -> None:
        cogs = ['help', 'set', 'remove', 'check', 'force', 'setup', 'joinListener', 'vote', 'select', 'dev']
        for cog in cogs:
            try:
                await self.load_extension(f"cogs.{cog}")
                logger.info("Loaded extension '%s'", cog)
            except Exception:
                logger.exception("Failed to load extension %s", cog)

    @tasks.loop(hours=12)
    async def update_stats_task(self) -> None:
        try:
            if str(self.config.get('SYSTEM')).upper() == 'DEV':
                logger.debug("DEV mode detected - skipping stats API post")
                return
            server_count = len(self.guilds)
            user_count = sum((guild.member_count or 0) for guild in self.guilds)
            await api_request(server_count, user_count)
        except Exception:
            logger.exception("update_stats_task error")

    @update_stats_task.before_loop
    async def before_status_task(self) -> None:
        await self.wait_until_ready()

    async def setup_hook(self) -> None:
        await self.load_cogs()
        logger.info("Sharding configuration: total shards = %d", self.shard_count or -1)
        logger.info("Skipping command tree synchronization")
        self.remove_command('help')
        if not self.update_stats_task.is_running():
            self.update_stats_task.start()

    async def on_ready(self) -> None:
        logger.info(20 * '=' + " Bot is ready. " + 20 * "=")

    async def on_socket_response(self, msg: Dict[str, Any]) -> None:
        if msg.get('t') == 'RESUMED':
            logger.info('Shard connection resumed.')

    async def on_shard_disconnect(self, shard_id: int) -> None:
        logger.warning('Shard %d has disconnected from Gateway, attempting to reconnect...', shard_id)

    async def on_shard_ready(self, shard_id: int) -> None:
        self._ready_shards.add(shard_id)
        logger.info('Shard %d is ready (%d/%d).', shard_id, len(self._ready_shards), self.shard_count)
        if len(self._ready_shards) == self.shard_count:
            logger.info('All shards ready (%d total).', self.shard_count)

    async def on_shard_connect(self, shard_id: int) -> None:
        logger.info('Shard %d has connected to Gateway.', shard_id)


async def main():
    config = load_yml('assets/token.yml')
    messages = load_yml('assets/messages.yml')

    token = config['TOKEN']
    db_url = config['DB_LOCAL_URI']

    logger.info("Local database connect")
    db_instance = database.Database(url=db_url)
    with db_instance as db_session:
        db_session.database_init()

    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True

    activity = discord.CustomActivity(name="Change color of your username!")

    bot = MyBot(
        command_prefix="!$%ht",
        intents=intents,
        activity=activity,
        status=discord.Status.online,
        config=config,
        db=db_instance,
        messages=messages
    )

    async with bot:
        logger.info(20 * '=' + " Starting the bot. " + 20 * "=")
        await bot.start(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Bot has been terminated from console line")
