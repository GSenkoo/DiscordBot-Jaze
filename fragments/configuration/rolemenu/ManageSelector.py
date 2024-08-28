import discord
from utils import MyViewClass
from .functions import get_selector_embed
from .functions import get_formated_selector_options
from .functions import get_main_embed


class ManageSelector(MyViewClass):
    def __init__(self, bot, ctx, selector_data, manage_role_menu_view):
        super().__init__(timeout = 180)
        self.bot = bot
        self.ctx = ctx
        self.selector_data = selector_data
        self.manage_role_menu_view = manage_role_menu_view

        def update_displayed_options():
            self.children[0].options = get_formated_selector_options(self.selector_data["options_data"])
        self.update_displayed_options = update_displayed_options
        self.update_displayed_options()


    @discord.ui.select(
        placeholder = "Choisir une option à modifier",
        options = None
    )
    async def choose_option_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        if select.values[0] == "nope":
            await interaction.response.defer()
            return
        
        


    @discord.ui.select(
        placeholder = "Modifier le sélécteur",
        options = [
            discord.SelectOption(label = "Texte", value = "placeholder")
        ]
    )
    async def edit_selector_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return


    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
    async def back_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        for index, selector_previous_data in enumerate(self.manage_role_menu_view.data["selectors"]):
            if selector_previous_data["id"] == self.selector_data["id"]:
                self.manage_role_menu_view.data["selectors"][index] = self.selector_data.copy()
                break
        self.manage_role_menu_view.update_select()
        await interaction.edit(embed = await get_main_embed(self.bot, self.ctx, self.manage_role_menu_view.data), view = self.manage_role_menu_view)