import discord
import asyncio

from utils import MyViewClass
from utils import Tools
from utils import GPChecker

from .functions import get_button_embed
from .functions import get_main_embed
from .ManageRoles import ManageRoles

class ManageButton(MyViewClass):
    def __init__(self, bot, ctx, data, manage_role_menu_view):
        super().__init__(timeout = 180)
        self.bot = bot
        self.ctx = ctx
        self.data = data
        self.manage_role_menu_view = manage_role_menu_view

    @discord.ui.select(
        placeholder = "Modifier le bouton",
        options = [
            discord.SelectOption(label = "Texte", emoji = "✏", value = "label"),
            discord.SelectOption(label = "Emoji", emoji = "🎭", value = "emoji"),
            discord.SelectOption(label = "Couleur", emoji = "🎨", value = "color"),
            discord.SelectOption(label = "Rôle", emoji = "👤", value = "role"),
            discord.SelectOption(label = "Rôle requis", emoji = "📌", value = "required_role"),
            discord.SelectOption(label = "Rôle ignoré", emoji = "🚫", value = "ignored_role")
        ]
    )
    async def edit_button_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        tools = Tools(self.bot)
        
        option_name = [option.label for option in select.options if option.value == select.values[0]][0]
        if select.values[0] in ["label", "emoji", "color"]:
            await interaction.response.defer()
            message = await self.ctx.send(f"> Quel{'le' if select.values == 'color' else ''} **{option_name}** souhaitez-vous définir à votre bouton?" + (" Couleurs disponibles : `bleu`, `rouge`, `vert` et `gris`" if select.values[0] == "color" else ""))

            async def response_check(message):
                return (message.channel == interaction.channel) and (message.author == interaction.user) and (message.content)
            
            try: response_message = await self.bot.wait_for("message", check = response_check, timeout = 60)
            except asyncio.TimeoutError():
                await self.ctx.send("> Action annulée, 1 miute s'est écoulée.")
                return
            finally: tools.create_delete_message_task(message)
            tools.create_delete_message_task(response_message)

            # -------------------------------------- Button - Text
            if select.values[0] == "label":
                if len(response_message.content) > 80:
                    await self.ctx.send("> Le texte d'un bouton ne peut pas faire plus de 80 caractères.", delete_after = 3)
                    return
                self.data["label"] = response_message.content
            
            # -------------------------------------- Button - Emoji
            if select.values[0] == "emoji":
                tools = Tools(self.bot)
                emoji = await tools.get_emoji(response_message.content)

                if not emoji:
                    await self.ctx.send("> L'emoji donné est invalide.", delete_after = 3)
                    return
                self.data["emoji"] = str(emoji)

            # -------------------------------------- Button - Color
            if select.values[0] == "color":
                query = response_message.content.lower()
                if   query in ["bleu", "blue", "blurple"]: self.data["color"] = "blurple"
                elif query in ["rouge", "red"]: self.data["color"] = "red"
                elif query in ["vert", "green"]: self.data["color"] = "green"
                elif query in ["grey", "gris"]: self.data["color"] = "grey"
                else:
                    await self.ctx.send("> La couleur de bouton donné est invalide.", delete_after = 3)
                    return

            await interaction.message.edit(embed = await get_button_embed(self.data, self.ctx, self.bot))

        if "role" in select.values[0]:
            await interaction.edit(view = ManageRoles(self.bot, self.ctx, select.values[0], option_name, self))
        

    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
    async def back_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        for index, previous_data in enumerate(self.manage_role_menu_view.data["buttons"]):
            if previous_data["id"] == self.data["id"]:
                self.manage_role_menu_view.data["buttons"][index] = self.data.copy()
                break
        self.manage_role_menu_view.update_select()
        await interaction.edit(embed = await get_main_embed(self.bot, self.ctx, self.manage_role_menu_view.data), view = self.manage_role_menu_view)