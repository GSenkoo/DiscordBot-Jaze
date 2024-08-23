import discord
from discord.ext import commands


class on_reaction_add(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction : discord.Reaction, user : discord.User):
        if not reaction.message.guild:
            return
        
        react_role_data_sql = await self.bot.db.execute(f"SELECT * FROM role_react WHERE guild_id = {reaction.message.guild.id} AND channel_id = {reaction.message.channel.id} AND message_id = {reaction.message.id} AND emoji = {reaction.emoji}")
        if not react_role_data_sql:
            return
        
        reaction_role_table_columns = await self.bot.db.get_table_columns("react_role")
        react_role_data = dict(set(zip(reaction_role_table_columns, react_role_data_sql)))

        role = reaction.message.guild.get_role(react_role_data["role"])
        if not role:
            return
        
        member = reaction.message.guild.get_member(user.id)
        if not member: # normalement, cette condition ne sera jamais vrai
            return
        
        try: await member.add_roles(role, reason = "React-Role")
        except: pass


def setup(bot):
    bot.add_cog(on_reaction_add(bot))