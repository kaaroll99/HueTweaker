import asyncio
import csv
import logging

import tasks_defs
from bot_init import bot
from config import db
from utils.data_loader import load_yml
import os

token_file = load_yml('assets/token.yml')
config_file = load_yml('assets/config.yml')


@bot.event
async def on_ready():
    bot.remove_command('help')
    # csv_file = 'logs/guilds_info.csv'
    # fields = ['Guild Name', 'Guild ID', 'Owner Name', 'Member Count', 'Preferred Locale']
    #
    # with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    #     writer = csv.DictWriter(f, fieldnames=fields)
    #     writer.writeheader()
    #
    #     for guild in bot.guilds:
    #         owner_name = guild.owner.name if guild.owner else "-"
    #         writer.writerow({
    #             'Guild Name': guild.name,
    #             'Guild ID': guild.id,
    #             'Owner Name': owner_name,
    #             'Member Count': guild.member_count,
    #             'Preferred Locale': guild.preferred_locale
    #         })
    logging.info(20 * '=' + " Bot is ready. " + 20 * "=")


@bot.event
async def on_socket_response(msg):
    if msg.get('t') == 'RESUMED':
        logging.info('Shard connection resumed.')


@bot.event
async def on_shard_disconnect(shard_id):
    logging.info(f'Shard ID {shard_id} has disconnected from Gateway, attempting to reconnect...')


async def main():
    with db as db_session:
        db_session.database_init()
    async with bot:
        tasks_defs.update_stats_topgg.start()
        tasks_defs.update_stats_taks.start()

        logging.info(20 * '=' + " Bot is running. " + 20 * "=")
        await bot.start(token_file['TOKEN'])


try:
    logging.info(20 * '=' + " Starting the bot. " + 20 * "=")
    asyncio.run(main())
except KeyboardInterrupt:
    logging.warning(f"Bot has been terminated from console line")
except discord.errors.HTTPException as e:
    print(e)
    os.system('kill 1')