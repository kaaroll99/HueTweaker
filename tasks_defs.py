import csv
import datetime
import json
import logging

import discord
import requests
import topgg
from discord.ext import tasks

import config
from config import bot

config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')


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
        # await bot.topggpy.post_shard_count
        logging.info(f"Posted server info to topgg ({bot.topggpy.guild_count})")
    except Exception as e:
        logging.warning(f"Failed to post server info to topgg - {e.__class__.__name__}: {e}")


@tasks.loop(time=datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')))
async def update_stats_taks():
    await bot.wait_until_ready()
    stats_url = "https://discordbotlist.com/api/v1/bots/1209187999934578738/stats"
    stats_headers = {"Content-Type": "application/json", "Authorization": token_file['DISCORDBOTLIST_TOKEN']}
    stats_data = json.dumps({"users": sum(guild.member_count for guild in bot.guilds), "guilds": len(bot.guilds)})
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
    with open("assets/commands_list.json", "r") as f:
        json_payload = json.load(f)
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

@tasks.loop(time=datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')))
async def guilds_csv():
    await bot.wait_until_ready()
    try:
        csv_file = 'guilds_info.csv'
        fields = ['Guild Name', 'Guild ID', 'Owner Name', 'Member Count']

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()

            for guild in bot.guilds:
                owner_name = guild.owner.name if guild.owner else "-"
                writer.writerow({
                    'Guild Name': guild.name,
                    'Guild ID': guild.id,
                    'Owner Name': owner_name,
                    'Member Count': guild.member_count,
                })

        file = discord.File(csv_file, filename=f"{str(datetime.date.today().strftime('%Y-%m-%d'))}.csv")
        channel = bot.get_channel(config_file['db_backup_channel'])

        if channel is None:
            logging.warning(f"Backup channel not found.")
            return
        await channel.send(file=file)
        logging.info(f"CSV saved to {file.filename}")
    except Exception as e:
        logging.warning(f"Database backup error - {e.__class__.__name__}: {e}")
