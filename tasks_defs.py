# import datetime
# import logging
# import os
#
# import requests
# import topgg
# from discord.ext import tasks
# from dotenv import load_dotenv
# from msgspec import json
#
# from bot_init import bot
# from utils.data_loader import load_json
#
# load_dotenv(".env")
#
# top_gg_times = [
#     datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')),
#     datetime.time(hour=12, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET'))
# ]
#
#
# @tasks.loop(time=top_gg_times)
# async def update_stats_topgg():
#     bot.topggpy = topgg.DBLClient(bot, os.getenv('top_gg_token'))
#     try:
#         await bot.topggpy.post_guild_count()
#         logging.info(f"Posted server info to topgg ({bot.topggpy.guild_count})")
#     except Exception as e:
#         logging.warning(f"Failed to post server info to topgg - {e.__class__.__name__}: {e}")
#
#
# @tasks.loop(time=datetime.time(hour=1, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=1), 'CET')))
# async def update_stats_taks():
#     await bot.wait_until_ready()
#     stats_url = "https://discordbotlist.com/api/v1/bots/1209187999934578738/stats"
#     stats_headers = {"Content-Type": "application/json", "Authorization": os.getenv('discordbotlist_token')}
#     stats_data = json.encode({"users": sum(guild.member_count for guild in bot.guilds), "guilds": len(bot.guilds)})
#     try:
#         response = requests.post(stats_url, data=stats_data, headers=stats_headers, timeout=10)
#         response.raise_for_status()
#         logging.info(f"Servers count has been updated: {response.status_code}")
#     except requests.exceptions.Timeout:
#         logging.error("Request timed out")
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Failed to post servers count: {e}")
#     except Exception as e:
#         logging.error(f"Unexpected error occurred: {e}", exc_info=True)
#
#     url = f"https://discordbotlist.com/api/v1/bots/1209187999934578738/commands"
#     json_payload = load_json("assets/commands_list.json")
#     headers = {
#         "Authorization": os.getenv('discordbotlist_token'),
#         "Content-Type": "application/json"
#     }
#     try:
#         response = requests.post(url, json=json_payload, headers=headers, timeout=10)
#         response.raise_for_status()
#         logging.info(f"Server command list has been updated: {response.status_code}")
#     except requests.exceptions.Timeout:
#         logging.error("Request timed out")
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Failed to post bot commands: {e}")
#     except Exception as e:
#         logging.error(f"Unexpected error occurred: {e}", exc_info=True)
