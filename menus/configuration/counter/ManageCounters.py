import discord
import asyncio
from utils import MyViewClass
from .functions import get_counters_main_embed
from .functions import get_counter_choices
from .functions import get_counter_embed
from .functions import get_data
from .functions import save_data
from .CounterDeleter import CounterDeleter
from .ManageCounter import ManageCounter


"""
Counter data format : 
[
    {   
        "enabled": True, 
        "name": "CounterName",
        "text": "CounterData : {ServerName}",
        "channel": channel_id_here,
        "update_frequency": "10m" (possibility : 5m, 10m, 30m, 1h)
    }
]
"""

def delete_message(message):
    async def task():
        try: await message.delete()
        except: pass
    loop = asyncio.get_event_loop()
    loop.create_task(task())


class ManageCounters(MyViewClass):
    def __init__(self, bot, ctx, counters_data):
        super().__init__(timeout = 900)
        self.bot = bot
        self.ctx = ctx
        self.counters_data = counters_data

        def update_manager_choices():
            self.children[0].options = get_counter_choices(self.counters_data)
        self.update_manager_choices = update_manager_choices
        self.update_manager_choices()

    
    @discord.ui.select(
        placeholder = "Configurer un compteur",
        options = None
    )
    async def choose_counter_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        if select.values[0] == "nope":
            await interaction.response.defer()
            return
        
        for counter_data in self.counters_data:
            if select.values[0] == "counter_" + counter_data["name"]:
                await interaction.edit(embed = await get_counter_embed(self.ctx, self.bot, counter_data), view = ManageCounter(self, counter_data))
                return
        
        await interaction.response.send_message("> Le compteur que vous avez choisi n'est plus valide.", ephemeral = True)
        

    @discord.ui.select(
        placeholder = "Configurer vos compteurs",
        options = [
            discord.SelectOption(label = "Créer un compteur", emoji = "➕", value = "create_counter"),
            discord.SelectOption(label = "Supprimer un compteur", emoji = "➖", value = "delete_counter")
        ]
    )
    async def config_counters(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        # ################### --------------------------- Créer un compteur
        if select.values[0] == "create_counter":
            await interaction.response.defer()
            
            # ----------------------------------------------- Demande d'un nom pour le nouveau compteur à créer
            ask_message = await self.ctx.send("> Quel nom souhaiterez-vous définir à votre nouveau compteur? Envoyez `cancel` pour annuler.")
            
            def response_check(message):
                return (message.author == interaction.user) and (message.channel == interaction.channel) and (message.content)
            
            try:
                response_message = await self.bot.wait_for("message", check = response_check, timeout = 60)
            except asyncio.TimeoutError:
                await self.ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                return
            finally:
                delete_message(ask_message)
            delete_message(response_message)

            # ----------------------------------------------- Traitement des données
            if response_message.content.lower() == "cancel":
                await self.ctx.send("> Action annulée.", delete_after = 3)
                return
            
            for counter_data in self.counters_data:
                if counter_data["name"] == response_message.content:
                    await self.ctx.send(f"> Action annulée, il éxiste déjà un compteur avec le nom donné.", delete_after = 3)
                    return
                
            self.counters_data.append({
                "enabled": False, 
                "name": response_message.content,
                "text": None,
                "channel": None,
                "update_frequency": "10m"
            })


            self.update_manager_choices()
            await interaction.message.edit(embed = await get_counters_main_embed(self.bot, self.ctx, self.counters_data), view = self)


        # ################### --------------------------- Supprimer un compteur
        if select.values[0] == "delete_counter":
            if not self.counters_data:
                await interaction.response.send_message("> Il n'y a pas de compteur à supprimer pour le moment.", ephemeral = True)
                return
            await interaction.edit(view = CounterDeleter(self.bot, self.ctx, self))


    @discord.ui.button(label = "Sauvegarder", style = discord.ButtonStyle.primary)
    async def save_callback(self, button, interaction : discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        for counter_data in self.counters_data:
            if not counter_data["enabled"]:
                continue
            if not counter_data["text"]:
                await interaction.response.send_message(f"> Pour le compteur **{counter_data['name']}**, vous n'avez pas fourni de texte valide.", ephemeral = True)
                return
            if not interaction.guild.get_channel(counter_data["channel"]):
                await interaction.response.send_message(f"> Pour le compteur **{counter_data['name']}**, vous n'avez pas fourni de salon valide.", ephemeral = True)
                return
            
        try:
            await save_data(self.bot, self.ctx, self.counters_data)
        except Exception as e:
            print(e)            
            await interaction.response.send_message("> Une erreur s'est produite lors de la tentative de sauvegarde, merci de réessayer.", ephemeral = True)
            return
        
        message_embed = interaction.message.embeds[0]
        message_embed.title = "Configuration des compteurs terminée"
        await interaction.edit(embed = message_embed, view = None)
        

    @discord.ui.button(style = discord.ButtonStyle.danger, emoji = "🗑")
    async def cancel_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        await interaction.edit(embed = discord.Embed(title = "Configuration annulée", color = await self.bot.get_theme(self.ctx.guild.id)), view = None)