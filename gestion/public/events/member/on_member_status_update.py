import discord
from datetime import datetime
from discord.ext import commands


class on_member_status_update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before : discord.Member, after : discord.Member):
        if (before.status == after.status):
            return 
        # Je vérifie selon le discord.Member.status, comme ça, les membres seront tous automatiquements mise à jours automatiquement quand ils changent leurs statut (dnd, idle, online, offline). 
        # (et pas raw_status parceque il ne prendrais seulement en compte que le changement du texte)


        


    
def setup(bot):
    bot.add_cog(on_member_status_update(bot))