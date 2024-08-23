import discord
from utils.Tools import Tools
from discord.ext import commands


class on_member_remove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_member_remove(self, member : discord.Member):
        
        # ----------------------------------- Leave message
        leaves_enabled = await self.bot.db.get_data("leaves", "enabled", guild_id = member.guild.id)
        if leaves_enabled:
            tools = Tools(self.bot)
            await tools.send_leave_message(member.guild, member)


def setup(bot):
    bot.add_cog(on_member_remove(bot))