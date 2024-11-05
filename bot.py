import asyncio
import datetime
import logging
import os

import discord
import requests
import topgg
from discord import Locale
from discord.ext import commands, tasks
from msgspec import json

from database import database
from utils.console_logger import setup_logger
from utils.data_loader import load_json, load_yml

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
    update_times = [
        datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')),
        datetime.time(hour=12, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET'))
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_locale = Locale.american_english
        self.NEED_SYNC = True
        self.topggpy = topgg.DBLClient(self, token_file['TOP_GG_TOKEN'])

    async def load_cogs(self):
        cogs = ['help', 'set', 'remove', 'check', 'force', 'setup', 'joinListener', 'vote', 'select']
        for cog in cogs:
            try:
                await self.load_extension(f"cogs.{cog}")
                logger.info(f"Loaded extension '{cog}'")
            except Exception as e:
                logger.error(f"Failed to load extension {cog}: {e}")

    @tasks.loop(time=update_times)
    async def update_stats_topgg(self):
        url = f'https://top.gg/api/bots/{self.user.id}/stats'
        headers = {
            'Authorization': token_file['TOP_GG_TOKEN'],  # Make sure the key is correct
            'Content-Type': 'application/json'
        }
        data = {
            'server_count': len(self.guilds),
            'shard_count': self.shard_count
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        logging.info('Successfully posted server count to Top.gg')
                    else:
                        logging.warning(f'Failed to post server count to Top.gg: {response.status} {response.reason}')
        except Exception as e:
            logging.error(f'Error posting server count to Top.gg: {e}', exc_info=True)

    @update_stats_topgg.before_loop
    async def before_update_stats_topgg(self):
        await self.wait_until_ready()

    @tasks.loop(time=update_times)
    async def update_stats_task(self):
        stats_url = "https://discordbotlist.com/api/v1/bots/1209187999934578738/stats"
        stats_headers = {"Content-Type": "application/json", "Authorization": token_file['discordbotlist_token']}
        stats_data = json.encode({"users": sum(guild.member_count for guild in self.guilds), "guilds": len(self.guilds)})
        try:
            response = requests.post(stats_url, data=stats_data, headers=stats_headers, timeout=10)
            response.raise_for_status()
            logging.info(f"Servers count has been updated: {response.status_code}")
        except requests.exceptions.Timeout:
            logging.error("Request timed out")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to post servers count: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}", exc_info=True)

        url = f"https://discordbotlist.com/api/v1/bots/1209187999934578738/commands"
        json_payload = load_json("assets/commands_list.json")
        headers = {
            "Authorization": token_file['discordbotlist_token'],
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, json=json_payload, headers=headers, timeout=10)
            response.raise_for_status()
            logging.info(f"Server command list has been updated: {response.status_code}")
        except requests.exceptions.Timeout:
            logging.error("Request timed out")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to post bot commands: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}", exc_info=True)


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

        self.update_stats_topgg.start()
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
    shard_count=2
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
