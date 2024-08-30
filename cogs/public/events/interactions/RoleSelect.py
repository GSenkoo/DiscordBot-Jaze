import discord
from discord.ext import commands


class RoleSelectInteractionEvent(commands.Cog):
    """
    Lors de la confirmation de la configuration d'un sélécteur, le custom_id du sélécteur 
    est "selector_role", les options du sélécteurs suivent tous un format définis à la 
    configuration du sélécteur :

        - "role_button_1241484256182669402_1265398039066054676_1276176305376722984"
        -              ^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^
        -              Rôle à ajouter      Rôle obligatoire    Rôle interdit

    Parcontre, les rôles 
    """
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_interaction(self, interaction : discord.Interaction):
        if (interaction.type != discord.InteractionType.component) or (not interaction.custom_id.startswith("role_button_")):
            return


def setup(bot):
    bot.add_cog(RoleSelectInteractionEvent(bot))