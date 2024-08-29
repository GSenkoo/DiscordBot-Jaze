import discord
import asyncio

from utils import GPChecker
from utils import MyViewClass
from utils import Tools

from .functions import get_selector_embed
from .functions import get_selector_option_embed
from .ManageRoles import ManageRoles


class ManageSelectorOption(MyViewClass):
    def __init__(self, bot, ctx, data, manage_selector_view):
        super().__init__(timeout = 180)
        self.bot = bot
        self.ctx = ctx
        self.data = data
        self.manage_selector_view = manage_selector_view

        for index, option_data in enumerate(self.manage_selector_view.selector_data["options_data"]):
            if option_data["label"] == self.data["label"]:
                self.option_index = index
                break
        assert self.option_index is not None


    @discord.ui.select(
        placeholder = "Modifier l'option",
        options = [
            discord.SelectOption(label = "Texte", emoji = "✏", value = "label"),
            discord.SelectOption(label = "Description", emoji = "📝", value = "description"),
            discord.SelectOption(label = "Emoji", emoji = "🎭", value = "emoji"),
            discord.SelectOption(label = "Rôle", emoji = "👤", value = "role"),
            discord.SelectOption(label = "Rôle requis", emoji = "📌", value = "required_role"),
            discord.SelectOption(label = "Rôle ignoré", emoji = "🚫", value = "ignored_role")
        ]
    )
    async def edit_selector_option_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        option_name = [option.label.lower() for option in select.options if option.value == select.values[0]][0]

        # ----------------------------------- LABEL / DESCRIPTION / EMOJI
        if select.values[0] in ["label", "description", "emoji"]:
            await interaction.response.defer()
            ask_message = await self.ctx.send(f"> Quel{'le' if select.values[0] == 'description' else ''} {option_name} souhaitez-vous définir à votre embed?")
            tools = Tools(self.bot)

            def response_check(message):
                return (message.author == interaction.user) and (message.content) and (message.channel == interaction.channel)

            try: response_message = await self.bot.wait_for('message', check = response_check, timeout = 60)
            except asyncio.TimeoutError():
                await self.ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                return
            finally: tools.create_delete_message_task(ask_message)
            tools.create_delete_message_task(response_message)

            # ----------------------------------- Le label d'une option est aussi utilisé comme un identifiant, donc ne doit pas être dupliquer.
            if select.values[0] == "label":
                options_data_copy = self.manage_selector_view.selector_data["options_data"].copy()
                del options_data_copy[self.option_index]

                for other_option_data in options_data_copy:
                    if other_option_data["label"] == response_message.content:
                        await self.ctx.send("> Il éxiste déjà une autre option ayant été définis avec ce texte.", delete_after = 3)
                        return

            # ----------------------------------- La taille maximum d'une description est de 100 caractères. C'est la même chose pour le label, mais il a été limité à 80 pour laisser de la marge.
            if select.values[0] in ["label", "description"]:
                if len(response_message.content) > (80 if select.values[0] == "label" else 100):
                    await self.ctx.send(f"> La taille de votre {option_name} ne doit pas dépasser les {80 if select.values[0] == 'label' else 100} caractères.", delete_after = 3)
                    return
                self.data[select.values[0]] = response_message.content
            
            # ----------------------------------- L'emoji doit juste éxister
            if select.values[0] == "emoji":
                emoji = await tools.get_emoji(response_message.content)
                if not emoji:
                    await self.ctx.send(f"> L'emoji donné est invalide.", delete_after = 3)
                    return
                self.data["emoji"] = str(emoji)
            
            await interaction.edit(embed = await get_selector_option_embed(self.data, self.ctx, self.bot))
        
        # ----------------------------------- ROLE / REQUIRED ROLE / IGNORED ROLE
        if "role" in select.values[0]:
            await interaction.edit(view = ManageRoles(self.bot, self.ctx, select.values[0], option_name, self))


    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
    async def back_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        self.manage_selector_view.selector_data["options_data"][self.option_index] = self.data.copy()
        self.manage_selector_view.update_displayed_options()
        await interaction.edit(embed = await get_selector_embed(self.manage_selector_view.selector_data, self.ctx, self.bot), view = self.manage_selector_view)