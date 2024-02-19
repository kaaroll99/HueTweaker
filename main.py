import discord
from discord.ext import commands
import asyncio
import config
from config import bot
import logging
from database import database

config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')
cogs = ['help', 'color', 'embed']


@bot.event
async def on_ready():
    try:
        cmds = []
        synced = await bot.tree.sync()
        for command in synced:
            cmds.append(command.name)
        bot.remove_command('help')
        logging.info(f"Cogs ({len(cogs)}): " + ", ".join([f'{cog}' for cog in cogs]))
        logging.info(f"Active commands ({len(cmds)}): " + ", ".join([f'{cmd}' for cmd in cmds]))
    except Exception as e:
        print(e)


async def main():
    async with bot:
        logging.info('Bot is running.')
        for cog in cogs:
            await bot.load_extension(f"cogs.{cog}")
        await bot.start(token_file['TOKEN'])

try:
    asyncio.run(main())
except KeyboardInterrupt:
    logging.warning(f"bot has been terminated from console line")
