import discord
from discord.ext import commands
from utils.Database import Database

class MartialBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.colors_save = {}
    
    async def get_theme(self, guild_id : int):
        if guild_id in self.colors_save.keys():
            return self.colors_save[guild_id]
        
        database = Database()
        try:
            await database.connect()
            theme = await database.get_data(table = "guild", column = "theme", guild_id = guild_id)
        finally: await database.disconnect()
        self.colors_save[guild_id] = int(theme)

        return int(theme)