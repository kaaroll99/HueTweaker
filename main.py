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

        # with open("assets/avatar_animated_500.gif", "rb") as f:
        #     await bot.user.edit(avatar=f.read())

        logging.info(f"Cogs ({len(cogs)}): " + ", ".join([f'{cog}' for cog in cogs]))
        logging.info(f"Active commands ({len(cmds)}): " + ", ".join([f'{cmd}' for cmd in cmds]))
    except Exception as e:
        print(e)


async def main():
    db = database.Database(url=f"sqlite:///databases/guilds.db")
    db.connect()
    db.database_init()
    async with bot:

        @tasks.loop(hours=24)
        async def update_stats_taks():
            await bot.wait_until_ready()

            tasks_defs.update_stats(
                "discordbotlist",
                "https://discordbotlist.com/api/v1/bots/1209187999934578738/stats",
                {"users": sum(guild.member_count for guild in bot.guilds), "guilds": len(bot.guilds)},
                token_file['DISCORDBOTLIST_TOKEN']
            )

        tasks_defs.update_stats_topgg.start()
        update_stats_taks.start()
        tasks_defs.database_backup.start()
        tasks_defs.send_command_list.start()

        logging.info('Bot is running.')
        for cog in cogs:
            await bot.load_extension(f"cogs.{cog}")
        await bot.start(token_file['TOKEN'])
try:
    asyncio.run(main())

except KeyboardInterrupt:
    logging.warning(f"bot has been terminated from console line")
