import discord
from discord.ext import commands


class on_raw_reaction_add(commands.Cog):
    def __init__(self, bot):
        self.bot : commands.AutoShardedBot = bot

    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, playload : discord.RawReactionActionEvent):
        if not playload.guild_id:
            return
        
        member = playload.member
        if not member:
            guild = self.bot.get_guild(playload.guild_id)
            if not guild:
                return
            member = guild.get_member(playload.user_id)
            if not member:
                return
    
        role_react_data_sql = await self.bot.db.execute(f"SELECT * FROM role_react WHERE message_id = %s AND emoji = %s", (playload.message_id, str(playload.emoji),), fetch = True)
        if not role_react_data_sql:
            return
        
        reaction_role_table_columns = await self.bot.db.get_table_columns("role_react")
        role_react_data = dict(zip(reaction_role_table_columns, role_react_data_sql[0]))
        role = member.guild.get_role(role_react_data["role"])

        if not role:
            return
        if role.id in [member_role.id for member_role in member.roles]:
            return

        try: await member.add_roles(role, reason = "React-Role")
        except: pass


def setup(bot):
    bot.add_cog(on_raw_reaction_add(bot))