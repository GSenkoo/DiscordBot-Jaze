import discord
from discord.ext import commands


class RoleButtonInteractionEvent(commands.Cog):
    """
    Lors de la confirmation de la configuration d'un bouton dans la commande +rolemenu, le bot
    a utilisé le format suivant pour la valeur du bouton afin de pouvoir reconnaitre les 
    paramètres du bouton :

        - "role_button_1241484256182669402_1265398039066054676_1276176305376722984_True"
        -              ^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^ ^^^^
        -              Rôle à ajouter      Rôle obligatoire    Rôle interdit       True/False Envoi de réponse de confirmation
    """
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_interaction(self, interaction : discord.Interaction):
        if (interaction.type != discord.InteractionType.component) or (not interaction.custom_id.startswith("role_button_")):
            return
        
        datas = interaction.custom_id.removeprefix("role_button_").split("_")
        
        assert len(datas) == 4
        assert all(data.isdigit() for data in datas[:-1])
        assert datas[3] in ("True", "False")

        datas = [int(data) for data in datas[:-1]] + [datas[3]]
        
        role = interaction.guild.get_role(datas[0])
        role_required = interaction.guild.get_role(datas[1]) if datas[1] else None
        role_ignored = interaction.guild.get_role(datas[2]) if datas[2] else None
        send_response = bool(datas[3])
        member_roles_ids = [role.id for role in interaction.user.roles] if interaction.user.roles else []

        if not role:
            await interaction.response.send_message(f"> Le rôle <@&{role.mention}> n'éxiste plus ou ne m'est plus accessible.", ephemeral = True)
            return
        
        # --------------------------- Vérifications des rôles requis et rôles ignorés.
        if (role_required) and (role_required.id not in member_roles_ids):
            await interaction.response.send_message(f"> Vous devez avoir le rôle {role_required.mention}.", ephemeral = True)
            return
        if (role_ignored) and (role_ignored.id in member_roles_ids):
            await interaction.response.send_message(f"> Vous ne devez pas avoir le rôle {role_ignored.mention}.", ephemeral = True)
            return
        
        # --------------------------- Ajout/Retrait du rôle
        if role.id not in member_roles_ids:
            await interaction.user.add_roles(role, reason = "Role-Button")
            if send_response:
                await interaction.response.send_message(f"> Le rôle {role.mention} vous a été ajouté.", ephemeral = True)
                return
        else:
            await interaction.user.remove_roles(role, reason = "Role-Button")
            if send_response:
                await interaction.response.send_message(f"> Le rôle {role.mention} vous a été retiré.", ephemeral = True)
                return
        
        await interaction.response.defer()


def setup(bot):
    bot.add_cog(RoleButtonInteractionEvent(bot))