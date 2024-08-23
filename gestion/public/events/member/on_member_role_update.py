import discord
from discord.ext import commands


class on_member_role_update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before : discord.Member, after : discord.Member):
        if (before.roles == after.roles) or (not after.roles):
            return
        
        # -------------------------- For BLRANK 
        blrank_users = await self.bot.db.get_data("guild", "blrank_users", True, guild_id = after.guild.id)
        noderank_roles = await self.bot.db.get_data("guild", "noderank_roles", True, guild_id = after.guild.id)
        

        if after.id in blrank_users:
            role_to_remove = [role for role in after.roles if (role.is_assignable()) and (role.id not in noderank_roles) and (role.position < after.guild.me.top_role.position)]
            if role_to_remove:
                await after.remove_roles(*role_to_remove, reason = f"Membre blrank. Pour retirer le blrank utilisez <prefix>blrank del @{after.display_name}")

def setup(bot):
    bot.add_cog(on_member_role_update(bot))