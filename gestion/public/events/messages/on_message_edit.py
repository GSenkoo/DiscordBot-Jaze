import discord
from discord.ext import commands
from datetime import datetime


class on_message_edit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.guild:
            return
        if (before.content == after.content) or (after.author == after.guild.me):
            return

        await self.bot.db.set_data("snipe_edit", "author_id", after.author.id, guild_id = after.guild.id, channel_id = after.channel.id)
        await self.bot.db.set_data("snipe_edit", "author_name", after.author.display_name, guild_id = after.guild.id, channel_id = after.channel.id)
        await self.bot.db.set_data("snipe_edit", "author_avatar", after.author.avatar.url if after.author.avatar else None, guild_id = after.guild.id, channel_id = after.channel.id)
        await self.bot.db.set_data("snipe_edit", "message_content_before", before.content if len(before.content) <= 1024 else before.content[:1021] + "...", guild_id = after.guild.id, channel_id = after.channel.id)
        await self.bot.db.set_data("snipe_edit", "message_content_after", after.content if len(after.content) <= 1024 else after.content[:1021] + "...", guild_id = after.guild.id, channel_id = after.channel.id)
        await self.bot.db.set_data("snipe_edit", "message_datetime", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), guild_id = after.guild.id, channel_id = after.channel.id)


def setup(bot):
    bot.add_cog(on_message_edit(bot))