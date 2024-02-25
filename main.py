import discord
from discord.ext import commands
import asyncio
import config
from config import bot
import logging
from database import database
from watchdog.observers import Observer
from watchdog_handler import FileHandler

config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')
cogs = ['help', 'color', 'embed', 'joinListener']


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
