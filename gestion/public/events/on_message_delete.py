import discord
from datetime import datetime
from discord.ext import commands
from utils.Database import Database


class on_message_delete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message : discord.Message):
        database = Database()
        await database.connect()
        try:
            await database.set_data("snipe", "author_id", message.author.id, False, guild_id = message.guild.id, channel_id = message.channel.id)
            await database.set_data("snipe", "author_name", message.author.display_name, False, guild_id = message.guild.id, channel_id = message.channel.id)
            await database.set_data("snipe", "author_avatar", message.author.display_avatar, False, guild_id = message.guild.id, channel_id = message.channel.id)
            await database.set_data("snipe", "message_content", message.content, False, guild_id = message.guild.id, channel_id = message.channel.id)
            await database.set_data("snipe", "message_datetime", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), True, guild_id = message.guild.id, channel_id = message.channel.id)
        finally: await database.disconnect()
    
def setup(bot):
    bot.add_cog(on_message_delete(bot))