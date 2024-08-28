import discord
import asyncio

from utils import MyViewClass
from utils import Tools
from utils import GPChecker

from .functions import get_button_embed
from .functions import get_main_embed

class ManageButton(MyViewClass):
    def __init__(self, bot, ctx, button_data, manage_role_menu_view):
        super().__init__(timeout = 180)
        self.bot = bot
        self.ctx = ctx
        self.button_data = button_data
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
            message = await self.ctx.send(f"> Quel **{option_name}** souhaitez-vous définir à votre bouton?" + (" Couleurs disponibles : `bleu`, `rouge`, `vert` et `gris`" if select.values[0] == "color" else ""))

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
                self.button_data["label"] = response_message.content
            
            # -------------------------------------- Button - Emoji
            if select.values[0] == "emoji":
                tools = Tools(self.bot)
                emoji = await tools.get_emoji(response_message.content)

                if not emoji:
                    await self.ctx.send("> L'emoji donné est invalide.", delete_after = 3)
                    return
                self.button_data["emoji"] = str(emoji)

            # -------------------------------------- Button - Color
            if select.values[0] == "color":
                query = response_message.content.lower()
                if   query in ["bleu", "blue", "blurple"]: self.button_data["color"] = "blurple"
                elif query in ["rouge", "red"]: self.button_data["color"] = "red"
                elif query in ["vert", "green"]: self.button_data["color"] = "green"
                elif query in ["grey", "gris"]: self.button_data["color"] = "grey"
                else:
                    await self.ctx.send("> La couleur de bouton donné est invalide.", delete_after = 3)
                    return

            await interaction.message.edit(embed = await get_button_embed(self.button_data, self.ctx, self.bot))

        if "role" in select.values[0]:
            manage_button_view = self
            choosed_value = select.values[0]
            

            class ChooseButtonRole(MyViewClass):
                @discord.ui.select(
                    select_type = discord.ComponentType.role_select,
                    placeholder = f"Choisir un rôle"
                )
                async def choose_role_select_callback(self, select, interaction):
                    if interaction.user != manage_button_view.ctx.author:
                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                        return
                    
                    role = interaction.guild.get_role(select.values[0].id)
                    if not role:
                        await interaction.response.send_message("> Le rôlé donné est invalide ou alors je n'y ai pas accès.", ephemeral = True)
                        return
                    
                    gp_checker = GPChecker(manage_button_view.ctx, manage_button_view.bot)
                    check = gp_checker.we_can_add_role(role)
                    if check != True:
                        await interaction.response.send_message(check, ephemeral = True)
                        return
                    
                    options_translated = {"required_role": "rôle requis", "ignored_role": "rôle ignoré", "role": "rôle du bouton"}
                    if choosed_value != "required_role":
                        if (manage_button_view.button_data["required_role"] if manage_button_view.button_data["required_role"] else "nah") == select.values[0].id:
                            await interaction.response.send_message(f"> Le {options_translated[choosed_value]} ne peut pas être le même que le {options_translated['required_role']}.", ephemeral = True)
                            return
                    else:
                        if (manage_button_view.button_data["required_role"] if manage_button_view.button_data["required_role"] else "nah") in [manage_button_view.button_data["role"], manage_button_view.button_data["ignored_role"]]:
                            await interaction.response.send_message(f"> Le {options_translated[choosed_value]} ne peut pas être le même que le {options_translated['required_role']}.", ephemeral = True)
                            return
                    
                    manage_button_view.button_data[choosed_value] = select.values[0].id
                    await interaction.edit(embed = await get_button_embed(manage_button_view.button_data, manage_button_view.ctx, manage_button_view.bot), view = manage_button_view)
                    
                @discord.ui.button(label = f"Choisissez un {option_name.lower()}", style = discord.ButtonStyle.primary, disabled = True)
                async def button_callback(self, button, interaction):
                    pass

                @discord.ui.button(label = "Retirer", emoji = "❌", style = discord.ButtonStyle.danger)
                async def remove_callback(self, button, interaction):
                    if interaction.user != manage_button_view.ctx.author:
                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                        return
                    
                    manage_button_view.button_data[choosed_value] = None
                    await interaction.edit(embed = await get_button_embed(manage_button_view.button_data, manage_button_view.ctx, manage_button_view.bot), view = manage_button_view)
                    

                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                async def comeback_callback(self, button, interaction):
                    if interaction.user != manage_button_view.ctx.author:
                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                        return
                    await interaction.edit(view = manage_button_view)

            await interaction.edit(view = ChooseButtonRole())
        

    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
    async def back_callback(self, button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        
        for index, button_previous_data in enumerate(self.manage_role_menu_view.data["buttons"]):
            if button_previous_data["id"] == self.button_data["id"]:
                self.manage_role_menu_view.data["buttons"][index] = self.button_data.copy()
                break
        self.manage_role_menu_view.update_select()
        await interaction.edit(embed = await get_main_embed(self.bot, self.ctx, self.manage_role_menu_view.data), view = self.manage_role_menu_view)