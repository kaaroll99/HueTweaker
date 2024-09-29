import os

from dotenv import load_dotenv

from database import database
from utils.console_logger import setup_logger

load_dotenv(".env")

if os.getenv('system', None) == 'DEV':
    db = database.Database(url=os.getenv('db_local_uri'))
else:
    db = database.Database(
        url=f"mysql+pymysql://{os.getenv('db_login')}:{os.getenv('db_pass')}@{os.getenv('db_host')}/{os.getenv('db_name')}")

logger = setup_logger()
logger.info("Log file has been created.")
