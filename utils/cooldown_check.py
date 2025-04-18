import aiohttp
import discord
from discord import app_commands

from utils.data_loader import load_yml

token_file = load_yml('assets/token.yml')


async def check_query(user_id: int):
    url = f'https://top.gg/api/bots/1209187999934578738/check'
    headers = {
        'Authorization': token_file['TOP_GG_TOKEN'],
        'Content-Type': 'application/json'
    }
    data = {
        'userId': user_id,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                data = await response.json()
                if data['voted'] > 0:
                    return True
                else:
                    return False
            else:
                return True


async def is_user_on_cooldown(interaction: discord.Interaction):
    query = await check_query(interaction.user.id)
    if query:
        return app_commands.Cooldown(1, 3.0)
    else:
        return app_commands.Cooldown(1, 60.0)
    