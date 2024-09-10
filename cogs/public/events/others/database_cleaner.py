import discord
from discord.ext import commands


class database_cleaner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.bot.db.execute("DELETE FROM role_react WHERE channel_id = %s", (channel.id,))
        await self.bot.db.execute("DELETE FROM counter WHERE channel = %s", (channel.id,))


    @commands.Cog.listener()
    async def on_raw_message_delete(self, playload : discord.RawMessageDeleteEvent):
        await self.bot.db.execute("DELETE FROM role_react WHERE message_id = %s", (playload.message_id,))


def setup(bot):
    bot.add_cog(database_cleaner(bot))