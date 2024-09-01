import discord
import asyncio

from discord import AllowedMentions as AM

from utils import MyViewClass
from utils import Tools

from .functions import get_selector_embed
from .functions import get_formated_selector_options
from .functions import get_main_embed
from .functions import get_selector_option_embed
from .ManageSelectorOption import ManageSelectorOption


class ManageSelector(MyViewClass):
    def __init__(self, bot, ctx, selector_data, manage_role_menu_view):
        super().__init__(timeout = 300)
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
        
        option_label = select.values[0].split("_")[2] # Format d'une valeure d'une option : selector_option_{LABEL}
        option_data = [option for option in self.selector_data["options_data"] if option["label"] == option_label][0]
        await interaction.edit(embed = await get_selector_option_embed(option_data, self.ctx, self.bot), view = ManageSelectorOption(self.bot, self.ctx, option_data, self))
        
        
    @discord.ui.select(
        placeholder = "Modifier le sélecteur",
        options = [
            discord.SelectOption(label = "Texte", emoji = "✏", value = "placeholder"),
            discord.SelectOption(label = "Choix maximum", emoji = "⏫", value = "max_values"),
            discord.SelectOption(label = "Choix minimum", emoji = "⏬", value = "min_values"),
            discord.SelectOption(label = "Créer une option", emoji = "➕", value = "option_create"),
            discord.SelectOption(label = "Supprimer une option", emoji = "➖", value = "option_delete"),
            discord.SelectOption(label = "Réponse de confirmation", emoji = "💬", value = "send_response")        
        ]
    )
    async def edit_selector_callback(self, select, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        if (select.values[0] == "option_create" and len(self.selector_data["options_data"]) == 25):
            await interaction.response.send_message("> Vous ne pouvez plus ajouter d'option car vous avez déjà atteint la limite de 25 options.", ephemeral = True)
            return
        
        if select.values[0] in ["placeholder", "max_values", "min_values", "option_create"]:
            await interaction.response.defer()

            tools = Tools(self.bot)
            option_name = [option.label.lower() for option in select.options if option.value == select.values[0]][0]

            # -------------------------------------- Demande d'une valeure
            ask_message = await self.ctx.send(
                f"> Quel sera le **{option_name}** de votre sélecteur?" if select.values[0] != "option_create" else "> Quel **texte** souhaitez-vous définir à votre future option?"
            )
            
            def response_check(message):
                return (message.author == interaction.user) and (message.channel == interaction.channel) and (message.content)
            try:
                response_message = await self.bot.wait_for("message", check = response_check, timeout = 60)
            except asyncio.TimeoutError:
                await self.ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                return
            finally: tools.create_delete_message_task(ask_message)
            tools.create_delete_message_task(response_message)
            
            # -------------------------------------- Vérification de la valeure
            # ---------------------------- Selector - Placeholder
            if select.values[0] == "placeholder":
                if len(response_message.content) > 100:
                    await self.ctx.send("> La taille maximale du texte du sélecteur doit être inférieur à 100 caractères.", delete_after = 3)
                    return
                self.selector_data["placeholder"] = response_message.content


            if "values" in select.values[0]:
                if not response_message.content.isdigit():
                    await self.ctx.send("> Votre réponse doit être un nombre entier.", delete_after = 3)
                    return

                number = int(response_message.content)                
                if select.values[0] == "min_values":
                    if not 0 <= number <= 25:
                        await self.ctx.send("> Votre nombre de choix minimum doit être entre 0 (inclu) et 25 (inclu).", delete_after = 3)
                        return
                    if number > self.selector_data["max_values"]:
                        await self.ctx.send("> Votre nombre de choix minimum doit être inférieur ou égal à votre nombre de choix maximum.", delete_after = 3)
                        return
                
                if select.values[0] == "max_values":
                    if not 1 <= number <= 25:
                        await self.ctx.send("> Votre nombre de choix maximum doit être compris entre 1 (inclu) et 25 (inclu).", delete_after = 3)
                        return
                    if number < self.selector_data["min_values"]:
                        await self.ctx.send("> Votre nombre de choix maximum doit être suppérieur ou égal à votre nombre de choix maximum.", delete_after = 3)
                        return
                
                self.selector_data[select.values[0]] = number


            if select.values[0] == "option_create":
                if len(response_message.content) > 80:
                    await self.ctx.send("La taille maximale du texte de votre option doit être inférieur à 80 caractères.", delete_after = 3)
                    return
                
                for option_data in self.selector_data["options_data"]:
                    if option_data["label"] == response_message.content:
                        await self.ctx.send(f"> Une option sur sélecteur possède déjà le nom `{response_message.content if len(response_message.content) <= 100 else response_message.content[:100] + '...'}`.", allowed_mentions = AM.none(), delete_after = 3)
                        return
                    
                self.selector_data["options_data"].append({   
                    "label": response_message.content,
                    "description": None,
                    "emoji": None,
                    "role": None
                })
                self.update_displayed_options()
            
            await interaction.message.edit(embed = await get_selector_embed(self.selector_data, self.ctx, self.bot), view = self)


        if select.values[0] == "option_delete":
            if not self.selector_data["options_data"]:
                await interaction.response.send_message("> Il n'y a actuellement aucune option à supprimer sur sélecteur.", ephemeral = True)
                return

            manage_selector_view = self
            class ChooseOptionToDelete(MyViewClass):
                @discord.ui.select(
                    placeholder = "Choisir une option",
                    options = get_formated_selector_options(manage_selector_view.selector_data["options_data"])
                )
                async def choose_option_to_delete(self, select, interaction):
                    if interaction.user != manage_selector_view.ctx.author:
                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                        return
                    
                    option_label = select.values[0].split("_")[2] # Format d'une valeure d'une option : selector_option_{LABEL}
                    for index, options_data in enumerate(manage_selector_view.selector_data["options_data"]):
                        if options_data["label"] == option_label:
                            del manage_selector_view.selector_data["options_data"][index]
                            break
                    
                    manage_selector_view.update_displayed_options()
                    await interaction.edit(
                        embed = await get_selector_embed(manage_selector_view.selector_data, manage_selector_view.ctx, manage_selector_view.bot),
                        view = manage_selector_view
                    )

                @discord.ui.button(label = "Choisissez une option", style = discord.ButtonStyle.primary, disabled = True)
                async def button_indicator_callback(self, button, interaction):
                    pass

                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                async def back_callback(self, button, interaction):
                    if interaction.user != manage_selector_view.ctx.author:
                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                        return

                    await interaction.edit(view = manage_selector_view)

            await interaction.edit(view = ChooseOptionToDelete())


        if select.values[0] == "send_response":
            self.selector_data["send_response"] = not self.selector_data["send_response"]
            await interaction.edit(embed = await get_selector_embed(self.selector_data, self.ctx, self.bot))


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