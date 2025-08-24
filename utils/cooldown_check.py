import aiohttp
import discord
from discord import app_commands

from utils.data_loader import load_yml

token_file = load_yml('assets/token.yml')


async def check_query(user_id: int):
    url = f'https://top.gg/api/bots/1209187999934578738/check?userId={user_id}'
    headers = {
        'Authorization': token_file['TOP_GG_TOKEN'],
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if int(data.get('voted', 0)) > 0:
                    return True
                else:
                    return False
            else:
                return True


async def is_user_on_cooldown(interaction: discord.Interaction):
    query = await check_query(interaction.user.id)
    if query:
        return app_commands.Cooldown(1, 5.0)
    else:
        return app_commands.Cooldown(1, 30.0)
