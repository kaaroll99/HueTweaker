import discord
from discord.ext import commands, tasks
import asyncio
import config
from config import bot
import logging
from database import database
import tasks_defs

config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')
cogs = ['help', 'set', 'remove', 'check', 'force', 'toprole', 'embed', 'joinListener', 'vote']


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
    db = database.Database(url=f"sqlite:///databases/guilds.db")
    db.connect()
    db.database_init()
    async with bot:
        tasks_defs.update_stats_topgg.start()
        tasks_defs.update_stats_taks.start()
        tasks_defs.database_backup.start()
        tasks_defs.guilds_csv.start()
        tasks_defs.send_command_list.start()

        logging.info('Bot is running.')
        for cog in cogs:
            await bot.load_extension(f"cogs.{cog}")
        await bot.start(token_file['TOKEN'])
try:
    asyncio.run(main())

except KeyboardInterrupt:
    logging.warning(f"bot has been terminated from console line")
