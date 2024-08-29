import discord

from utils import GPChecker
from utils import MyViewClass

from .functions import get_button_embed

class ManageButtonRoles(MyViewClass):
    def __init__(self, bot, ctx, choosed_value, option_name, manage_button_view):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.choosed_value = choosed_value
        self.option_name = option_name
        self.manage_button_view = manage_button_view

        self.children[1].label = f"Choisissez un {self.option_name.lower()}"


    @discord.ui.select(
        select_type = discord.ComponentType.role_select,
        placeholder = f"Choisir un rôle"
    )
    async def choose_role_select_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        role = interaction.guild.get_role(select.values[0].id)
        if not role:
            await interaction.response.send_message("> Le rôlé donné est invalide ou alors je n'y ai pas accès.", ephemeral = True)
            return
        
        gp_checker = GPChecker(self.ctx, self.bot)
        check = await gp_checker.we_can_add_role(role)
        if check != True:
            await interaction.response.send_message(check, ephemeral = True)
            return
        
        options_translated = {"required_role": "rôle requis", "ignored_role": "rôle ignoré", "role": "rôle du bouton"}
        if self.choosed_value != "required_role":
            if (self.manage_button_view.button_data["required_role"] if self.manage_button_view.button_data["required_role"] else "nah") == select.values[0].id:
                await interaction.response.send_message(f"> Le {options_translated[self.choosed_value]} ne peut pas être le même que le {options_translated['required_role']}.", ephemeral = True)
                return
        else:
            if (self.manage_button_view.button_data["required_role"] if self.manage_button_view.button_data["required_role"] else "nah") in [self.manage_button_view.button_data["role"], self.manage_button_view.button_data["ignored_role"]]:
                await interaction.response.send_message(f"> Le {options_translated[self.choosed_value]} ne peut pas être le même que le {options_translated['required_role']}.", ephemeral = True)
                return
        
        self.manage_button_view.button_data[self.choosed_value] = select.values[0].id
        await interaction.edit(embed = await get_button_embed(self.manage_button_view.button_data, self.ctx, self.bot), view = self.manage_button_view)
        

    @discord.ui.button(label = None, style = discord.ButtonStyle.primary, disabled = True)
    async def button_callback(self, button, interaction):
        pass


    @discord.ui.button(label = "Retirer", emoji = "❌", style = discord.ButtonStyle.danger)
    async def remove_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        self.manage_button_view.button_data[self.choosed_value] = None
        await interaction.edit(embed = await get_button_embed(self.manage_button_view.button_data, self.ctx, self.bot), view = self.manage_button_view)
        

    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
    async def comeback_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        await interaction.edit(view = self.manage_button_view)