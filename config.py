import logging
import os
import re
from logging.handlers import TimedRotatingFileHandler

import discord

from database import database
from utils.data_loader import load_yml


def setup_logger():
    os.makedirs('logs', exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    latest_handler = logging.FileHandler('logs/latest.log', mode='w', encoding='utf-8')
    latest_handler.setFormatter(formatter)
    logger.addHandler(latest_handler)

    daily_handler = TimedRotatingFileHandler(
        'logs/daily.log',
        when="midnight",
        backupCount=7,
        encoding='utf-8'
    )
    daily_handler.setFormatter(formatter)
    daily_handler.namer = lambda name: name.replace("daily.log.", "") + ".log"
    logger.addHandler(daily_handler)

    return logger


def init_bot():
    from bot_init import MyBot

    bot = MyBot(
        command_prefix="!$%ht",
        intents=intents,
        activity=activity,
        status=discord.Status.online,
        shard_count=2
    )
    bot.remove_command('help')
    return bot


langs = ["en-US", "pl"]
intents = discord.Intents.none()
intents.guilds = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.playing, name="/help")
bot = init_bot()
bot.remove_command('help')

token_file = load_yml('assets/token.yml')
if token_file.get('system', None) == 'dev':
    db = database.Database(url=f"sqlite:///assets/guilds.db")
else:
    db = database.Database(
        url=f"mysql+pymysql://{token_file['db_login']}:{token_file['db_pass']}@{token_file['db_host']}/{token_file['db_name']}")

hex_regex = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
rgb_regex = re.compile(r"^rgb\((25[0-5]|2[0-4]\d|[01]?\d{1,2})\s*,\s*(25[0-5]|2[0-4]\d|[01]?\d{1,2})\s*,\s*(25[0-5]|2[0-4]\d|[01]?\d{1,2})\)$")
hsl_regex = re.compile(r"^hsl\((\d+(\.\d+)?|100(\.0+)?),\s*(\d+(\.\d+)?|100(\.0+)?)%\s*,\s*(\d+(\.\d+)?|100(\.0+)?)%\)$")
cmyk_regex = re.compile(r"^cmyk\((100(\.0+)?|\d+(\.\d+)?)%,\s*(100(\.0+)?|\d+(\.\d+)?)%,\s*(100(\.0+)?|\d+(\.\d+)?)%,\s*(100(\.0+)?|\d+(\.\d+)?)%\)$")

logger = setup_logger()
logger.info("Log file has been created.")
