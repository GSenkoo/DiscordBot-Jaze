import discord
from utils import MyViewClass
from .functions import get_suggestion_settings_embed

class ChooseModeratorRoles(MyViewClass):
    def __init__(self, bot, ctx, manage_suggestions_view):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.manage_suggestions_view = manage_suggestions_view

        self.children[0].max_values = 15 - len(manage_suggestions_view.suggestion_data["moderator_roles"])

    @discord.ui.select(
        placeholder = "Choisissez un rôle",
        select_type = discord.ComponentType.role_select,
        max_values = 1
    )
    async def select_choose_role_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send("> Vous n'êtes pas autorisés à intéragir avec ceci.")
            return
        
        for role in select.values:
            if (role.id in self.manage_suggestions_view.suggestion_data["moderator_roles"]) or (len(self.manage_suggestions_view.suggestion_data["moderator_roles"]) >= 15):
                continue
            self.manage_suggestions_view.suggestion_data["moderator_roles"].append(role.id)

        await interaction.edit(embed = await get_suggestion_settings_embed(self.bot, self.ctx, self.manage_suggestions_view.suggestion_data), view = self.manage_suggestions_view)
        
    @discord.ui.button(label = "Choisissez un rôle", style = discord.ButtonStyle.primary, disabled = True)
    async def button_callback(self, button, interaction):
        pass
