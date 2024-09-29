# import asyncio
# import logging
# import os
#
# from dotenv import load_dotenv
#
# import tasks_defs
# from bot_init import bot
# from bot import db
#
# load_dotenv(".env")
#
# async def main():
#     with db as db_session:
#         db_session.database_init()
#     async with bot:
#         tasks_defs.update_stats_topgg.start()
#         tasks_defs.update_stats_taks.start()
#
#         logging.info(20 * '=' + " Bot is running. " + 20 * "=")
#         await bot.start(os.getenv('bot_token'))
#
# try:
#     logging.info(20 * '=' + " Starting the bot. " + 20 * "=")
#     asyncio.run(main())
# except KeyboardInterrupt:
#     logging.warning(f"Bot has been terminated from console line")
