import discord
from datetime import datetime
from discord.ext import commands


class on_interaction_giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction : discord.Interaction):
        if interaction.custom_id != "giveaway":
            return
        
        await interaction.response.send_message("> Fonctionnel.", ephemeral = True)


def setup(bot):
    bot.add_cog(on_interaction_giveaway(bot))