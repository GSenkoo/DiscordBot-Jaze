import discord
import asyncio
from utils import MyViewClass
from utils import Searcher
from utils import Tools
from .functions import get_counter_embed
from .functions import get_counters_main_embed


def delete_message(message):
    async def task():
        try: await message.delete()
        except: pass
    loop = asyncio.get_event_loop()
    loop.create_task(task())


class ManageCounter(MyViewClass):
    def __init__(self, manage_counters_view, counter_data):
        super().__init__(timeout = 300)
        self.bot = manage_counters_view.bot
        self.ctx = manage_counters_view.ctx
        self.manage_counters_view = manage_counters_view
        self.counter_data = counter_data


    @discord.ui.select(
        placeholder = "Modifier le compteur",
        options = [
            discord.SelectOption(label = "Statut", emoji = "❔", value = "enabled"),
            discord.SelectOption(label = "Texte", emoji = "✏", value = "text"),
            discord.SelectOption(label = "Salon", emoji = "📌", value = "channel"),
            discord.SelectOption(label = "Fréquence des mises à jours", emoji = "🔄", value = "update_frequency"),
        ]
    )
    async def edit_counter_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        

        if select.values[0] == "enabled":
            self.counter_data["enabled"] = not self.counter_data["enabled"]
            await interaction.edit(embed = await get_counter_embed(self.ctx, self.bot, self.counter_data))
        

        if select.values[0] in ["text", "channel"]:
            option_name = [option.label.lower() for option in select.options if option.value == select.values[0]][0]
            ask_message = await self.ctx.send(f"> Quel **{option_name}** souhaitez-vous définir à votre compteur?")
            await interaction.response.defer()

            def response_check(message):
                return (interaction.user == message.author) and (message.channel == interaction.channel) and (message.content)
            
            try:
                response_message = await self.bot.wait_for("message", check = response_check, timeout = 60)
            except asyncio.TimeoutError:
                await self.ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                return
            finally:
                delete_message(ask_message)
            
            delete_message(response_message)

            if select.values[0] == "text":
                # ------------------------------- Vérifications
                if len(response_message.content) > 100:
                    await self.ctx.send("> Vous devez fournir un texte de compteur de moins de 100 caractères.", delete_after = 3)
                    return
                
                tools = Tools(self.bot)
                guild_vars_list = tools.get_guild_vars_list()

                if not any(var in response_message.content for var in guild_vars_list if "count" in var.lower()):
                    await self.ctx.send("> Vous devez mettre au moins une variable pouvant être énumérer dans le texte du compteur.", delete_after = 3)
                    return

                # ------------------------------- Définition
                self.counter_data["text"] = response_message.content

            if select.values[0] == "channel":
                searcher = Searcher(self.bot, self.ctx)
                channel = await searcher.search_channel(response_message.content)
                
                # ------------------------------- Vérifications
                if not channel:
                    await self.ctx.send("> Le salon donné est invalide.", delete_after = 3)
                    return
                if not channel.type == discord.ChannelType.voice:
                    await self.ctx.send("> Le salon donné doit être un salon vocal.", delete_after = 3)
                    return
                for counter_data in self.manage_counters_view.counters_data:
                    if counter_data["name"] == self.counter_data["name"]:
                        continue
                    if counter_data["channel"] == channel.id:
                        await self.ctx.send("> Le salon donné est déjà utilisé pour un autre compteur.", delete_after = 3)
                        return

                # ------------------------------- Définition
                self.counter_data["channel"] = channel.id

            await interaction.message.edit(embed = await get_counter_embed(self.ctx, self.bot, self.counter_data))


        if select.values[0] == "update_frequency":
            async def choose_frequency_callback(interaction):
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                self.counter_data["update_frequency"] = interaction.custom_id
                await interaction.edit(embed = await get_counter_embed(self.ctx, self.bot, self.counter_data), view = self)

            view = MyViewClass()
            for custom_id in ["5m", "10m", "30m", "1h", "3h"]:
                button = discord.ui.Button(label = custom_id, custom_id = custom_id, style = discord.ButtonStyle.primary)
                button.callback = choose_frequency_callback
                view.add_item(button)
            
            await interaction.edit(view = view)


    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
    async def comeback_button(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        for index, counter_data in enumerate(self.manage_counters_view.counters_data):
            if counter_data["name"] == self.counter_data["name"]:
                self.manage_counters_view.counters_data[index] = self.counter_data
                break

        self.manage_counters_view.update_manager_choices()
        await interaction.edit(embed = await get_counters_main_embed(self.bot, self.ctx, self.manage_counters_view.counters_data), view = self.manage_counters_view)