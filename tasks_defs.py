import discord
from discord.ext import commands, tasks
import config
from config import bot
import logging
import topgg
import datetime
import json
import requests

config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')


def update_stats(name: str, url: str, data, token: str):
    json_data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    response = requests.post(url, data=json_data, headers=headers)
    if response.status_code == 200:
        logging.info(f"Posted servers count to {name} ({data})")
    else:
        logging.warning(f"Failed to post guilds count to {name} - {response.status_code}")


top_gg_times = [
    datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')),
    datetime.time(hour=12, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET'))
]


@tasks.loop(time=top_gg_times)
async def update_stats_topgg():
    topgg_token = token_file['TOP_GG_TOKEN']
    bot.topggpy = topgg.DBLClient(bot, topgg_token)
    try:
        await bot.topggpy.post_guild_count()
        logging.info(f"Posted server count to topgg ({bot.topggpy.guild_count})")
    except Exception as e:
        logging.warning(f"Failed to post server count to topgg - {e.__class__.__name__}: {e}")


@tasks.loop(time=datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')))
async def update_stats_taks():
    await bot.wait_until_ready()

    update_stats(
        "discordbotlist",
        "https://discordbotlist.com/api/v1/bots/1209187999934578738/stats",
        {"users": sum(guild.member_count for guild in bot.guilds), "guilds": len(bot.guilds)},
        token_file['DISCORDBOTLIST_TOKEN']
    )


@tasks.loop(time=datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')))
async def database_backup():
    await bot.wait_until_ready()
    try:
        db_file = discord.File("databases/guilds.db", filename=f"{str(datetime.date.today().strftime('%Y-%m-%d'))}.db")
        channel = bot.get_channel(config_file['db_backup_channel'])

        if channel is None:
            logging.warning(f"Backup channel not found.")
            return
        await channel.send(file=db_file)
        logging.info(f"Database saved to {db_file.filename}")
    except Exception as e:
        logging.warning(f"Database backup error - {e.__class__.__name__}: {e}")


@tasks.loop(hours=72)
async def send_command_list():
    url = f"https://discordbotlist.com/api/v1/bots/1209187999934578738/commands"
    with open("assets/commands_list.json", "r") as f:
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
