"""
{
    RoleMenu data format :

    "buttons": [
        {
            "id": "",
            "label": "Role 1",
            "emoji": "emoji_here",
            "color": "grey",
            "role": role_id_here,
            "required_role": required_role_id_here,
            "ignored_role": ignored_role_id_here
        }
        ...
    ],
    "selectors": [
        {
            "id": "",
            "placeholder": "Click here",
            "min_values": 0,
            "max_values": 1,
            "options_data": [
                {   
                    "label": "A label here",
                    "description": "A description here",
                    "emoji": "emoji_here",
                    "role": role_id_here,
                    "required_role": required_role_id_here,
                    "ignored_role": ignored_role_id_here
                }
                ...
            ]
        }
        ...
    ]
}
"""

"""
Schema of the system (in fragments.configuration.rolemenu) :

                    ManageRoleMenu() + functions.py
                    /             \ 
                   /               \ 
            ManageButton()    ManageSelector()
            + functions.py    + functions.py
                  \                /
                   \              /
                 ManageButtonRoles()   
"""

import discord
import asyncio

from discord import AllowedMentions as AM
from utils import MyViewClass
from utils import Tools

from .functions import get_main_embed
from .functions import get_button_embed
from .functions import get_role_menu_select_options
from .functions import get_selector_embed
from .ManageButton import ManageButton
from .ManageSelector import ManageSelector


class ManageRoleMenu(MyViewClass):
    def __init__(self, bot, ctx):
        super().__init__(timeout = 600)
        self.bot = bot
        self.ctx = ctx
        self.data = {"buttons": [], "selectors": []}
        
        def update_select():
            self.children[0].options = get_role_menu_select_options(self.data)
        self.update_select = update_select
        self.update_select()


    @discord.ui.select(
        placeholder = "Choisir un bouton/sélécteur",
        options = None
    )
    async def choose_interact_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        if select.values[0] == "nope":
            await interaction.response.defer()
            return
        
        manage_role_menu_view = self

        if select.values[0].startswith("button"):
            button_data = [button for button in self.data["buttons"] if button["id"] == select.values[0].split("_")[1]][0]
            await interaction.edit(embed = await get_button_embed(button_data, self.ctx, self.bot), view = ManageButton(self.bot, self.ctx, button_data, manage_role_menu_view))
        
        if select.values[0].startswith("selector"):
            selector_data = [selector for selector in self.data["selectors"] if selector["id"] == select.values[0].split("_")[1]][0]
            await interaction.edit(embed = await get_selector_embed(selector_data, self.ctx, self.bot), view = ManageSelector(self.bot, self.ctx, selector_data, manage_role_menu_view))


    @discord.ui.select(
        placeholder = "Gérer les sélécteurs et boutons",
        options = [
            discord.SelectOption(label = "Ajouter un bouton", emoji = "➕", value = "add_button"),
            discord.SelectOption(label = "Ajouter un sélécteur", emoji = "➕", value = "add_selector"),
            discord.SelectOption(label = "Retirer un bouton/sélécteur", emoji = "➖", value = "remove_selector"),
        ]
    )
    async def manage_interact_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        tools = Tools(self.bot)
        
        option_name = [option for option in select.options if option.value == select.values[0]][0].label
        interaction_type_translated = option_name.split(" ")[2]

        interaction_type = select.values[0].split("_")[1]
        action_type = select.values[0].split("_")[0]
        components_ids = [component["id"] for component in self.data[interaction_type + "s"]] # tous les identifiants des boutons OU sélécteurs
        
        if action_type == "add":
            if (interaction_type == "button") and (len(self.data["buttons"]) + len(self.data["selectors"]) * 5 == 25):
                await interaction.response.send_message(f"> Vous ne pouvez plus ajouter de bouton.", ephemeral = True)
                return
            if (interaction_type == "selector") and (len(self.data["buttons"]) + len(self.data["selectors"]) * 5 > 20):
                await interaction.response.send_message(f"> Vous ne pouvez plus ajouter de sélécteur.", ephemeral = True)
                return  
            
            await interaction.response.defer()

            # -------------------------------------------------- Ask
            ask_message = await self.ctx.send(f"> Quel sera le **nom** du {interaction_type_translated} que vous souhaitez ajouter? Envoyez `cancel` pour annuler.")
            def response_check(message):
                return (message.author == interaction.user) and (message.content) and (message.channel == interaction.channel)
            try: response_message = await self.bot.wait_for("message", check = response_check, timeout = 60)
            except asyncio.TimeoutError():
                await self.ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                return
            finally: tools.create_delete_message_task(ask_message)
            tools.create_delete_message_task(response_message)

            # -------------------------------------------------- Check
            if response_message.content.lower() == "cancel":
                await self.ctx.send("> Action annulée.", delete_after = 3)
                return
            if len(response_message.content) > 20:
                await self.ctx.send(f"> Le nom attribué à un {interaction_type} ne peut pas dépasser les 20 caractères.", delete_after = 3)
                return
            if response_message.content in components_ids:
                await self.ctx.send(f"> Il éxiste déjà un {interaction_type} avec le nom `{response_message.content}`.", allowed_mentions = AM.none(), delete_after = 3)
                return
            
            # -------------------------------------------------- Saves
            if interaction_type == "button":
                self.data["buttons"].append(
                    {
                        "id": response_message.content,
                        "label": "Cliquez ici",
                        "color": "grey",
                        "emoji": None,
                        "role": None,
                        "required_role": None,
                        "ignored_role": None
                    }
                )
                self.update_select()
                await interaction.message.edit(embed = await get_main_embed(self.bot, self.ctx, self.data), view = self)

            if interaction_type == "selector":
                self.data["selectors"].append(
                    {
                        "id": response_message.content,
                        "placeholder": "Choisir des rôles",
                        "min_values": 0,
                        "max_values": 1,
                        "options_data": []
                    }
                )
                self.update_select()
                await interaction.message.edit(embed = await get_main_embed(self.bot, self.ctx, self.data), view = self)

        if action_type == "remove":
            if (not self.data["buttons"]) and (not self.data["selectors"]):
                await interaction.response.send_message("> ")

            options = get_role_menu_select_options(self.data)
            manage_role_menu_view = self

            class ChooseOneToRemove(MyViewClass):
                @discord.ui.select(
                    placeholder = "Choisir un sélécteur/bouton",
                    options = options
                )
                async def choose_option_to_del_callback(self, select, interaction):
                    if interaction.user != manage_role_menu_view.ctx.author:
                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                        return

                    interaction_type = select.values[0].split("_")[0]
                    component_id = select.values[0].split("_")[1]

                    for index, component_data in enumerate(manage_role_menu_view.data[interaction_type + "s"]):
                        if component_data["id"] == component_id:
                            manage_role_menu_view.data[interaction_type + "s"].pop(index)
                            break

                    manage_role_menu_view.update_select()
                    await interaction.edit(embed = await get_main_embed(manage_role_menu_view.bot, manage_role_menu_view.ctx, manage_role_menu_view.data), view = manage_role_menu_view)
                    
                @discord.ui.button(label = "Choisissez un sélécteur/bouton", style = discord.ButtonStyle.primary, disabled = True)
                async def button_indicator_callback(self, button, interaction):
                    pass

                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                async def back_callback(self, button, interaction):
                    if interaction.user != manage_role_menu_view.ctx.author:
                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                        return    
                    await interaction.edit(view = manage_role_menu_view)

            await interaction.edit(view = ChooseOneToRemove())


    @discord.ui.button(label = "Confirmer", style = discord.ButtonStyle.primary)
    async def confirm_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return


    @discord.ui.button(style = discord.ButtonStyle.danger, emoji = "🗑")
    async def cancel_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        await interaction.edit(embed = discord.Embed(title = "Configuration annulée", color = await self.bot.get_theme(self.ctx.guild.id)), view = None)