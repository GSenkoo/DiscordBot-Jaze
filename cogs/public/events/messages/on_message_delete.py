import discord
from datetime import datetime
from discord.ext import commands


class on_message_delete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message : discord.Message):
        if message.author == message.guild.me:
            return

        await self.bot.db.set_data("snipe", "author_id", message.author.id, guild_id = message.guild.id, channel_id = message.channel.id)
        await self.bot.db.set_data("snipe", "author_name", message.author.display_name, guild_id = message.guild.id, channel_id = message.channel.id)
        await self.bot.db.set_data("snipe", "author_avatar", message.author.display_avatar, guild_id = message.guild.id, channel_id = message.channel.id)
        await self.bot.db.set_data("snipe", "message_content", message.content if len(message.content) <= 2000 else message.content[:1997] + "...", guild_id = message.guild.id, channel_id = message.channel.id)
        await self.bot.db.set_data("snipe", "message_datetime", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), guild_id = message.guild.id, channel_id = message.channel.id)

def setup(bot):
    bot.add_cog(on_message_delete(bot))