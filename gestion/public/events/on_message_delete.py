import discord
from datetime import datetime
from discord.ext import commands


class on_message_delete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message : discord.Message):
        await self.bot.db.set_data("snipe", "author_id", message.author.id, guild_id = message.guild.id, channel_id = message.channel.id)
        await self.bot.db.set_data("snipe", "author_name", message.author.display_name, guild_id = message.guild.id, channel_id = message.channel.id)
        await self.bot.db.set_data("snipe", "author_avatar", message.author.display_avatar, guild_id = message.guild.id, channel_id = message.channel.id)
        await self.bot.db.set_data("snipe", "message_content", message.content, guild_id = message.guild.id, channel_id = message.channel.id)
        await self.bot.db.set_data("snipe", "message_datetime", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), guild_id = message.guild.id, channel_id = message.channel.id)

def setup(bot):
    bot.add_cog(on_message_delete(bot))