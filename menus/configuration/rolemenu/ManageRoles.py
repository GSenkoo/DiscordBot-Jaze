import discord

from utils import GPChecker
from utils import MyViewClass


class ManageRoles(MyViewClass):
    def __init__(self, bot, ctx, choosed_value, option_name, previous_view, get_embed_func):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.choosed_value = choosed_value
        self.option_name = option_name
        self.previous_view = previous_view
        self.get_embed_func = get_embed_func

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
        
        if (not hasattr(self.previous_view, "manage_selector_view")) and (self.choosed_value != "role"):
            if (self.choosed_value == "ignored_role" and self.previous_view.data["required_role"] == select.values[0].id) or (self.choosed_value == "required_role" and self.previous_view.data["ignored_role"] == select.values[0].id):
                await interaction.response.send_message("> Le rôle requis et le rôle ignoré ne peuvent pas être identiques.", ephemeral = True)
                return
        
        if hasattr(self.previous_view, "manage_selector_view"): # Pour savoir si nous sommes actuellements entrain de gérer une option de sélécteur
            for index, option_data in enumerate(self.previous_view.manage_selector_view.selector_data["options_data"]):
                if index == self.previous_view.option_index:
                    continue
                if option_data["role"] == role.id:
                    await interaction.response.send_message(f"> Le rôle {role.mention} est déjà attribué dans une autre option du sélécteur.", ephemeral = True)
                    return

        self.previous_view.data[self.choosed_value] = select.values[0].id
        await interaction.edit(embed = await self.get_embed_func(self.previous_view.data, self.ctx, self.bot), view = self.previous_view)
        

    @discord.ui.button(label = None, style = discord.ButtonStyle.primary, disabled = True)
    async def button_callback(self, button, interaction):
        pass


    @discord.ui.button(label = "Retirer", style = discord.ButtonStyle.danger)
    async def remove_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        self.previous_view.data[self.choosed_value] = None
        await interaction.edit(embed = await self.get_embed_func(self.previous_view.data, self.ctx, self.bot), view = self.previous_view)
        

    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
    async def comeback_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        await interaction.edit(view = self.previous_view)