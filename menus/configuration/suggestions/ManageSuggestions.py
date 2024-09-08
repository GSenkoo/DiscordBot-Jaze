import discord
import asyncio
import json

from utils import MyViewClass
from utils import Searcher
from utils import Tools

from .ChooseModeratorRoles import ChooseModeratorRoles
from .ChooseModeratorRolesToRemove import ChooseModeratorRolesToRemove
from .functions import get_suggestion_settings_embed


def delete_message(message):
    async def task():
        try: await message.delete()
        except: pass
    loop = asyncio.get_event_loop()
    loop.create_task(task())


class ManageSuggestions(MyViewClass):
    def __init__(self, bot, ctx, suggestion_data):
        super().__init__(timeout = 300)
        self.bot = bot
        self.ctx = ctx
        self.suggestion_data = suggestion_data

    @discord.ui.select(
        placeholder = "Modifier un paramètre",
        options = [
            discord.SelectOption(label = "Statut des suggestions", emoji = "⏳", value = "enabled"),
            discord.SelectOption(label = "Salon de suggestion", emoji = "💡", value = "channel"),
            discord.SelectOption(label = "Salon de confirmation", emoji = "🔎", value = "confirm_channel"),
            discord.SelectOption(label = "Emoji \"pour\"", emoji = "✅", value = "for_emoji"),
            discord.SelectOption(label = "Emoji \"contre\"", emoji = "❌", value = "against_emoji"),
            discord.SelectOption(label = "Ajouter des rôles modérateurs", emoji = "➕", value = "add_moderator_roles"),
            discord.SelectOption(label = "Supprimer des rôles modérateurs", emoji = "➖", value = "remove_moderator_roles")
        ],
        custom_id = "select"
    )
    async def select_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        await interaction.response.defer()
        def get_option_name(current_option : str = None):
            if not current_option: current_option = select.values[0]

            for option in self.get_item("select").options:
                if option.value == current_option:
                    return option.label
            return None
        
        
        # ------------------------------ Pour les cas spéciaux
        if select.values[0] == "add_moderator_roles":
            if len(self.suggestion_data["moderator_roles"]) >= 15:
                await interaction.response.send_message("> Vous ne pouvez pas rajouter plus de 15 rôles modérateurs.", ephemeral = True)
                return
            
            await interaction.message.edit(view = ChooseModeratorRoles(self.bot, self.ctx, self))

        if select.values[0] == "remove_moderator_roles":
            if len(self.suggestion_data["moderator_roles"]) == 0:
                await interaction.response.send_message("> Vous n'avez pas configur de rôles modérateurs", ephemeral = True)
                return
            
            await interaction.message.edit(view = ChooseModeratorRolesToRemove(self.ctx, self))

        # ------------------------------ Demander une réponse
        if "moderator" not in select.values[0]:
            message = await self.ctx.send(
                f"> Quelle sera la nouvelle valeur de votre **{get_option_name().lower()}**? Envoyez `cancel` pour annuler"
                + (" et `delete` pour retirer l'option actuelle." if select.values[0] == "confirm_channel" else ".")
                + (" Répondez par `on` (ou `activé`) ou bien par `off` (ou `désactivé`)." if select.values[0] == "enabled" else "")
            )
            def response_check(message):
                return (message.author == interaction.user) and (message.content) and (message.channel == interaction.channel)
            try: response = await self.bot.wait_for("message", check = response_check, timeout = 60)
            except asyncio.TimeoutError:
                await self.ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                return
            finally: delete_message(message)
            delete_message(response)

            if response.content.lower() == "cancel":
                await self.ctx.send("> Action annulée.", delete_after = 3)
                return

        # ------------------------------ Gestion de la réponse
        if select.values[0] == "enabled":
            if response.content.lower().replace("é", "e") in ["active", "on", "enabled"]: self.suggestion_data["enabled"] = True
            elif response.content.lower().replace("é", "e") in ["desactive", "off", "disabled"]: self.suggestion_data["enabled"] = False
            else: await self.ctx.send("> Action annulée, réponse invalide.", delete_after = 3)

        if select.values[0] in ["channel", "confirm_channel"]:
            if (select.values[0] != "cancel") and (response.content.lower() == "delete"):
                self.suggestion_data[select.values[0]] = None
            else:
                searcher = Searcher(self.bot, self.ctx)
                channel = await searcher.search_channel(response.content)
                if not channel:
                    await self.ctx.send("> Action annulée, le salon donné est invalide.", delete_after = 3)
                    return
                
                opposed_option = ["channel", "confirm_channel"]
                opposed_option.remove(select.values[0])
                if self.suggestion_data[opposed_option[0]] == channel.id:
                    await self.ctx.send(f"> Action annulée, votre **{get_option_name().lower()}** ne peut pas être le même que votre **{get_option_name(opposed_option[0]).lower()}**.", delete_after = 3)
                    return
                
                self.suggestion_data[select.values[0]] = channel.id

        if select.values[0] in ["for_emoji", "against_emoji"]:
            tools = Tools(self.bot)
            found_emoji = await tools.get_emoji(response.content)
            if not found_emoji:
                await self.ctx.send("> Action annulée, l'emoji donné est invalide.", delete_after = 3)
                return
            
            self.suggestion_data[select.values[0]] = found_emoji

        await interaction.message.edit(embed = await get_suggestion_settings_embed(self.bot, self.ctx, self.suggestion_data))
    
    @discord.ui.button(label = "Sauvegarder", style = discord.ButtonStyle.primary)
    async def button_save_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        if (self.suggestion_data["enabled"]) and (not self.suggestion_data["channel"]):
            await self.ctx.send("> Si vous souhaitez activer le système de suggestion, un salon de suggestion sera obligatoire.", ephemeral = True)
            return
        
        for data, value in self.suggestion_data.items():
            await self.bot.db.set_data("suggestions", data, value if type(value) != list else json.dumps(value), guild_id = interaction.guild.id)
        
        suggestion_embed = await get_suggestion_settings_embed(self.bot, self.ctx, self.suggestion_data)
        suggestion_embed.title = "Paramètres de suggestions sauvegardés"

        await interaction.edit(embed = suggestion_embed, view = None)
    
    @discord.ui.button(emoji = "🗑", style = discord.ButtonStyle.danger)
    async def delete_button_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        await interaction.edit(embed = discord.Embed(title = "Configuration du système de suggestion annulée", color = await self.bot.get_theme(self.ctx.guild.id)), view = None)
