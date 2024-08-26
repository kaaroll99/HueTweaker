import asyncio
import logging

import config
import tasks_defs
from config import db, bot

config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')


async def main():
    with db as db_session:
        db_session.database_init()
    async with bot:
        tasks_defs.update_stats_topgg.start()
        tasks_defs.update_stats_taks.start()

        logging.info('Bot is running.')
        await bot.start(token_file['TOKEN'])

try:
    asyncio.run(main())
except KeyboardInterrupt:
    logging.warning(f"Bot has been terminated from console line")
