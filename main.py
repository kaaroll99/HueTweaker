import discord
from discord.ext import commands, tasks
import asyncio
import config
from config import bot
import logging
from database import database
import topgg
import datetime

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

        logging.info(f"Cogs ({len(cogs)}): " + ", ".join([f'{cog}' for cog in cogs]))
        logging.info(f"Active commands ({len(cmds)}): " + ", ".join([f'{cmd}' for cmd in cmds]))
    except Exception as e:
        print(e)


async def main():
    db = database.Database(url=f"sqlite:///databases/guilds.db")
    db.connect()
    db.database_init()
    async with bot:

        dbl_token = token_file['TOP_GG_TOKEN']
        bot.topggpy = topgg.DBLClient(bot, dbl_token)

        @tasks.loop(minutes=60)
        async def update_stats():
            try:
                await bot.topggpy.post_guild_count()
                logging.info(f"Posted server count ({bot.topggpy.guild_count})")
            except Exception as e:
                logging.critical(f"Failed to post server count - {e.__class__.__name__}: {e}")

        @tasks.loop(hours=24)
        async def database_backup():
            try:
                db_file = discord.File("databases/guilds.db", filename=f"{str(datetime.date.today().strftime('%Y-%m-%d'))}.db")
                await bot.get_channel(1209974090509713438).send(file=db_file)
                logging.info(f"Database saved to {db_file}")
            except Exception as e:
                logging.critical(f"Database backup error - {e.__class__.__name__}: {e}")

        update_stats.start()
        database_backup.start()

        logging.info('Bot is running.')
        for cog in cogs:
            await bot.load_extension(f"cogs.{cog}")
        await bot.start(token_file['TOKEN'])

try:
    asyncio.run(main())
except KeyboardInterrupt:
    logging.warning(f"bot has been terminated from console line")
