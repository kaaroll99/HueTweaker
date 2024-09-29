import os

from dotenv import load_dotenv

from database import database

load_dotenv(".env")

if os.getenv('system', None) == 'DEV':
    pass
else:
    db = database.Database(
        url=f"mysql+pymysql://{os.getenv('db_login')}:{os.getenv('db_pass')}@{os.getenv('db_host')}/{os.getenv('db_name')}")

# logger.info("Log file has been created.")
