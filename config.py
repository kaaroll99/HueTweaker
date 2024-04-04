import yaml
import discord
from discord.ext import commands
from logging.handlers import TimedRotatingFileHandler
from database import database, model
import logging

intents = discord.Intents.none()
intents.guilds = True
intents.members = True

activity = discord.Activity(type=discord.ActivityType.playing, name="/help")
bot = commands.Bot(command_prefix="!$%ht", intents=intents, activity=activity, status=discord.Status.online)
bot.remove_command('help')

db = database.Database(url=f"sqlite:///databases/guilds.db")

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


def load_yml(path):
    with open(path, 'r', encoding='utf-8') as file:
        output = yaml.safe_load(file)
    return output
