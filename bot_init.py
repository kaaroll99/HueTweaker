import asyncio
import logging

import discord
from discord import app_commands, Locale
from discord.ext import commands
from pyexpat.errors import messages

from utils.data_loader import load_json, load_yml


import asyncio
import logging
from discord import app_commands

class MyBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_locale = Locale.american_english
        self.NEED_SYNC = True

    async def setup_hook(self):
        cogs = ['help', 'set', 'remove', 'check', 'force', 'setup', 'joinListener', 'vote', 'select']
        logging.info("Loading extensions: " + ", ".join(cogs))
        for cog in cogs:
            try:
                logging.info(f"Loading {cog} cog ...")
                await self.load_extension(f"cogs.{cog}")
            except Exception as e:
                logging.error(f"Failed to load extension {cog}: {e}")
        logging.info("Loading of extensions completed")

        if self.NEED_SYNC:
            logging.info("Command tree synchronization ...")
            await self.tree.sync()
            logging.info("Command tree synchronization completed")
            self.NEED_SYNC = False
        else:
            logging.info("Skipping command tree synchronization")


intents = discord.Intents.none()
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

cmd_messages = load_yml('assets/messages.yml')
