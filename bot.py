import asyncio
import datetime
import logging
import os

import discord
import requests
from discord import Locale
from discord.ext import commands, tasks
from msgspec import json

from database import database
from utils.console_logger import setup_logger
from utils.data_loader import load_json, load_yml

import aiohttp

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

async def post_data(url: str, headers: dict, data: dict, message: str = "server count") -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    logging.info(f'Successfully posted {message} to {url}')
                    return {"status": response.status, "success": True}
                else:
                    logging.warning(f'Failed to post {message} to {url}: {response.status} {response.reason}')
                    return {"status": response.status, "success": False, "reason": response.reason}
    except asyncio.TimeoutError:
        logging.error(f"Request to {url} timed out")
        return {"status": None, "success": False, "reason": "Timeout"}
    except Exception as e:
        logging.error(f'Error posting {message} to {url}: {e}', exc_info=True)
        return {"status": None, "success": False, "reason": str(e)}

class MyBot(commands.AutoShardedBot):
    update_times = [
        datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')),
        datetime.time(hour=12, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET'))
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_locale = Locale.american_english
        self.NEED_SYNC = True

    async def load_cogs(self):
        cogs = ['help', 'set', 'remove', 'check', 'force', 'setup', 'joinListener', 'vote', 'select', 'dev']
        for cog in cogs:
            try:
                await self.load_extension(f"cogs.{cog}")
                logger.info(f"Loaded extension '{cog}'")
            except Exception as e:
                logger.error(f"Failed to load extension {cog}: {e}")

    @tasks.loop(time=update_times)
    async def update_stats_task(self):
        # Update bot stats top.gg
        url = f'https://top.gg/api/bots/1209187999934578738/stats'
        server_count = len(self.guilds)
        headers = {
            'Authorization': token_file['TOP_GG_TOKEN'],
            'Content-Type': 'application/json'
        }
        data = {
            'server_count': server_count,
            'shard_count': 2
        }
        await post_data(url, headers, data, message="stats to Top.gg")
        
        # Update bot stats discordlist.gg
        url = f'https://api.discordlist.gg/v0/bots/1209187999934578738/guilds'
        server_count = len(self.guilds)
        headers = {
            'Authorization': f"Bearer {token_file['DISCORDLIST_GG_TOKEN']}",
            'Content-Type': 'application/json; charset=utf-8'
        }
        data = {
            'count': server_count
        }
        await post_data(url, headers, data, message="stats to discordlist.gg")
        
        # Update bot stats discordbotlist.com
        url = "https://discordbotlist.com/api/v1/bots/1209187999934578738/stats"
        headers = {
            "Content-Type": "application/json",
            "Authorization": token_file['DISCORDBOTLIST_TOKEN']
        }
        data = {
            "users": sum(guild.member_count for guild in self.guilds), 
            "guilds": len(self.guilds)
        }
        await post_data(url, headers, data, message="stats to discordbotlist.com")

        # Update commands list discordbotlist.com
        url = f"https://discordbotlist.com/api/v1/bots/1209187999934578738/commands"
        json_payload = load_json("assets/commands_list.json")
        headers = {
            "Authorization": token_file['DISCORDBOTLIST_TOKEN'],
            "Content-Type": "application/json"
        }
        await post_data(url, headers, json_payload, message="command list")

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
        self.remove_command('help')
        logging.info(20 * '=' + " Bot is ready. " + 20 * "=")


    @staticmethod
    async def on_socket_response(msg) -> None:
        if msg.get('t') == 'RESUMED':
            logging.info('Shard connection resumed.')


    @staticmethod
    async def on_shard_disconnect(shard_id) -> None:
        logging.info(f'Shard ID {shard_id} has disconnected from Gateway, attempting to reconnect...')


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
        logging.info(20 * '=' + " Bot is running. " + 20 * "=")
        await bot.start(token_file['TOKEN'])


if __name__ == "__main__":
    try:
        logging.info(20 * '=' + " Starting the bot. " + 20 * "=")
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning(f"Bot has been terminated from console line")
