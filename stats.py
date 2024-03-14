from config import bot

top_guild_info = {'name': '', 'id': '', 'member_count': 0}

with open('stats.txt', 'w') as file:
    for guild in bot.guilds:
        if guild.member_count > top_guild_info['member_count']:
            top_guild_info['name'] = guild.name
            top_guild_info['id'] = guild.id
            top_guild_info['member_count'] = guild.member_count

        file.write(f"{guild.name};{guild.id};{guild.member_count}\n")

# Zapisz informacje o topowym serwerze do pliku
with open('stats.txt', 'a') as file:
    file.write(f"\nTop guild: {top_guild_info['name']}; {top_guild_info['id']}; {top_guild_info['member_count']}")
