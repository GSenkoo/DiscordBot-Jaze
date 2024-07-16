import discord
from datetime import datetime
from discord.ext import commands


class on_member_join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_member_join(self, member : discord.Member):

        # ----------------------------------- GHOST PING
        ghostping_channels = await self.bot.db.get_data("guild", "ghostping_channels", True, guild_id = member.guild.id)
        if ghostping_channels:
            for channel_id in ghostping_channels:
                channel = member.guild.get_channel(channel_id)
                await channel.send(member.mention, delete_after = 3)

    
def setup(bot):
    bot.add_cog(on_member_join(bot))