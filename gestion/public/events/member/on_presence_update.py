import discord
import json
from discord.ext import commands


class on_presence_update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_presence_update(self, before : discord.Member, after : discord.Member):
        if not self.bot.db:
            return
        
        soutien_datas = await self.bot.db.execute(f"SELECT * FROM soutien WHERE guild_id = {after.guild.id}", fetch = True)
        if not soutien_datas:
            return

        soutien_data = dict(set(zip(await self.bot.db.get_table_columns("soutien"), soutien_datas[0])))
        if not soutien_data["enabled"]:
            return
        
        soutien_role = after.guild.get_role(soutien_data["role"])
        if not soutien_role:
            return
        
        add_role = False
        if soutien_data["strict"]:
            if str(after.activity) in soutien_data["status"]:
                add_role = True
        else:
            for status in json.loads(soutien_data["status"]):
                if status.lower() in str(after.activity).lower():
                    add_role = True
        
        member_role_ids = [role.id for role in after.roles] if after.roles else []

        if (add_role) and (soutien_role.id not in member_role_ids):
            try: await after.add_roles(soutien_role, reason = "Rôle soutien")
            except: pass
        if (not add_role) and (soutien_role.id in member_role_ids):
            try: await after.remove_roles(soutien_role, reason = "Rôle soutien")
            except: pass
    
def setup(bot):
    bot.add_cog(on_presence_update(bot))