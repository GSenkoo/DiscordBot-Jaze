import discord
from discord.ext import commands


class SnipeDeleteEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction : discord.Interaction):
        if (interaction.type != discord.InteractionType.component) or (not interaction.custom_id.startswith("snipedelete_")):
            return
        
        allowed_users = [int(user_id) for user_id in interaction.custom_id.removeprefix("snipedelete_").split("_")]
        if interaction.user.id not in allowed_users:
            await interaction.response.send_message("> Seul l'auteur de la commande ou l'auteur du snipe peut supprimer ce message.", ephemeral = True)
            return
        
        await interaction.message.delete()


def setup(bot):
    bot.add_cog(SnipeDeleteEvent(bot))