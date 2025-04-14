import aiohttp
import logging
import asyncio
from utils.data_loader import load_json, load_yml

token_file = load_yml('assets/token.yml')


async def post_data(url: str, headers: dict, data: dict, message: str = "server count") -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    logging.info(f'Successfully posted {message} to {url}')
                    return {"status": response.status, "success": True}
                else:
                    logging.warning(f'Failed to post {message} to {url}: {response.status} {response.reason}')
                    return {"status": response.status, "success": False, "reason": response.reason}
    except asyncio.TimeoutError:
        logging.error(f"Request to {url} timed out")
        return {"status": None, "success": False, "reason": "Timeout"}
    except Exception as e:
        logging.error(f'Error posting {message} to {url}: {e}', exc_info=True)
        return {"status": None, "success": False, "reason": str(e)}


async def api_request(server_count: int, user_count: int) -> None:
    # Update bot stats top.gg
        url = f'https://top.gg/api/bots/1209187999934578738/stats'
        headers = {
            'Authorization': token_file['TOP_GG_TOKEN'],
            'Content-Type': 'application/json'
        }
        data = {
            'server_count': server_count,
            'shard_count': 2
        }
        await post_data(url, headers, data, message="stats to Top.gg")
        
        # Update bot stats discordlist.gg
        url = f'https://api.discordlist.gg/v0/bots/1209187999934578738/guilds'
        headers = {
            'Authorization': f"Bearer {token_file['DISCORDLIST_GG_TOKEN']}",
            'Content-Type': 'application/json; charset=utf-8'
        }
        data = {
            'count': server_count
        }
        await post_data(url, headers, data, message="stats to discordlist.gg")
        
        # Update bot stats discordbotlist.com
        url = "https://discordbotlist.com/api/v1/bots/1209187999934578738/stats"
        headers = {
            "Content-Type": "application/json",
            "Authorization": token_file['DISCORDBOTLIST_TOKEN']
        }
        data = {
            "users": user_count, 
            "guilds": server_count
        }
        await post_data(url, headers, data, message="stats to discordbotlist.com")

        # Update commands list discordbotlist.com
        url = f"https://discordbotlist.com/api/v1/bots/1209187999934578738/commands"
        json_payload = load_json("assets/commands_list.json")
        headers = {
            "Authorization": token_file['DISCORDBOTLIST_TOKEN'],
            "Content-Type": "application/json"
        }
        await post_data(url, headers, json_payload, message="command list")
    