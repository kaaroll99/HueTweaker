import discord
from discord.ext import commands, tasks
import asyncio
import config
from config import bot
import logging
from database import database
from watchdog.observers import Observer
from watchdog_handler import FileHandler
import topgg

config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')
cogs = ['help', 'color', 'embed', 'joinListener']


dbl_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEyMDkxODc5OTk5MzQ1Nzg3MzgiLCJib3QiOnRydWUsImlhdCI6MTcwOTI0MTc0NX0.Ng7tOwfJvj1d53sDVsp-EHgNoIGUt1ntPztMFmObso8"  # set this to your bot's Top.gg token
bot.topggpy = topgg.DBLClient(bot, dbl_token)


@tasks.loop(minutes=30)
async def update_stats():
    """This function runs every 30 minutes to automatically update your server count."""
    try:
        await bot.topggpy.post_guild_count()
        print(f"Posted server count ({bot.topggpy.guild_count})")
    except Exception as e:
        print(f"Failed to post server count\n{e.__class__.__name__}: {e}")

update_stats.start()


@bot.event
async def on_ready():
    try:
        cmds = []
        synced = await bot.tree.sync()
        for command in synced:
            cmds.append(command.name)
        bot.remove_command('help')

        observer = Observer()
        handler = FileHandler(bot, 1209949486571589785, 1209974090509713438)
        observer.schedule(handler, path='logs/', recursive=False)
        observer.start()

        logging.info(f"Cogs ({len(cogs)}): " + ", ".join([f'{cog}' for cog in cogs]))
        logging.info(f"Active commands ({len(cmds)}): " + ", ".join([f'{cmd}' for cmd in cmds]))
    except Exception as e:
        print(e)


async def main():
    db = database.Database(url=f"sqlite:///databases/guilds.db")
    db.connect()
    db.database_init()
    async with bot:
        logging.info('Bot is running.')
        for cog in cogs:
            await bot.load_extension(f"cogs.{cog}")
        await bot.start(token_file['TOKEN'])

try:
    asyncio.run(main())
except KeyboardInterrupt:
    logging.warning(f"bot has been terminated from console line")
