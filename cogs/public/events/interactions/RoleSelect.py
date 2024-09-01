import discord
from discord.ext import commands
from utils import GPChecker


class RoleSelectInteractionEvent(commands.Cog):
    """
    Lors de la confirmation de la configuration d'un sélécteur, le custom_id du sélécteur 
    est sous forme : 
        - "selector_roles_True"
        -                 ^^^^
        -                 True/False Envoi d'une réponse de confirmation à l'utilisateur
    
    les options de ce même sélécteur suivent tous le format suivant :
        - "option_1241484256182669402_1265398039066054676_1276176305376722984"
        -                  ^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^
        -                  Rôle à ajouter      Rôle obligatoire    Rôle interdit

    """
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_interaction(self, interaction : discord.Interaction):
        if (interaction.type != discord.InteractionType.component) or (not interaction.custom_id.startswith("selector_roles_")):
            return
        
        # ------------------------------------ Get the select instance
        select = None
        for row in interaction.message.components:
            for component in row.children:
                if component.custom_id == interaction.custom_id:
                    select = component
                    break
        assert select
        
        # ------------------------------------ Obtention/Initialisation des variables nécessaire
        select_send_response = bool(interaction.custom_id.split("_")[2])
        select_choosed_values = interaction.data["values"]
        select_not_choosed_values = [option.value for option in select.options if option.value not in select_choosed_values]
        select_choices_max_count = select.max_values

        member_roles_ids = [role.id for role in interaction.user.roles] if interaction.user.roles else []

        # ------------------------------------ Traitement des données
        roles_to_add = []
        roles_to_del = []

        for choosed_value in select_choosed_values:
            role = interaction.guild.get_role(int(choosed_value.split("_")[1]))
            if (not role) or (role.id in member_roles_ids):
                continue
            roles_to_add.append(role)
        
        for not_choosed_value in select_not_choosed_values:
            role = interaction.guild.get_role(int(not_choosed_value.split("_")[1]))
            if (not role) or (role.id not in member_roles_ids):
                continue
            roles_to_del.append(role)

        if roles_to_add:
            await interaction.user.add_roles(*roles_to_add, reason = "Role-Select")
        if roles_to_del:
            await interaction.user.remove_roles(*roles_to_del, reason = "Role-Select")

        roles_to_add = [role.mention for role in roles_to_add]
        roles_to_del = [role.mention for role in roles_to_del]

        if (roles_to_add or roles_to_del) and select_send_response:
            await interaction.respond(
                "> Vos rôles ont correctement été mis à jour.\n"
                + ((f"\nVous avez reçu {len(roles_to_add)} rôle{'s' if len(roles_to_add) > 1 else ''} (" + ", ".join(roles_to_add) + ")") if roles_to_add else "")
                + ((f"\nVous avez été dépossédé de {len(roles_to_del)} rôle{'s' if len(roles_to_del) > 1 else ''} (" + ", ".join(roles_to_del) + ")") if roles_to_del else ""),
                ephemeral = True
            )
        else:
            await interaction.response.defer()


def setup(bot):
    bot.add_cog(RoleSelectInteractionEvent(bot))