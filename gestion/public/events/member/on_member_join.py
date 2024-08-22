import discord
import asyncio
from utils.Tools import Tools
from datetime import datetime
from discord.ext import commands


class on_member_join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_member_join(self, member : discord.Member):

        # ----------------------------------- GHOST PING
        async def send_ghost_ping():
            ghostping_channels = await self.bot.db.get_data("guild", "ghostping_channels", True, guild_id = member.guild.id)
            if ghostping_channels:
                for channel_id in ghostping_channels:
                    channel = member.guild.get_channel(channel_id)
                    await channel.send(member.mention, delete_after = 3)

        # ----------------------------------- JOIN ROLES
        async def add_join_roles():
            join_roles = await self.bot.db.get_data("guild", "join_roles", True, guild_id = member.guild.id)
            if join_roles:
                roles = []
                for role_id in join_roles:
                    role = member.guild.get_role(role_id)
                    if role: roles.append(role)
                
                await member.add_roles(*roles, reason = "Rôle(s) d'arrivées")

        # ----------------------------------- CAPTCHA ROLE
        async def add_captcha_role():
            captcha_enabled = await self.bot.db.get_data("captcha", "enabled", guild_id = member.guild.id)
            if captcha_enabled:
                non_verified_role_id = await self.bot.db.get_data("captcha", "non_verified_role", guild_id = member.guild.id)
                non_verified_role = member.guild.get_role(non_verified_role_id)

                if non_verified_role:
                    await member.add_roles(non_verified_role, reason = "Rôle des utilisateurs non vérifiés")

        # ----------------------------------- JOIN MESSAGE
        async def send_join_message():
            tools = Tools(self.bot)
            
            joins_message_enabled = await self.bot.db.get_data("joins", "enabled", guild_id = member.guild.id)
            if not joins_message_enabled:
                return
            
            captcha_enabled = await self.bot.db.get_data("captcha", "enabled", guild_id = member.guild.id)
            if captcha_enabled:
                send_after_captcha = await self.bot.db.get_data("joins", "send_after_captcha", guild_id = member.guild.id)
                if send_after_captcha:
                    return
            
            await tools.send_join_message(member.guild, member)

        tasks = [send_ghost_ping(), add_join_roles(), add_captcha_role(), send_join_message()]
        await asyncio.gather(*tasks)

    
def setup(bot):
    bot.add_cog(on_member_join(bot))