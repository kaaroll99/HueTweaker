import re

import discord
from database import database
from utils.console_logger import setup_logger
from utils.data_loader import load_yml


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
