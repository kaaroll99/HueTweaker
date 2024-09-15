import logging

import discord
from discord import app_commands, Locale
from discord.ext import commands

from utils.data_loader import load_json

translations = load_json('lang/translations.json')


class MyBot(commands.AutoShardedBot):
    def __init__(self, command_prefix, intents, activity, status, shard_count):
        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
            activity=activity,
            status=status,
            shard_count=shard_count
        )
        self.default_locale = Locale.american_english

    async def setup_hook(self):
        cogs = ['help', 'set', 'remove', 'check', 'force', 'setup', 'joinListener', 'vote', 'select']
        logging.info("Loading extensions: " + ", ".join(cogs))
        for cog in cogs:
            await self.load_extension(f"cogs.{cog}")
        logging.info("Loading of extensions completed")
        logging.info("Loading translator ...")
        await self.tree.set_translator(MyTranslator(self))
        logging.info("Loading translator completed")
        logging.info("Command tree synchronization ...")
        await self.tree.sync()
        logging.info("Command tree synchronization completed")


class MyTranslator(app_commands.Translator):
    def __init__(self, bot):
        self.bot = bot

    async def translate(self, string: app_commands.locale_str, locale: discord.Locale,
                        context: app_commands.TranslationContext) -> str | None:
        if locale.value in translations:
            return translations[locale.value].get(string.message, string.message)
        return translations[self.bot.default_locale.value].get(string.message, string.message)


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
