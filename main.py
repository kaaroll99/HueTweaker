import discord
from discord.ext import commands, tasks
import asyncio
import config
from config import bot
import logging
from database import database
import topgg
import datetime
import json
import requests

config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')
cogs = ['help', 'color', 'embed', 'joinListener', 'vote']


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

        topgg_token = token_file['TOP_GG_TOKEN']
        bot.topggpy = topgg.DBLClient(bot, topgg_token)

        @tasks.loop(hours=2)
        async def update_stats_topgg():
            try:
                await bot.topggpy.post_guild_count()

                data = {
                    "guilds": 2
                }
                data_formated = json.dumps(data)

                logging.info(f"Posted server count to topgg ({bot.topggpy.guild_count})")
                logging.info(f"Posted server count to discordbotlist ({json.loads(data_formated)['guilds']})")
            except Exception as e:
                logging.warning(f"Failed to post server count to topgg - {e.__class__.__name__}: {e}")

        @tasks.loop(hours=2)
        async def update_stats_dbl():
            print(len(bot.guilds))
            print(bot.topggpy.guild_count)
            try:
                data = {
                    "guilds": len(bot.guilds)
                }

                # logging.info(f"Posted server count to discordbotlist ({data["guilds"]})")
            except Exception as e:
                logging.warning(f"Failed to post server count to discordbotlist - {e.__class__.__name__}: {e}")

        @tasks.loop(hours=24)
        async def database_backup():
            try:
                db_file = discord.File("databases/guilds.db", filename=f"{str(datetime.date.today().strftime('%Y-%m-%d'))}.db")
                await bot.get_channel(1209974090509713438).send(file=db_file)
                logging.info(f"Database saved to {db_file}")
            except Exception as e:
                logging.warning(f"Database backup error - {e.__class__.__name__}: {e}")

        @tasks.loop(hours=48)
        async def send_command_list():
            url = f"https://discordbotlist.com/api/v1/bots/1209187999934578738/commands"

            with open("commands_list.json", "r") as f:
                json_payload = json.load(f)

            headers = {
                "Authorization": token_file['DISCORDBOTLIST_TOKEN'],
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=json_payload, headers=headers)

            if response.status_code == 200:
                logging.info(f"Server command list has been updated: {response.status_code}")
            else:
                logging.warning(f"Failed to post server commands - {response.status_code}")

        update_stats_topgg.start()
        update_stats_dbl.start()
        database_backup.start()
        send_command_list.start()

        logging.info('Bot is running.')
        for cog in cogs:
            await bot.load_extension(f"cogs.{cog}")
        await bot.start(token_file['TOKEN'])

try:
    asyncio.run(main())
except KeyboardInterrupt:
    logging.warning(f"bot has been terminated from console line")
