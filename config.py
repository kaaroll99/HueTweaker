import yaml
import discord
from discord.ext import commands
from logging.handlers import TimedRotatingFileHandler
from database import database, model
import logging
import re


def load_yml(path):
    with open(path, 'r', encoding='utf-8') as file:
        output = yaml.safe_load(file)
    return output


intents = discord.Intents.none()
intents.guilds = True
intents.members = True

activity = discord.Activity(type=discord.ActivityType.playing, name="/help")
bot = commands.Bot(command_prefix="!$%ht", intents=intents, activity=activity, status=discord.Status.online)
bot.remove_command('help')

token_file = load_yml('token.yml')
if token_file.get('system', None) == 'dev':
    db = database.Database(url=f"sqlite:///databases/guilds.db")
else:
    db = database.Database(
        url=f"mysql+pymysql://{token_file['db_login']}:{token_file['db_pass']}@{token_file['db_host']}/{token_file['db_name']}")

hex_regex = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
rgb_regex = re.compile(r"^rgb\((25[0-5]|2[0-4]\d|[01]?\d{1,2})\s*,\s*(25[0-5]|2[0-4]\d|[01]?\d{1,2})\s*,\s*(25[0-5]|2[0-4]\d|[01]?\d{1,2})\)$")
hsl_regex = re.compile(r"^hsl\((\d+(\.\d+)?|100(\.0+)?),\s*(\d+(\.\d+)?|100(\.0+)?)%\s*,\s*(\d+(\.\d+)?|100(\.0+)?)%\)$")
cmyk_regex = re.compile(r"^cmyk\((100(\.0+)?|\d+(\.\d+)?)%,\s*(100(\.0+)?|\d+(\.\d+)?)%,\s*(100(\.0+)?|\d+(\.\d+)?)%,\s*(100(\.0+)?|\d+(\.\d+)?)%\)$")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

log_file = f'logs/latest.log'
file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.root.addHandler(file_handler)

log_file = f'logs/info'
handler = TimedRotatingFileHandler(log_file, when="midnight", encoding='utf-8')
handler.namer = lambda name: name.replace(".log", "") + ".log"
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.root.addHandler(handler)
logger.info("Log file has been created.")
