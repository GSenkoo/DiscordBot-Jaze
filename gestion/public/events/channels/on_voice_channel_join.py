import discord
from datetime import datetime
from discord.ext import commands


class on_channel_join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_channel_update(self, before, after):
        if (before.members == after.members) or (type(after) != discord.VoiceChannel):
            return

        blvoc_users = await self.bot.db.get_data("guild", "blvoc_users", True, guild_id = after.guild.id)
        for member in after.members:
            if member.id in blvoc_users:
                await member.move_to(None, reason = f"Membre blvoc. Pour retirer le blvoc utilisez <prefix>blvoc del @{member.display_name}")



def setup(bot):
    bot.add_cog(on_channel_join(bot))