import discord
from utils import MyViewClass
from .functions import get_suggestion_settings_embed

class ChooseModeratorRolesToRemove(MyViewClass):
    def __init__(self, ctx, manage_suggestions_view):
        super().__init__()
        self.ctx = ctx
        self.manage_suggestions_view = manage_suggestions_view

        roles_ids_to_name = {}
        for role_id in self.manage_suggestions_view.suggestion_data["moderator_roles"]:
            role = self.ctx.guild.get_role(role_id)
            if role:
                roles_ids_to_name[str(role_id)] = "@" +  role.name
            else:
                roles_ids_to_name[str(role_id)] = "@RôleIntrouvable"

        self.children[0].max_values = len(roles_ids_to_name)
        self.children[0].options = [
            discord.SelectOption(
                label = role_name,
                description = f"Identifiant : {role_id}",
                value = role_id
            ) for role_id, role_name in roles_ids_to_name.items()
        ]


    @discord.ui.select(
        placeholder = "Choisissez un rôle",
        max_values = 1,
        options = None,
    )
    async def select_remove_role_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send("> Vous n'êtes pas autorisés à intéragir avec ceci.")
            return
        
        for role_id in select.values:
            if (int(role_id) not in self.manage_suggestions_view.suggestion_data["moderator_roles"]):
                continue
            self.manage_suggestions_view.suggestion_data["moderator_roles"].remove(int(role_id))
        
        await interaction.edit(view = self.manage_suggestions_view, embed = await get_suggestion_settings_embed(self.manage_suggestions_view.bot, self.ctx, self.manage_suggestions_view.suggestion_data))
    
    @discord.ui.button(label = "Choisissez un rôle", style = discord.ButtonStyle.primary, disabled = True)
    async def button_info_callback(self, button, interaction):
        pass
