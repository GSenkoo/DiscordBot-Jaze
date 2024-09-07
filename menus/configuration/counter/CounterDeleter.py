import discord
from .functions import get_counters_main_embed
from .functions import get_counter_choices
from utils import MyViewClass


class CounterDeleter(MyViewClass):
    def __init__(self, bot, ctx, manage_counters_view):
        super().__init__(timeout = 180)
        self.bot = bot
        self.ctx = ctx
        self.manage_counters_view = manage_counters_view

        self.children[0].options = get_counter_choices(manage_counters_view.counters_data)


    @discord.ui.select(
        placeholder = "Choisir une option",
        options = None
    )
    async def choose_option_to_del_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        for counter_data in self.manage_counters_view.counters_data:
            if counter_data["name"] == select.values[0].removeprefix("counter_"):
                self.manage_counters_view.counters_data.remove(counter_data)
                self.manage_counters_view.update_manager_choices()
                await interaction.edit(embed = await get_counters_main_embed(self.bot, self.ctx, self.manage_counters_view.counters_data), view = self.manage_counters_view)
                return
            
        await interaction.response.send_message("> Le compteur que vous avez choisi n'est plus disponible.", ephemeral = True)

    
    @discord.ui.button(label = "Choisissez un compteur", style = discord.ButtonStyle.primary, disabled = True)
    async def choose_counter_callback(self, select, interaction):
        pass


    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
    async def comeback_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        await interaction.edit(view = self.manage_counters_view)