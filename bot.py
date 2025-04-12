import asyncio
import datetime
import logging

import discord
from discord import Locale
from discord.ext import commands, tasks

from database import database
from utils.console_logger import setup_logger
from utils.data_loader import load_yml
from utils.stats_api import api_request

setup_logger()
logger = logging.getLogger(__name__)
logger.info("Log file has been created.")
token_file = load_yml('assets/token.yml')

if token_file.get('SYSTEM', None) == 'DEV':
    logging.info(f"Local database connect")
    db = database.Database(url=token_file['DB_LOCAL_URI'])
else:
    logging.info(f"MySQL database connect")
    db = database.Database(
        url=f"mysql+pymysql://{token_file['db_login']}:{token_file['db_pass']}@{token_file['db_host']}/{token_file['db_name']}")

cmd_messages = load_yml('assets/messages.yml')


class MyBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_locale = Locale.american_english
        self.NEED_SYNC = True

    async def load_cogs(self):
        cogs = ['help', 'set', 'remove', 'check', 'force', 'setup', 'joinListener', 'vote', 'select']
        for cog in cogs:
            try:
                await self.load_extension(f"cogs.{cog}")
                logger.info(f"Loaded extension '{cog}'")
            except Exception as e:
                logger.error(f"Failed to load extension {cog}: {e}")

    @tasks.loop(hours=12)
    async def update_stats_task(self):
        server_count = len(self.guilds)
        user_count = sum(guild.member_count for guild in self.guilds)
        await api_request(server_count, user_count)

    @update_stats_task.before_loop
    async def before_status_task(self) -> None:
        await self.wait_until_ready()

    async def setup_hook(self) -> None:
        await self.load_cogs()
        logging.info("Loading of extensions completed")
        if self.NEED_SYNC:
            logging.info("Command tree synchronization ...")
            await self.tree.sync()
            logging.info("Command tree synchronization completed")
            self.NEED_SYNC = False
        else:
            logging.info("Skipping command tree synchronization")

        self.update_stats_task.start()

    async def on_ready(self) -> None:
        await bot.wait_until_ready()
        self.remove_command('help')
        logging.info(20 * '=' + " Bot is ready. " + 20 * "=")

    @staticmethod
    async def on_socket_response(msg) -> None:
        if msg.get('t') == 'RESUMED':
            logging.info('Shard connection resumed.')

    @staticmethod
    async def on_shard_disconnect(shard_id) -> None:
        logging.info(f'Shard ID {shard_id} has disconnected from Gateway, attempting to reconnect...')
        
    @staticmethod
    async def on_shard_ready(shard_id) -> None:
        logging.info(f'Shard ID {shard_id} is ready.')
        
    @staticmethod
    async def on_shard_connect(shard_id) -> None:
        logging.info(f'Shard ID {shard_id} has connected to Gateway.')
        

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.playing, name="/help")

bot = MyBot(
    command_prefix="!$%ht",
    intents=intents,
    activity=activity,
    status=discord.Status.online,
    shard_count=3
)


async def main():
    with db as db_session:
        db_session.database_init()
    async with bot:
        logging.info(20 * '=' + " Starting the bot. " + 20 * "=")
        await bot.start(token_file['TOKEN'])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning(f"Bot has been terminated from console line")
