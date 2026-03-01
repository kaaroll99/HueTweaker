import aiohttp
import discord
from discord import app_commands

from constants import BOT_ID
from utils.data_loader import load_yml

token_file = load_yml('assets/token.yml')


async def check_query(user_id: int) -> bool:
    url = f'https://top.gg/api/bots/{BOT_ID}/check?userId={user_id}'
    headers = {'Authorization': token_file['TOP_GG_TOKEN']}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return int(data.get('voted', 0)) > 0
            return True


async def is_user_on_cooldown(interaction: discord.Interaction) -> app_commands.Cooldown:
    voted = await check_query(interaction.user.id)
    return app_commands.Cooldown(1, 5.0) if voted else app_commands.Cooldown(1, 30.0)
