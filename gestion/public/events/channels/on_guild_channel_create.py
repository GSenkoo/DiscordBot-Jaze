import discord
import asyncio
from discord.ext import commands


class on_guild_channel_create(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        
        # ----------------------------------- Captcha auto configuration
        if type(channel) == discord.CategoryChannel:
            return

        captcha_enabled = await self.bot.db.get_data("captcha", "enabled", guild_id = channel.guild.id)
        if not captcha_enabled:
            return
        
        auto_config = await self.bot.db.get_data("captcha", "auto_config", guild_id = channel.guild.id)
        if not auto_config:
            return
            
        non_verified_role_id = await self.bot.db.get_data("captcha", "non_verified_role", guild_id = channel.guild.id)
        non_verified_role = channel.guild.get_role(non_verified_role_id)
        if not non_verified_role:
            return
        
        non_verified_role_overwrites = channel.overwrites_for(non_verified_role)
        if non_verified_role_overwrites.view_channel:
            return
        
        non_verified_role_overwrites.view_channel = False
        await channel.set_permissions(non_verified_role, overwrite = non_verified_role_overwrites)


def setup(bot):
    bot.add_cog(on_guild_channel_create(bot))