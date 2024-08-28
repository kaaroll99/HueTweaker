import asyncio
import csv
import logging
from datetime import datetime

import discord

import tasks_defs
from config import db, bot
from utils.data_loader import load_yml

token_file = load_yml('assets/token.yml')
config_file = load_yml('assets/config.yml')


@bot.event
async def on_ready():
    csv_file = 'guilds_info.csv'
    fields = ['Guild Name', 'Guild ID', 'Owner Name', 'Member Count', 'Preferred Locale']

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for guild in bot.guilds:
            owner_name = guild.owner.name if guild.owner else "-"
            writer.writerow({
                'Guild Name': guild.name,
                'Guild ID': guild.id,
                'Owner Name': owner_name,
                'Member Count': guild.member_count,
                'Preferred Locale': guild.preferred_locale
            })
    logging.info(15 * '=' + " Bot is ready. " + 15 * "=")


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
