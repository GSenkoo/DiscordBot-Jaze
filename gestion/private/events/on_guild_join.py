import discord
from discord.ext import commands
from utils.PermissionsManager import PermissionsManager


class on_guild_join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        permission_manager = PermissionsManager()
        await permission_manager.initialize_guild_perms(guild.id)
    
def setup(bot):
    bot.add_cog(on_guild_join(bot))