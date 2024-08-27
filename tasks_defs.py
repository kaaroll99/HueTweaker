import csv
import datetime
from utils.data_loader import load_json
import logging

import discord
import requests
import topgg
from discord.ext import tasks

import config
import utils.data_loader
from config import bot
from msgspec import json

config_file = utils.data_loader.load_yml('assets/config.yml')
token_file = utils.data_loader.load_yml('assets/token.yml')


top_gg_times = [
    datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')),
    datetime.time(hour=12, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET'))
]


@tasks.loop(time=top_gg_times)
async def update_stats_topgg():
    topgg_token = token_file['TOP_GG_TOKEN']
    bot.topggpy = topgg.DBLClient(topgg_token)
    try:
        await bot.topggpy.post_guild_count(int(len(bot.guilds)))
        # await bot.topggpy.post_shard_count
        logging.info(f"Posted server info to topgg ({bot.topggpy.guild_count})")
    except Exception as e:
        logging.warning(f"Failed to post server info to topgg - {e.__class__.__name__}: {e}")


@tasks.loop(time=datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')))
async def update_stats_taks():
    await bot.wait_until_ready()
    stats_url = "https://discordbotlist.com/api/v1/bots/1209187999934578738/stats"
    stats_headers = {"Content-Type": "application/json", "Authorization": token_file['DISCORDBOTLIST_TOKEN']}
    stats_data = json.encode({"users": sum(guild.member_count for guild in bot.guilds), "guilds": len(bot.guilds)})
    try:
        response = requests.post(stats_url, data=stats_data, headers=stats_headers, timeout=10)
        response.raise_for_status()
        logging.info(f"Servers count has been updated: {response.status_code}")
    except requests.exceptions.Timeout:
        logging.error("Request timed out")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to post servers count: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}", exc_info=True)

    url = f"https://discordbotlist.com/api/v1/bots/1209187999934578738/commands"
    json_payload = load_json("assets/commands_list.json")
    headers = {
        "Authorization": token_file['DISCORDBOTLIST_TOKEN'],
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=json_payload, headers=headers, timeout=10)
        response.raise_for_status()
        logging.info(f"Server command list has been updated: {response.status_code}")
    except requests.exceptions.Timeout:
        logging.error("Request timed out")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to post bot commands: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}", exc_info=True)
