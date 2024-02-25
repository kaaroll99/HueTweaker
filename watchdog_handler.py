from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import bot
import discord
import datetime
import os


class FileHandler(FileSystemEventHandler):
    def __init__(self, bot, channel_id, channel_database_id):
        self.bot = bot
        self.channel_id = channel_id
        self.channel_database_id = channel_database_id

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.log'):
            self.bot.loop.create_task(self.send_file(event.src_path))

    async def send_file(self, path):
        name = os.path.basename(path)
        channel = self.bot.get_channel(self.channel_id)
        file = discord.File(path, filename=name)
        await channel.send(name, file=file)

        db_channel = self.bot.get_channel(self.channel_database_id)
        db_file = discord.File("databases/guilds.db", filename=f"{str(datetime.date.today().strftime("%Y-%m-%d"))}.db")
        await db_channel.send(file=db_file)
