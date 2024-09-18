import logging
import asyncio
import discord
from discord import app_commands, Locale
from discord.ext import commands

from utils.data_loader import load_json

translations = load_json('lang/translations.json')


class MyBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_queue = asyncio.Queue()
        self.background_tasks = []
        self.default_locale = Locale.american_english

    async def setup_hook(self):
        cogs = ['help', 'set', 'remove', 'check', 'force', 'setup', 'joinListener', 'vote', 'select']
        logging.info("Loading extensions: " + ", ".join(cogs))
        for i, cog in enumerate(cogs, start=1):
            try:
                await self.load_extension(f"cogs.{cog}")
                print(f"{round((i / len(cogs)) * 100, 2)}%")
                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Failed to load extension {cog}: {e}")
        logging.info("Loading of extensions completed")
        logging.info("Loading translator ...")
        await self.tree.set_translator(MyTranslator(self))
        logging.info("Loading translator completed")
        logging.info("Command tree synchronization ...")
        # await self.tree.sync()
        logging.info("Command tree synchronization completed")
        self.background_tasks.append(self.loop.create_task(self.process_command_queue()))

    async def process_command_queue(self):
        while True:
            command, interaction = await self.command_queue.get()
            try:
                await command(interaction)
            except discord.errors.HTTPException as e:
                if e.status == 429:
                    retry_after = e.retry_after
                    logging.warning(f"Rate limited. Retrying after {retry_after} seconds.")
                    await asyncio.sleep(retry_after)
                    await self.command_queue.put((command, interaction))
                else:
                    logging.error(f"HTTP Exception: {e}")
            finally:
                self.command_queue.task_done()

    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.application_command:
            command = self.tree.get_command(interaction.command.name)
            await self.command_queue.put((command._callback, interaction))
            await interaction.response.defer()
        else:
            await super().on_interaction(interaction)


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
    shard_count=3
)
