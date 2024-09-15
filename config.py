from database import database
from utils.console_logger import setup_logger
from utils.data_loader import load_yml

token_file = load_yml('assets/token.yml')
config_file = load_yml('assets/config.yml')
if token_file.get('system', None) == 'dev':
    db = database.Database(url=f"sqlite:///assets/guilds.db")
else:
    db = database.Database(
        url=f"mysql+pymysql://{token_file['db_login']}:{token_file['db_pass']}@{token_file['db_host']}/{token_file['db_name']}")

logger = setup_logger()
logger.info("Log file has been created.")

langs = config_file['langs']
