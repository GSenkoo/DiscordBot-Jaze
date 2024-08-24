import discord
import json
import asyncio
import textwrap

from discord.ui.item import Item
from discord.ext import commands
from discord import AllowedMentions as AM
from utils.Paginator import PaginatorCreator
from utils.Searcher import Searcher
from utils.MyViewClass import MyViewClass
from utils.Tools import Tools
from utils.GPChecker import GPChecker

def delete_message(message):
    async def task():
        try: await message.delete()
        except: pass
    loop = asyncio.get_event_loop()
    loop.create_task(task())

class Configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Définir les rôles qui ne seront pas retirés lors des derank et blrank", usage = "<add/del/reset/list> [role]")
    @commands.guild_only()
    async def noderank(self, ctx, action : str, role : discord.Role = None):
        if action.lower() not in ["add", "del", "list", "reset"]:
            await ctx.send(f"> Action invalide, voici un rappel d'utilisation : `{await self.bot.get_prefix(ctx.message)}noderank <add/del/reset/list> [role]`.")
            return
        
        if (action.lower() not in ["list", "reset"]) and (not role):
            await ctx.send("> Si votre action est \"add\" ou \"del\", alors le paramètre `role` devient obligatoire.")
            return

        noderank_roles = await self.bot.db.get_data("guild", "noderank_roles", True, guild_id = ctx.guild.id)

        if action.lower() == "list":
            paginator_creator = PaginatorCreator()
            paginator = await paginator_creator.create_paginator(
                title = "Rôles noderank",
                embed_color = await self.bot.get_theme(ctx.guild.id),
                data_list = [f"<@&{noderank_role}>" for noderank_role in noderank_roles],
                no_data_message = "*Aucun rôle noderank*",
                page_counter = False
            )

            if type(paginator) == list:
                await ctx.send(embed = paginator[0])
            else:
                await paginator.send(ctx)
            return
        
        if action.lower() == "del":
            if role.id not in noderank_roles:
                await ctx.send(f"> Le rôle {role.mention} n'est pas un rôle noderank.", allowed_mentions = AM.none())
                return
            
            noderank_roles.remove(role.id)
        if action.lower() == "add":
            if role.id in noderank_roles:
                await ctx.send(f"> Le rôle {role.mention} est déjà un rôle noderank.", allowed_mentions = AM.none())
                return
            
            noderank_roles.append(role.id)

        if action.lower() == "reset":
            if not noderank_roles:
                await ctx.send(f"> Il n'y a aucun rôle noderank, donc rien à réinitialiser.")
                return
            
            await ctx.send(f"> Un total de {len(noderank_roles)} rôles ne sont désormais plus noderank.")
            noderank_roles = []
        
        await self.bot.db.set_data("guild", "noderank_roles", json.dumps(noderank_roles), guild_id = ctx.guild.id)

        if action.lower() == "reset": return
        await ctx.send(f"> Le rôle {role.mention} " + ("sera désorormais" if action == "del" else "ne sera désormais plus") + " retiré lors des derank.", allowed_mentions = AM.none())


    @commands.command(description = "Définir la limite de suppression de message par commande clear")
    @commands.guild_only()
    async def clearlimit(self, ctx, number : int):
        if not 5 <= number <= 10000:
            await ctx.send("> Votre nombre maximal de suppression de message par commande clear doit être entre 5 et 10000.")
            return

        clear_limit = await self.bot.db.get_data("guild", "clear_limit", guild_id = ctx.guild.id)
        if clear_limit == number:
            await ctx.send(f"> La limite de suppression de message par commande clear est déjà définis à {clear_limit}.")
            return

        await self.bot.db.set_data("guild", "clear_limit", number, guild_id = ctx.guild.id)
        await ctx.send(f"> La limite de suppression de message par commande clear a été définis à **{number}** messages.")

    
    @commands.command(description = "Changer le thème du bot", aliases = ["setcolor", "color", "settheme"])
    @commands.guild_only()
    async def theme(self, ctx, color : discord.Color):
        await self.bot.set_theme(ctx.guild.id, color.value)
        await ctx.send(f"> Le thème du bot a correctement été défini à `{color}`")


    @commands.command(description = "Modifier le prefix du bot", aliases = ["setprefix"])
    @commands.guild_only()
    async def prefix(self, ctx, prefix : str):
        if len(prefix) > 5:
            await ctx.send("> Votre prefix ne peut pas faire plus de 5 caractères.")
            return
        
        if "`" in prefix:
            await ctx.send("> Votre prefix ne peut pas contenir le caractère \"`\".")
            return
        
        commands_names = [command.name for command in self.bot.commands]
        if prefix in commands_names:
            await ctx.send("> Votre prefix ne peut pas être le nom d'une commande.")
            return
        
        await self.bot.set_prefix(ctx.guild.id, prefix)
        await ctx.send(f"> Le préfix du bot sur ce serveur est désormais `{prefix}`.")
    

    @commands.command(description = "Modifier le style de navigation du help (sélecteur/bouton)", usage = "<selector/button>", aliases = ["hltp"])
    @commands.guild_only()
    async def helptype(self, ctx, helptype : str):
        if helptype.lower() not in ["selector", "button"]:
            await ctx.send(f"> Type de help invalide, rappel d'utilisation de la commande : `{await self.bot.get_prefix(ctx.message)}helptype <selector/button>`.")
            return
        
        current_helptype = await self.bot.db.get_data("guild", "help_type", guild_id = ctx.guild.id)
        if current_helptype == helptype[:1].lower():
            await ctx.send(f"> Le type de help actuel est déjà défini sur **{helptype}**.")
            return
        
        await self.bot.db.set_data("guild", "help_type", helptype[:1].lower(), guild_id = ctx.guild.id)
        await ctx.send(f"> Le type de help a bien été défini sur **{helptype}**.")


    @commands.command(description = "Ajouter/Supprimer des salons où les membres seront mentionné à l'arrivée", usage = "<add/del/reset/list> [channel]")
    @commands.guild_only()
    async def ghostping(self, ctx, action : str, channel : discord.TextChannel = None):
        if action.lower() not in ["add", "del", "list", "reset"]:
            await ctx.send(f"> Action invalide, rappel d'utilisation de la commande : `{await self.bot.get_prefix(ctx.message)}ghostping <add/del/reset/list> [channel]`")
            return
        
        if not channel:
            channel = ctx.channel
        
        ghostping_channels = await self.bot.db.get_data("guild", "ghostping_channels", True, guild_id = ctx.guild.id)
        if action.lower() == "list":
            if not ghostping_channels:
                await ctx.send(f"> Il n'y aucun salon ghostping.")
                return
            
            embed = discord.Embed(
                title = f"Salons ghostping ({len(ghostping_channels)}/10)",
                color = await self.bot.get_theme(ctx.guild.id),
                description = f"\n".join([f"<#{channel_id}> (`{channel_id}`)" for channel_id in ghostping_channels])
            )

            await ctx.send(embed = embed)
            return

        if action.lower() == "add":
            if len(ghostping_channels) >= 10:
                await ctx.send(f"> Vous ne pouvez pas définir plus de 10 salons ghostping.")
                return
            if channel.id in ghostping_channels:
                await ctx.send(f"> Le salon {channel.mention} est déjà dans la liste des salons ghostping.")
                return

            ghostping_channels.append(channel.id)
            await ctx.send(f"> Les nouveaux membres seront désormais mentionnés dans le salon {channel.mention}.")

        if action.lower() == "del":
            if channel.id not in ghostping_channels:
                await ctx.send(f"> Le salon {channel.mention} n'est pas dans la liste des salons ghostping.")
                return
            
            ghostping_channels.remove(channel.id)
            await ctx.send(f"> Les nouveaux membres ne seront désormais plus mentionnés dans le salon {channel.mention}.")
        if action.lower() == "reset":
            if not ghostping_channels:
                await ctx.send(f"> Il n'y aucun salon ghostping, donc rien à réinitialiser.")
                return
            
            await ctx.send(f"> Un total de {len(ghostping_channels)} salons ne recevront plus de mention de nouveaux membres.")
            ghostping_channels = []

        await self.bot.db.set_data("guild", "ghostping_channels", json.dumps(ghostping_channels), guild_id = ctx.guild.id)

    
    @commands.command(description = "Définir des rôles qui seront automatiquements ajoutés aux nouveaux membres", usage = "<add/del/reset/list> [role]")
    @commands.guild_only()
    async def joinrole(self, ctx, action, role : discord.Role = None):
        if action.lower() not in ["add", "del", "list", "reset"]:
            await ctx.send(f"> Action invalide, rappel d'utilisation de la commande : `{await self.bot.get_prefix(ctx.message)}joinrole <add/del/reset/list> [role]`")
            return

        if (action.lower() in ["add", "del"]) and (not role):
            await ctx.send("> Si votre action est \"add\" ou \"del\", le paramètre `role` devient obligatoire.")
            return
        
        join_roles = await self.bot.db.get_data("guild", "join_roles", True, guild_id = ctx.guild.id)
        if action.lower() == "list":
            if not join_roles:
                await ctx.send(f"> Il n'y aucun rôle automatiquement ajouté aux nouveaux membres.")
                return
            
            embed = discord.Embed(
                title = f"Join roles ({len(join_roles)}/10)",
                color = await self.bot.get_theme(ctx.guild.id),
                description = f"\n".join([f"<@&{role_id}> (`{role_id}`)" for role_id in join_roles])
            )

            await ctx.send(embed = embed)
            return

        if action.lower() == "add":
            if len(join_roles) >= 10:
                await ctx.send(f"> Vous ne pouvez pas définir plus de 10 rôles ajoutés aux nouveaux membres.")
                return
            if role.id in join_roles:
                await ctx.send(f"> Le rôle {role.mention} est déjà dans la liste des rôles automatiquements ajoutés aux nouveaux membres.", allowed_mentions = AM.none())
                return
            
            gp_checker = GPChecker(ctx, self.bot)
            check = await gp_checker.we_can_add_role(role)
            if check != True:
                await ctx.send(check, allowed_mentions = AM.none())
                return
            
            captcha_role_id = await self.bot.db.get_data("captcha", "non_verified_role", guild_id = ctx.guild.id)
            if role.id == captcha_role_id:
                await ctx.send("> Le rôle des utilisateurs non vérifiés (dans le système de captcha) ne peut pas être dans la liste des rôles automatiquements ajoutés.")
                return              

            join_roles.append(role.id)
            await ctx.send(f"> Les nouveaux membres srecevront désormais automatiquement le rôle {role.mention}.", allowed_mentions = AM.none())

        if action.lower() == "del":
            if role.id not in join_roles:
                await ctx.send(f"> Le rôle {role.mention} n'est pas dans la liste des rôles à automatiquement ajouter aux nouveaux membres.", allowed_mentions = AM.none())
                return
            
            join_roles.remove(role.id)
            await ctx.send(f"> Les nouveaux membres ne recevront désormais plus automatiquement le rôle {role.mention}.", allowed_mentions = AM.none())
        if action.lower() == "reset":
            if not join_roles:
                await ctx.send(f"> Il n'y aucun rôles automatiquements ajoutés aux nouveaux membres, donc rien à réinitialiser.")
                return
            
            await ctx.send(f"> Un total de {len(join_roles)} rôles ne seront désormais plus ajouté aux nouveaux membres.")
            join_roles = []

        await self.bot.db.set_data("guild", "join_roles", json.dumps(join_roles), guild_id = ctx.guild.id)


    @commands.command(description = "Configurer l'ajout automatique d'un emoji spécifique dans un salon", usage = "<add/del/reset/list> [emoji] [channel]")
    @commands.guild_only()
    async def autoreact(self, ctx, action : str, emoji : str = None, channel : discord.TextChannel = None):
        tools = Tools(self.bot)
        action = action.lower()

        if action not in ["add", "del", "list", "reset"]:
            await ctx.send(f"> Action invalide, rappel d'utilisation de la commande : `{await self.bot.get_prefix(ctx.message)}autoreact <add/del/reset/list> [emoji] [channel]`")
            return
        
        if not channel: channel = ctx.channel
        
        if action in ["add", "del"]:
            if not emoji:
                await ctx.send("> Les paramètres `emoji` deviennent obligatoire si votre action est \"add\" ou \"del\".")
                return
          
        autoreact_data = await self.bot.db.get_data("guild", "autoreact", False, True, guild_id = ctx.guild.id)
        if action != "add":
            if not autoreact_data:
                await ctx.send("> Aucun ajout de réaction automatique a été configuré sur ce serveur.")
                return 

        if action == "list":
            embed = discord.Embed(
                title = f"Autoreact ({len(autoreact_data)}/5)",
                description = "\n".join([f"<#{channel_id}> : {', '.join(reactions)}" for channel_id, reactions in autoreact_data.items()]),
                color = await self.bot.get_theme(ctx.guild.id)
            )
            await ctx.send(embed = embed)
            return

        if action == "reset":
            await ctx.send(f"> Un total de {len(autoreact_data)} salons n'aura désormais plus d'ajout automatique de réactions.")
            autoreact_data = {}

        if action == "del":
            if str(channel.id) not in autoreact_data.keys():
                await ctx.send(f"> Le salon {channel.mention} n'a aucune réaction automatique configuré.")
                return
            
            found_emoji = await tools.get_emoji(emoji)
            if not found_emoji:
                await ctx.send(f"> L'emoji donné est invalide.")
                return
            
            if str(found_emoji) not in autoreact_data[str(channel.id)]:
                await ctx.send(f"> L'emoji donné n'est pas dans la liste des réactions automatiques du salon {channel.mention}.")
                return
            
            autoreact_data[str(channel.id)].remove(str(found_emoji))
            if not autoreact_data[str(channel.id)]:
                del autoreact_data[str(channel.id)]
            await ctx.send(f"> La réaction {found_emoji} ne sera désormais plus automatiquement ajouté dans le salon {channel.mention}.")

        if action == "add":
            found_emoji = await tools.get_emoji(emoji)
            if not found_emoji:
                await ctx.send(f"> L'emoji donné est invalide.")
                return
            
            if found_emoji in autoreact_data.get(str(channel.id), []):
                await ctx.send(f"> L'emoji donné est déjà dans la liste des réactions automatiques du salon {channel.mention}.")
                return

            if (str(channel.id) not in autoreact_data.keys()) and (len(autoreact_data) >= 5):
                await ctx.send("> Vous ne pouvez pas ajouter plus de 5 salons disposant d'ajout de réaction automatique.")
                return
            
            if len(autoreact_data.get(str(channel.id), [])) >= 3:
                await ctx.send("> Vous ne pouvez pas ajouter plus de 3 réactions automatiques par salon.")
                return
            
            autoreact_data[str(channel.id)] = autoreact_data.get(str(channel.id), []) + [str(found_emoji)]
            await ctx.send(f"> La réaction {found_emoji} sera désormais automatiquement ajouté dans le salon {channel.mention}.")

        await self.bot.db.set_data("guild", "autoreact", json.dumps(autoreact_data), guild_id = ctx.guild.id)
    

    @commands.command(description = "Configurer les paramètres de suggestion")
    @commands.guild_only()
    async def suggestions(self, ctx):
        suggestions_found = await self.bot.db.execute(f"SELECT * FROM suggestions WHERE guild_id = {ctx.guild.id}", fetch = True)
        searcher = Searcher(self.bot, ctx)
        tools = Tools(self.bot)

        if not suggestions_found:
            suggestion_data = {
                "channel": ctx.channel.id, "confirm_channel": None,
                "moderator_roles": [],
                "enabled": False, "for_emoji": "✅", "against_emoji": "❌"
            }
        else:
            suggesiton_columns = await self.bot.db.get_table_columns("suggestions")
            suggestion_current_data = dict(set(zip(suggesiton_columns, suggestions_found[0])))
            suggestion_data = {
                "channel": suggestion_current_data["channel"], "confirm_channel": suggestion_current_data["confirm_channel"],
                "moderator_roles": json.loads(suggestion_current_data["moderator_roles"]),
                "enabled": suggestion_current_data["enabled"], "for_emoji": suggestion_current_data["for_emoji"], "against_emoji": suggestion_current_data["against_emoji"]
            }
        
        async def get_suggestion_settings_embed(data : dict):
            embed = discord.Embed(
                title = "Paramètres de suggestions",
                color = await self.bot.get_theme(ctx.guild.id),
                description = "*Si aucun salon de confirmation n'est donné, alors les suggestions ne seront pas vérifiés.* "
                + "*Les utilisateurs avec la permission owner et le propriétaire peuvent confirmer les suggestions sans avoir à avoir un rôle modérateur.*"
            )

            embed.add_field(name = "Statut", value = "Activé" if data["enabled"] else "Désactivé")
            embed.add_field(name = "Salon de suggestion", value = f"<#{data['channel']}>" if data['channel'] else "*Aucun salon*")
            embed.add_field(name = "Salon de confirmation", value = f"<#{data['confirm_channel']}>" if data['confirm_channel'] else "*Aucun salon*")
            embed.add_field(name = "Emoji \"pour\"", value = data["for_emoji"])
            embed.add_field(name = "Emoji \"contre\"", value = data["against_emoji"])
            embed.add_field(name = "Rôles modérateurs", value = "<@&" + ">\n<@&".join([str(role_id) for role_id in data['moderator_roles']]) + ">" if data['moderator_roles'] else "*Aucun rôles modérateurs*")

            return embed

        bot = self.bot
        class Suggestions(discord.ui.View):
            def __init__(self, suggestion_data):
                super().__init__(timeout = 300)
                self.suggestion_data = suggestion_data

            async def on_timeout(self):
                try: await self.message.edit(view = None)
                except: pass

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
                if interaction.user != ctx.author:
                    await interaction.response.send("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.response.defer()
                def get_option_name(current_option : str = None):
                    if not current_option: current_option = select.values[0]

                    for option in self.get_item("select").options:
                        if option.value == current_option:
                            return option.label
                    return None
                
                def check_validity(message):
                    return (message.author == ctx.author) and (message.content) and (message.channel == ctx.channel)
                
                # ------------------------------ Pour les cas spéciaux
                if select.values[0] == "add_moderator_roles":
                    if len(self.suggestion_data["moderator_roles"]) >= 15:
                        await interaction.response.send_message("> Vous ne pouvez pas rajouter plus de 15 rôles modérateurs.", ephemeral = True)
                        return
                    
                    previous_view = self
                    class ChooseRole(MyViewClass):
                        @discord.ui.select(
                            placeholder = "Choisissez un rôle",
                            select_type = discord.ComponentType.role_select,
                            max_values = 15 - len(self.suggestion_data["moderator_roles"])
                        )
                        async def select_choose_role_callback(self, select, interaction):
                            if interaction.user != ctx.author:
                                await interaction.response.send("> Vous n'êtes pas autorisés à intéragir avec ceci.")
                                return
                            
                            for role in select.values:
                                if (role in previous_view.suggestion_data["moderator_roles"]) or (len(previous_view.suggestion_data["moderator_roles"]) >= 15):
                                    continue
                                previous_view.suggestion_data["moderator_roles"].append(role.id)

                            await interaction.message.edit(view = previous_view, embed = await get_suggestion_settings_embed(previous_view.suggestion_data))
                            await interaction.response.defer()

                        @discord.ui.button(label = "Choisissez un rôle", style = discord.ButtonStyle.primary, disabled = True)
                        async def button_callback(self, button, interaction):
                            pass

                    await interaction.message.edit(view = ChooseRole())

                if select.values[0] == "remove_moderator_roles":
                    if len(self.suggestion_data["moderator_roles"]) == 0:
                        await interaction.response.send_message("> Vous n'avez pas configur de rôles modérateurs", ephemeral = True)
                        return
                    
                    roles_ids_to_name = {}
                    for role_id in self.suggestion_data["moderator_roles"]:
                        role = ctx.guild.get_role(role_id)
                        if role: roles_ids_to_name[str(role_id)] = "@" +  role.name
                        else: roles_ids_to_name[str(role_id)] = "@RôleIntrouvable"

                    previous_view = self
                    class ChooseRoleToRemove(MyViewClass):
                        @discord.ui.select(
                            placeholder = "Choisissez un rôle",
                            max_values = len(roles_ids_to_name),
                            options = [
                                discord.SelectOption(label = role_name, description = f"Identifiant : {role_id}", value = role_id) for role_id, role_name in roles_ids_to_name.items()
                            ],
                
                        )
                        async def select_remove_role_callback(self, select, interaction):
                            if interaction.user != ctx.author:
                                await interaction.response.send("> Vous n'êtes pas autorisés à intéragir avec ceci.")
                                return
                            
                            for role_id in select.values:
                                if (int(role_id) not in previous_view.suggestion_data["moderator_roles"]):
                                    continue
                                previous_view.suggestion_data["moderator_roles"].remove(int(role_id))
                            
                            await interaction.message.edit(view = previous_view, embed = await get_suggestion_settings_embed(previous_view.suggestion_data))
                            await interaction.response.defer()
                        
                        @discord.ui.button(label = "Choisissez un rôle", style = discord.ButtonStyle.primary, disabled = True)
                        async def button_info_callback(self, button, interaction):
                            pass

                    await interaction.message.edit(view = ChooseRoleToRemove())


                # ------------------------------ Demander une réponse
                if "moderator" not in select.values[0]:
                    message = await ctx.send(
                        f"> Quelle sera la nouvelle valeur de votre **{get_option_name().lower()}**? Envoyez `cancel` pour annuler"
                        + (" et `delete` pour retirer l'option actuelle." if select.values[0] == "confirm_channel" else ".")
                        + (" Répondez par `on` (ou `activé`) ou bien par `off` (ou `désactivé`)." if select.values[0] == "enabled" else "")
                    )

                    try: response = await bot.wait_for("message", check = check_validity, timeout = 60)
                    except:
                        await ctx.send("> Action annulée, une minute s'est écoulée.", delete_after = 3)
                        return
                    finally: delete_message(message)
                    delete_message(response)

                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 3)
                        return

                # ------------------------------ Gestion de la réponse
                if select.values[0] == "enabled":
                    if response.content.lower().replace("é", "e") in ["active", "on", "enabled"]: self.suggestion_data["enabled"] = True
                    elif response.content.lower().replace("é", "e") in ["desactive", "off", "disabled"]: self.suggestion_data["enabled"] = False
                    else: await ctx.send("> Action annulée, réponse invalide.", delete_after = 3)

                if select.values[0] in ["channel", "confirm_channel"]:
                    if (select.values[0] != "cancel") and (response.content.lower() == "delete"):
                        self.suggestion_data[select.values[0]] = None
                    else:
                        channel = await searcher.search_channel(response.content)
                        if not channel:
                            await ctx.send("> Action annulée, le salon donné est invalide.", delete_after = 3)
                            return
                        
                        opposed_option = ["channel", "confirm_channel"]
                        opposed_option.remove(select.values[0])
                        if self.suggestion_data[opposed_option[0]] == channel.id:
                            await ctx.send(f"> Action annulée, votre **{get_option_name().lower()}** ne peut pas être le même que votre **{get_option_name(opposed_option[0]).lower()}**.", delete_after = 3)
                            return
                        
                        self.suggestion_data[select.values[0]] = channel.id

                if select.values[0] in ["for_emoji", "against_emoji"]:
                    found_emoji = await tools.get_emoji(response.content)
                    if not found_emoji:
                        await ctx.send("> Action annulée, l'emoji donné est invalide.", delete_after = 3)
                        return
                    
                    self.suggestion_data[select.values[0]] = found_emoji

                await interaction.message.edit(embed = await get_suggestion_settings_embed(self.suggestion_data))
            
            @discord.ui.button(label = "Sauvegarder", style = discord.ButtonStyle.success)
            async def button_save_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if (self.suggestion_data["enabled"]) and (not self.suggestion_data["channel"]):
                    await ctx.send("> Si vous souhaitez activer le système de suggestion, un salon de suggestion sera obligatoire.", ephemeral = True)
                    return
                
                for data, value in self.suggestion_data.items():
                    await bot.db.set_data("suggestions", data, value if type(value) != list else json.dumps(value), guild_id = interaction.guild.id)
                
                suggestion_embed = await get_suggestion_settings_embed(self.suggestion_data)
                suggestion_embed.title = "Paramètres de suggestions sauvegardés"

                await interaction.message.edit(embed = suggestion_embed, view = None)
                await interaction.response.defer()
            
            @discord.ui.button(emoji = "🗑", style = discord.ButtonStyle.danger)
            async def delete_button_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.message.edit(embed = discord.Embed(title = "Configuration du système de suggestion annulée", color = await bot.get_theme(ctx.guild.id)), view = None)
                await interaction.response.defer()

        await ctx.send(embed = await get_suggestion_settings_embed(suggestion_data), view = Suggestions(suggestion_data))


    @commands.command(description = "Configurer l'ajout d'un rôle automatique selon le status")
    @commands.guild_only()
    async def soutien(self, ctx):
        soutien_data = await self.bot.db.execute(f"SELECT * FROM soutien WHERE guild_id = {ctx.guild.id}", fetch = True)
        if not soutien_data:
            soutien_data = {"enabled": False, "status": [], "strict": False, "role": 0}
        else:
            soutien_columns = await self.bot.db.get_table_columns("soutien")
            soutien_datas = dict(set(zip(soutien_columns, soutien_data[0])))
            if not soutien_datas["status"]: soutien_datas["status"] = "[]"
            soutien_data = {"enabled": soutien_datas["enabled"], "status": json.loads(soutien_datas["status"]), "strict": soutien_datas["strict"], "role": soutien_datas["role"]}

        async def get_soutien_embed(data, guild):
            embed = discord.Embed(
                title = "Système de soutien",
                color = await self.bot.get_theme(ctx.guild.id),
                description = "*Si vous nous fournissez accidentellement un rôle soutien avec des permissions dangereuses, vous en assumerez la responsabilité.*"
            )

            role = guild.get_role(data["role"])

            embed.add_field(name = "Système mis en place", value = "Oui" if data["enabled"] else "Non")
            embed.add_field(name = "Rôle soutien", value = role.mention if role else "*Aucun rôle configuré*")
            embed.add_field(name = "Stricte égalitée?", value = "Oui" if data["strict"] else "Non")
            embed.add_field(name = "Statut autorisés", value = "\n".join(data["status"]) if data["status"] else "*Aucun status configuré*", inline = False)
            
            return embed
        
        async def delete_message(message):
            async def task():
                try: await message.delete()
                except: pass
            loop = asyncio.get_event_loop()
            loop.create_task(task())

        bot = self.bot
        class ManageSoutien(MyViewClass):
            def __init__(self, soutien_data):
                super().__init__(timeout = 300)
                self.soutien_data = soutien_data

            @discord.ui.select(
                placeholder = "Choisir un paramètre",
                options = [
                    discord.SelectOption(label = "Système mis en place", value = "enabled", emoji = "❔"),
                    discord.SelectOption(label = "Rôle soutien", emoji = "📌", value = "role"),
                    discord.SelectOption(label = "Stricte égalitée", emoji = "💢", value = "strict"),
                    discord.SelectOption(label = "Ajouter un statut autorisé", emoji = "➕", value = "add_status"),
                    discord.SelectOption(label = "Retirer un statut autorisé", emoji = "➖", value = "remove_status"),

                ]
            )
            async def choose_action_select_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if select.values[0] in ["enabled", "strict"]:
                    self.soutien_data[select.values[0]] = not self.soutien_data[select.values[0]]
                    await interaction.message.edit(embed = await get_soutien_embed(self.soutien_data, interaction.guild))
                    await interaction.response.defer()

                if select.values[0] == "role":
                    previous_view = self
                    class ChooseRole(MyViewClass):
                        @discord.ui.select(
                            select_type = discord.ComponentType.role_select,
                            placeholder = "Choisir un rôle"
                        )
                        async def choose_role_select_callback(self, select, interaction):
                            if interaction.user != ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                return
                            
                            role = interaction.guild.get_role(select.values[0].id)
                            
                            if not role:
                                await interaction.response.send_message(f"> Je n'ai pas accès au rôle {role.mention}.", ephemeral = True)
                                return
                            if not role.is_assignable():
                                await interaction.response.send_message(f"> Le rôle {role.mention} n'est pas assignable.", ephemeral = True)
                                return
                            if role.position >= interaction.guild.me.top_role.position:
                                await interaction.response.send_message(f"> Je ne peux pas ajotuer le rôle {role.mention} car il est suppérieur ou égal à mon rôle le plus élevé.", ephemeral = True)
                                return
                            
                            captcha_role_id = await bot.db.get_data("captcha", "non_verified_role", guild_id = interaction.guild.id)
                            if role.id == captcha_role_id:
                                await interaction.response.send_message("> Le rôle soutien ne peut pas être le même que celui des utilisateurs non vérifiés (dans le système de captcha).", ephemeral = True)
                                return
                            
                            previous_view.soutien_data["role"] = role.id
                            await interaction.message.edit(embed = await get_soutien_embed(previous_view.soutien_data, interaction.guild), view = previous_view)
                            await interaction.response.defer()
                            
                        @discord.ui.button(label = "Choisissez un rôle", style = discord.ButtonStyle.primary, disabled = True)
                        async def button_indicator_callback(self, button, interaction):
                            pass

                        @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                        async def button_comback_callback(self, button, interaction):
                            if interaction.user != ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                return
                            
                            await interaction.message.edit(view = previous_view)
                            await interaction.response.defer()

                    await interaction.message.edit(view = ChooseRole(timeout = 180))
                    await interaction.response.defer()
                
                if select.values[0] == "add_status":
                    if len(soutien_data["status"]) >= 25:
                        await interaction.response.send_message("> Vous ne pouvez pas ajouter plus de 25 status autorisés.", ephemeral = True)
                        return
                    
                    await interaction.response.defer()

                    def check_validity(message):
                        return (message.author == ctx.author) and (message.channel == ctx.channel) and (message.content)

                    message = await ctx.send("Quel **statut** souhaitez-vous ajouter?")
                    try: response_message = await bot.wait_for("message", check = check_validity, timeout = 60)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, une minute s'est écoulée.", delete_after = 3)
                        return
                    finally: delete_message(message)
                    delete_message(response_message)

                    if len(response_message.content) > 50:
                        await ctx.send("> Action annulée, le statut donné ne doit pas faire plus de 50 caracètres.", delete_after = 3)
                        return
                    if "\n" in response_message.content:
                        await ctx.send("> Action annulée, le statut donné ne doit pas contenir de retour à la ligne.", delete_after = 3)
                        return
                    
                    self.soutien_data["status"].append(response_message.content)
                    await interaction.message.edit(embed = await get_soutien_embed(self.soutien_data, interaction.guild))

                if select.values[0] == "remove_status":
                    if len(soutien_data["status"]) == 0:
                        await interaction.response.send_message("> Il n'y a pas de status à supprimer.", ephemeral = True)
                        return
                    
                    previous_view = self
                    class ChooseStatusToDelete(MyViewClass):
                        @discord.ui.select(
                            placeholder = "Choisir un status",
                            options = [
                                discord.SelectOption(label = status, value = status) for status in self.soutien_data["status"]
                            ],
                            max_values = len(self.soutien_data["status"])
                        )
                        async def choose_status_to_del_callback(self, select, interaction):
                            if interaction.user != ctx.author:
                                await ctx.send("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                return
                            
                            for value in select.values:
                                if value not in previous_view.soutien_data["status"]:
                                    continue
                                previous_view.soutien_data["status"].remove(value)

                            await interaction.message.edit(embed = await get_soutien_embed(previous_view.soutien_data, interaction.guild), view = previous_view)
                            await interaction.response.defer()

                        @discord.ui.button(label = "Choisissez un status", style = discord.ButtonStyle.primary, disabled = True)
                        async def callback_indication_button(self, button, interaction):
                            pass

                        @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                        async def comeback_button_callback(self, button, interaction):
                            if interaction.user != ctx.author:
                                await ctx.send("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                return
                            
                            await interaction.message.edit(view = previous_view)
                            await interaction.response.defer()

                    await interaction.message.edit(view = ChooseStatusToDelete())
                    await interaction.response.defer()

            @discord.ui.button(label = "Sauvegarder", style = discord.ButtonStyle.success)
            async def save_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if self.soutien_data["enabled"]:
                    if not self.soutien_data["status"]:
                        await interaction.response.send_message("> Vous devez indiquer au moins un statut pour votre système de soutien afin de le sauvegarder.", ephemeral = True)
                        return
                    
                    role = interaction.guild.get_role(self.soutien_data["role"])
                    if not role:
                        await interaction.response.send_message("> Vous devez indiquer un rôle de soutien valide pour sauvegarder.", ephemeral = True)
                        return
                    
                    captcha_role_id = await bot.db.get_data("captcha", "non_verified_role", guild_id = interaction.guild.id)
                    if role.id == captcha_role_id:
                        await interaction.response.send_message("> Le rôle soutien ne peut pas être le même que celui des utilisateurs non vérifiés (dans le système de captcha).", ephemeral = True)
                        return
                
                for data, value in self.soutien_data.items():
                    await bot.db.set_data("soutien", data, value if type(value) != list else json.dumps(value), guild_id = interaction.guild.id)
                
                message_embed = interaction.message.embeds[0]
                message_embed.title = "Système de soutien sauvegardé"

                await interaction.message.edit(embed = message_embed, view = None)
                await interaction.response.defer()

            @discord.ui.button(emoji = "🗑", style = discord.ButtonStyle.danger)
            async def delete_button_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.message.edit(embed = discord.Embed(title = "Configuration du système de soutien annulée", color = await self.bot.get_theme(ctx.guild.id)), view = None)
                await interaction.response.defer()

        await ctx.send(embed = await get_soutien_embed(soutien_data, ctx.guild), view = ManageSoutien(soutien_data = soutien_data))


    @commands.command(description = "Configurer un système de vérification des nouveaux membres")
    @commands.guild_only()
    async def captcha(self, ctx):
        async def get_captcha_embed(data) -> dict:
            embed = discord.Embed(
                title = "Système de vérification",
                description = "*À l'aide de ce panneau de configuration, vous pourrez configurer un bouton (que vous ajouterez à un message du bot) qui permettera la vérification des nouveaux membres.*",
                color = await self.bot.get_theme(ctx.guild.id),
            )

            embed.add_field(name = "Système mis en place", value = "Oui" if data["enabled"] else "Non")
            embed.add_field(name = "Texte du bouton", value = data["button_text"])
            embed.add_field(name = "Emoji du bouton", value = data["button_emoji"] if data["button_emoji"] else "*Aucun emoji (facultatif)*")
            embed.add_field(name = "Couleur du bouton", value = data["button_color"].capitalize())
            embed.add_field(name = "Salon de vérification", value = f"<#{data['channel']}>" if data["channel"] else "*Aucun salon*")
            embed.add_field(name = "Rôle des utilisateurs non vérifiés", value = f"<@&{data['non_verified_role']}>" if data["non_verified_role"] else "*Aucun rôle*")
            embed.add_field(name = "Rôle des utilisateurs vérifiés", value = f"<@&{data['verified_role']}>" if data["verified_role"] else "*Aucun rôle (facultatif)*")

            return embed
        
        guild_data = await self.bot.db.execute(f"SELECT * FROM captcha WHERE guild_id = {ctx.guild.id}", fetch = True)
        if not guild_data:
            data = {
                "enabled": False,
                "button_text": "Vérification",
                "button_emoji": None,
                "button_color": "blurple",
                "channel": None,
                "non_verified_role": None,
                "verified_role": None
            }
        else:
            captcha_table_columns = await self.bot.db.get_table_columns("captcha")
            data = dict(set(zip(captcha_table_columns, guild_data[0])))
    
        class ManageCaptchaView(MyViewClass):
            def __init__(self, ctx, data, bot):
                super().__init__()
                self.ctx = ctx
                self.data = data
                self.bot = bot

            @discord.ui.select(
                placeholder = "Choisir une option",
                options = [
                    discord.SelectOption(label = "Système mis en place", emoji = "❓", value = "enabled"),
                    discord.SelectOption(label = "Texte du bouton", emoji = "📝", value = "button_text"),
                    discord.SelectOption(label = "Emoji du bouton", emoji = "🎭", value = "button_emoji"),
                    discord.SelectOption(label = "Couleur du bouton", emoji = "🎨", value = "button_color"),
                    discord.SelectOption(label = "Salon de vérification", emoji = "🎯", value = "channel"),
                    discord.SelectOption(label = "Rôle des utilisateurs non vérifié", emoji = "🚫", value = "non_verified_role"),
                    discord.SelectOption(label = "Rôle des utilisateurs vérifiés", emoji = "✅", value = "verified_role")
                ]
            )
            async def mange_captcha_select_callback(self, select, interaction):
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if select.values[0] == "enabled":
                    self.data["enabled"] = not self.data["enabled"]
                    await interaction.message.edit(embed = await get_captcha_embed(self.data))
                    await interaction.response.defer()

                if select.values[0].startswith("button"):
                    option_name = [option.label.lower().split(" ")[0] for option in select.options if option.value == select.values[0]][0]
                    
                    await interaction.response.defer()
                    request_message = await self.ctx.send(
                        f"> Quel {option_name} souhaitez-vous définir à votre bouton? Envoyez `cancel` pour annuler."
                        + (" Couleurs disponibles : `bleu`, `rouge`, `vert` et `gris`" if select.values[0] == "button_color" else "")
                        + (" Envoyez `remove` pour retirer l'emoji." if select.values[0] == "button_emoji" else "")
                    )

                    def response_check(message):
                        return (message.author == interaction.user) and (message.channel == interaction.channel) and (message.content)
                    
                    try: response_message = await self.bot.wait_for("message", check = response_check, timeout = 60)
                    except asyncio.TimeoutError():
                        await self.ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                    finally: delete_message(request_message)
                    delete_message(response_message)

                    if response_message.content.lower() == "cancel":
                        await self.ctx.send("> Action annulée.", delete_after = 3)
                        return

                    if select.values[0] == "button_text":
                        if len(response_message.content) > 80:
                            await self.ctx.send("> Action annulée, vous ne pouvez pas définir un texte qui dépasse 80 caractères.", delete_after = 3)
                            return    
                        self.data["button_text"] = response_message.content
                    
                    if select.values[0] == "button_emoji":
                        if response_message.content.lower() == "remove":
                            self.data["button_emoji"] = None
                        else:
                            tools = Tools(self.bot)
                            emoji = await tools.get_emoji(response_message.content)
                            if not emoji:
                                await self.ctx.send("> Action annulée, emoji invalide.", delete_after = 3)
                                return
                            
                            self.data["button_emoji"] = emoji
                    
                    if select.values[0] == "button_color":
                        if response_message.content.lower() in ["bleu", "blue"]:
                            self.data["button_color"] = "blurple"
                        elif response_message.content.lower() in ["rouge", "red"]:
                            self.data["button_color"] = "red"
                        elif response_message.content.lower() in ["vert", "vert"]:
                            self.data["button_color"] = "green"
                        elif response_message.content.lower() in ["gris", "gris"]:
                            self.data["button_color"] = "grey"
                        else:
                            await self.ctx.send("> Action annulée, couleur invalide.", delete_after = 3)
                            return
                    
                    await interaction.message.edit(embed = await get_captcha_embed(self.data))
                        
                if select.values[0] == "channel":
                    manage_captcha_view = self
                    class ChooseChannelView(MyViewClass):
                        @discord.ui.select(
                            select_type = discord.ComponentType.channel_select,
                            placeholder = "Choisissez un salon"
                        )
                        async def choose_channel_select_callback(self, select, interaction):
                            if interaction.user != manage_captcha_view.ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                return
                            
                            channel = interaction.guild.get_channel(select.values[0].id)

                            if not channel:
                                await interaction.response.send_message("> Le salon donné est invalide ou alors je n'y ai pas accès.", ephemeral = True)
                                return
                            
                            if type(channel) != discord.TextChannel:
                                await interaction.response.send_message("> Merci de fournir un salon textuel valide.", ephemeral = True)
                                return

                            manage_captcha_view.data["channel"] = channel.id
                            await interaction.message.edit(view = manage_captcha_view, embed = await get_captcha_embed(manage_captcha_view.data))
                            await interaction.response.defer()
                            
                        @discord.ui.button(label = "Salon de vérification", style = discord.ButtonStyle.primary, disabled = True)
                        async def indication_button_callback(self, button, interaction):
                            pass

                        @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                        async def comeback_button_callback(self, button, interaction):
                            if interaction.user != manage_captcha_view.ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", delete_after = 3)
                                return

                            await interaction.message.edit(view = manage_captcha_view)
                            await interaction.response.defer()  
                        
                    await interaction.message.edit(view = ChooseChannelView())
                    await interaction.response.defer()
                        
                if "role" in select.values[0]:
                    manage_captcha_view = self
                    manage_captcha_select = select
                    option_name = [option.label for option in select.options if option.value == select.values[0]][0]

                    class ChooseRoleView(MyViewClass):
                        @discord.ui.select(
                            placeholder = "Choisissez un rôle",
                            select_type = discord.ComponentType.role_select
                        )    
                        async def choose_role_select_callback(self, select, interaction):
                            if interaction.user != manage_captcha_view.ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", delete_after = 3)
                                return
                            
                            role_id = select.values[0].id

                            join_roles = await manage_captcha_view.bot.db.get_data("guild", "join_roles", True, guild_id = interaction.guild.id)
                            if role_id in join_roles:
                                await interaction.response.send_message("> Vous ne pouvez pas choisir un rôle qui est parmis les rôles automatiquements ajoutés aux nouveaux membres.", ephemeral = True)
                                return
                            
                            soutien_role = await manage_captcha_view.bot.db.get_data("soutien", "role", guild_id = interaction.guild.id)
                            if role_id == soutien_role:
                                await interaction.response.send_message("> Vous ne pouvez pas choisir un rôle ayant définis comme rôle soutien.", ephemeral = True)
                                return
                            
                            role = interaction.guild.get_role(role_id)
                            if not role:
                                await interaction.response.send_message(f"> Le rôle donné n'éxiste plus ou alors je n'y ai plus accès.", ephemeral = True)
                                return
                            
                            if not role.is_assignable():
                                await interaction.response.send_message(f"> Le rôle {role.mention} n'est pas assignable.", ephemeral = True)
                                return
                            
                            if role.position >= interaction.guild.me.top_role.position:
                                await interaction.response.send_message("> Je ne peux pas ajouter un rôle qui est suppérieur ou égal hiérarchiquement à mon rôle le plus élevé.", ephemeral = True)
                                return
                            
                            manage_captcha_view.data[manage_captcha_select.values[0]] = role_id
                            await interaction.message.edit(embed = await get_captcha_embed(manage_captcha_view.data), view = manage_captcha_view)
                            await interaction.response.defer()
                            
                        @discord.ui.button(label = option_name, style = discord.ButtonStyle.primary, disabled = True)
                        async def indication_button_callback(self, button, interaction):
                            pass

                        @discord.ui.button(label = "Retirer", emoji = "❌")
                        async def remove_role_button_callback(self, button, interaction):
                            if interaction.user != manage_captcha_view.ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", delete_after = 3)
                                return
                            
                            if not manage_captcha_view.data[manage_captcha_select.values[0]]:
                                await interaction.response.send_message(f"> Vous n'avez pas définis de **{option_name.lower()}**.", ephemeral = True)
                                return

                            manage_captcha_view.data[manage_captcha_select.values[0]] = None
                            await interaction.message.edit(embed = await get_captcha_embed(manage_captcha_view.data), view = manage_captcha_view)
                            await interaction.response.defer()

                        @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                        async def comeback_button_callback(self, button, interaction):
                            if interaction.user != manage_captcha_view.ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", delete_after = 3)
                                return

                            await interaction.message.edit(view = manage_captcha_view)
                            await interaction.response.defer()  

                    await interaction.message.edit(view = ChooseRoleView())
                    await interaction.response.defer()

            @discord.ui.button(label = "Confirmer", emoji = "✅")
            async def save_button_callback(self, button, interaction):
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if not self.data["enabled"]:
                    for key, value in self.data.items():
                        if key == "guild_id": continue
                        await self.bot.db.set_data("captcha", key, value, guild_id = interaction.guild.id)
                    await interaction.message.edit(
                        embed = discord.Embed(title = "Paramètres du système de vérification sauvegardé", color = await self.bot.get_theme(interaction.guild.id)),
                        view = None
                    )
                    await interaction.response.defer()
                    return
                
                # -------------------------- Vérification des valeurs obligatoires à vérifier ---------------------------------
                gived_channel = interaction.guild.get_channel(self.data["channel"])
                if not gived_channel:
                    await interaction.response.send_message("> Merci de fournir un salon de vérification valide.", ephemeral = True)
                    return
                
                non_verified_role = interaction.guild.get_role(self.data["non_verified_role"])
                if not non_verified_role:
                    await interaction.response.send_message("> Merci de fournir un rôle valide pour les utilisateurs non vérifiés.", ephemeral = True)
                    return
                
                # -------------------------- Désactivation des bouttons et du sélecteur du ManageCaptchaView (afin d'empêcher le spam de confirmation)
                for children in self.children:
                    children.disabled = True
                async def restore():
                    for children in self.children:
                        children.disabled = False
                    await interaction.message.edit(view = self)

                await interaction.message.edit(view = self)
                await interaction.response.defer()

                # -------------------------- Demande à l'utilisateur le lien du message sur lequel il y'aura la bouton de vérfication
                def response_check(message):
                    return (message.author == interaction.user) and (message.channel == interaction.channel) and (message.content)
                message = None
                while not message:
                    ask_message = await self.ctx.send(f"> Quel est le **lien ou l'identifiant du message** auquel vous souhaitez ajouter le bouton? Le message doit être un message du bot, ne doit pas contenir de bouton/sélecteur (vous pouvez utiliser `{ctx.clean_prefix}clearcomponents <message>` pour retirer les boutons/sélécteurs d'un message) et doit être dans le salon <#{self.data['channel']}>. Envoyez `cancel` pour annuler cette action.")
                    try: response_message = await self.bot.wait_for("message", check = response_check, timeout = 60)
                    except asyncio.TimeoutError():
                        await self.ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                        await restore()
                        return

                    finally: delete_message(ask_message)
                    delete_message(response_message)

                    if response_message.content.lower() == "cancel":
                        await self.ctx.send("> Action annulée.", delete_after = 3)
                        await restore()
                        return
                    
                    content = response_message.content.removeprefix(f"https://discord.com/channels/{interaction.guild.id}/{self.data['channel']}/")
                    if not content.isdigit():
                        await self.ctx.send("> Lien invalide.", delete_after = 3)
                        continue

                    content = int(content)
                    channel = interaction.guild.get_channel(self.data['channel'])
                    if not channel:
                        await self.ctx.send("> Le salon de vérification donné ne m'est plus disponible, la configuration est donc annulée.", delete_after = 3)
                        await restore()
                        return
                    
                    try: message = await channel.fetch_message(content)
                    except:
                        await self.ctx.send("> Lien invalide.", delete_after = 3)
                        continue

                    if message.author != interaction.guild.me:
                        await self.ctx.send("> Je ne suis pas l'auteur du message donné.", delete_after = 3)
                        message = None
                        continue

                    if message.components:
                        await self.ctx.send("> Le message donné contient un/des sélécteur(s)/bouton(s).", delete_after = 3)
                        message = None
                        continue
            
                # -------------------------- Demander à l'utilisateur s'il souhaite une configuration automatique de son système de vérification
                manage_captcha_view = self
                previous_message = message

                async def get_data_validity():
                    try: message = await previous_message.channel.fetch_message(previous_message.id)
                    except:
                        return "> Configuration annulée, le message précédement fourni n'est plus disponible.", None, None, False
                    
                    try: non_verified_role = interaction.guild.get_role(manage_captcha_view.data["non_verified_role"])
                    except:
                        return "> Configuration annulée, le rôle (pour les utilisateurs non vérifiés) précédement fourni n'est plus disponible.", None, None, False
                    
                    try: verification_channel = interaction.guild.get_channel(manage_captcha_view.data["channel"])
                    except:
                        return "> Configuration annulée, le salon de vérification n'est plus disponible.", None, None, False

                    return message, non_verified_role, verification_channel, True

                class AutoConfig(MyViewClass):
                    @discord.ui.button(emoji = "✅")
                    async def launch_autoconfig_callback(self, button, interaction):
                        if interaction.user != manage_captcha_view.ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        # -------------------------- Vérification de la validité des valeurs
                        message, non_verified_role, verification_channel, successfull = await get_data_validity()
                        if not successfull:
                            await interaction.response.send_message(message, ephemeral = True)
                            await interaction.message.edit(view = None)
                            return

                        captcha_view = discord.ui.View(timeout = None)
                        captcha_view.add_item(discord.ui.Button(label = manage_captcha_view.data["button_text"], emoji = manage_captcha_view.data["button_emoji"], style = getattr(discord.ButtonStyle, manage_captcha_view.data["button_color"]), custom_id = "captcha_verify"))
                        try: await message.edit(view = captcha_view)
                        except:
                            await interaction.message.edit(embed = discord.Embed(title = "Configuration annulée, Impossible d'ajouter le bouton de vérification au message précédement donné.", color = await manage_captcha_view.bot.get_theme(interaction.guild.id)), view = None)
                            await interaction.response.defer()
                            return
                        
                        for key, value in manage_captcha_view.data.items():
                            if key == "guild_id": continue
                            await manage_captcha_view.bot.db.set_data("captcha", key, value, guild_id = interaction.guild.id)
                        await manage_captcha_view.bot.db.set_data("captcha", "auto_config", True, guild_id = interaction.guild.id)
                        
                        await interaction.message.edit(
                            embed = discord.Embed(
                                title = "Configuration automatique des permissions en cours...",
                                color = await manage_captcha_view.bot.get_theme(interaction.guild.id)
                            ),
                            view = None
                        )
                        await interaction.response.defer()

                        for channel in interaction.guild.channels:
                            if type(channel) == discord.CategoryChannel: continue
                            if (not channel.permissions_for(interaction.guild.default_role).view_channel) and (channel.id != verification_channel.id): continue

                            if channel.id == verification_channel.id:
                                if channel.permissions_for(interaction.guild.default_role).view_channel:
                                    channel_overwrites = channel.overwrites_for(interaction.guild.default_role)
                                    channel_overwrites.view_channel = False
                                    await channel.set_permissions(interaction.guild.default_role, overwrite = channel_overwrites, reason = f"[{interaction.user.display_name} - {interaction.user.id}] Configuration automatique des permissions de captcha")
                                
                                if not channel.permissions_for(non_verified_role).view_channel:
                                    await channel.set_permissions(non_verified_role, view_channel = True, reason = f"[{interaction.user.display_name} - {interaction.user.id}] Configuration automatique des permissions de captcha")

                                continue
                            
                            if channel.permissions_for(non_verified_role).view_channel:
                                try: await channel.set_permissions(non_verified_role, view_channel = False, reason = f"[{interaction.user.display_name} - {interaction.user.id}] Configuration automatique des permissions de captcha")
                                except: pass
                        
                        await interaction.message.edit(embed = discord.Embed(title = "Configuration automatique des permissions terminé", color = await manage_captcha_view.bot.get_theme(interaction.guild.id)), view = None) 
                        await manage_captcha_view.ctx.send(interaction.user.mention, embed = discord.Embed(title = "Votre système de vérification des nouveaux membres est prêt", color = await manage_captcha_view.bot.get_theme(interaction.guild.id)))
                        
                    @discord.ui.button(emoji = "❌")
                    async def no_autoconfig_callback(self, button, interaction):
                        if interaction.user != manage_captcha_view.ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return 
                        
                        message, _, _, successfull = await get_data_validity()
                        if not successfull:
                            await interaction.response.send_message(message, ephemeral = True)
                            await interaction.message.edit(view = None)
                            return
                        
                        for key, value in manage_captcha_view.data.items():
                            if key == "guild_id": continue
                            await manage_captcha_view.bot.db.set_data("captcha", key, value, guild_id = interaction.guild.id)
                        await manage_captcha_view.bot.db.set_data("captcha", "auto_config", False, guild_id = interaction.guild.id)

                        await interaction.message.edit(embed = discord.Embed(title = "Votre système de vérification des nouveaux membres est prêt", color = await manage_captcha_view.bot.get_theme(interaction.guild.id)), view = None)
                        await interaction.response.defer()
                        
                await interaction.message.edit(
                    embed = discord.Embed(
                        title = "Configuration recommandée",
                        description = f"***Souhaitez-vous configurer automatiquement les permissions du rôle <@&{manage_captcha_view.data['non_verified_role']}> et des salons de ce serveur ?***\n\nLe processus consiste à masquer tous les salons pour les nouveaux membres non vérifiés, à l'exception du salon de vérification. Une fois la vérification terminée, les salons masqués deviennent accessibles aux utilisateurs vérifiés, tandis que le salon de vérification leur est ensuite rendu invisible (les nouveaux salons seront automatiquements configurés).\n\n*Notez que les salons actuellement invisibles pour @everyone ne seront pas affectés par cette configuration.*",
                        color = await manage_captcha_view.bot.get_theme(interaction.guild.id)
                    ),
                    view = AutoConfig()
                )
                
            @discord.ui.button(emoji = "🗑", style = discord.ButtonStyle.danger)
            async def delete_button_callback(self, button, interaction):
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.message.edit(embed = discord.Embed(title = "Configuration du système de vérification annulée", color = await self.bot.get_theme(ctx.guild.id)), view = None)
                await interaction.response.defer()
        
        await ctx.send(embed = await get_captcha_embed(data), view = ManageCaptchaView(ctx, data, self.bot))


    @commands.command(description = "Configurer l'envoi automatique de message de bienvenue")
    @commands.guild_only()
    async def joins(self, ctx):
        async def get_join_data() -> dict:
            results = await self.bot.db.execute(f"SELECT * FROM joins WHERE guild_id = {ctx.guild.id}", fetch = True)
            if not results:
                return {
                    "enabled": False,
                    "channel": 0,
                    "message": "Bienvenue {MemberMention}",
                    "message_dm_enabled": False,
                    "message_dm": None,
                    "embed": {},
                    "send_after_captcha": False
                }
            
            joins_columns = await self.bot.db.get_table_columns("joins")
            return dict(set(zip(joins_columns, results[0])))
        
        async def get_join_embed(data : dict) -> discord.Embed:
            bot_prefix = await self.bot.get_prefix(ctx.message)

            embed = discord.Embed(
                title = "Paramètres de bienvenue",
                color = await self.bot.get_theme(ctx.guild.id),
                description = 
                "***Commandes qui ne pourraient que vous êtres utiles***\n"
                + f"> `{bot_prefix}variables`\n"
                + f"> `{bot_prefix}joinrole <add/del/reset/list> [role]`\n"
                + f"> `{bot_prefix}ghostping <add/del/reset/list> [channel]`"
            )

            channel = ctx.guild.get_channel(data["channel"])
            embed.add_field(name = "Système mis en place", value = "Oui" if data["enabled"] else "Non")
            embed.add_field(name = "Salon", value = f"<#{channel.id}>" if data["channel"] else "*Aucun salon valide*")
            embed.add_field(
                name = "Message",
                value = (
                    data["message"]
                    if (len(data["message"]) <= 500) 
                    else (data["message"][:500] + f"... (et {len(data['message']) - 500} caractères)")
                ) if data["message"] else "*Aucun message configuré*"
            )
            embed.add_field(name = "Envoi d'un MP", value = "Activé" if data["message_dm_enabled"] else "Désactivé")
            embed.add_field(
                name = "Message en MP", 
                value = (
                    data["message_dm"] if (len(data["message_dm"]) <= 500)
                    else (data["message_dm"][:500] + f"... (et {len(data['message_dm']) - 500} caractères)")
                ) if data["message_dm"] else "*Aucun message configuré*"
            )
            embed.add_field(name = "Embed", value = "Configuré" if len(await self.bot.db.get_data("joins", "embed", False, True, guild_id = ctx.guild.id)) else "Non configuré")
            embed.add_field(name = "Envoi après vérification", value = "Activé" if data["send_after_captcha"] else "Désactivé")

            return embed
        
        class JoinSettings(MyViewClass):
            def __init__(self, data : dict, bot):
                super().__init__()
                self.data = data
                self.bot = bot

            @discord.ui.select(
                placeholder = "Choisir une option",
                options = [
                    discord.SelectOption(label = "Système mis en place", emoji = "⏳", value = "enabled"),
                    discord.SelectOption(label = "Salon", emoji = "📌", value = "channel"),
                    discord.SelectOption(label = "Message", emoji = "💬", value = "message"),
                    discord.SelectOption(label = "Envoi d'un MP", emoji = "📩", value = "message_dm_enabled"),
                    discord.SelectOption(label = "Message en MP", emoji = "💭", value = "message_dm"),
                    discord.SelectOption(label = "Ajouter un embed", emoji = "📝", value = "embed"),
                    discord.SelectOption(label = "Retirer l'embed", emoji = "❌", value = "del_embed"),
                    discord.SelectOption(label = "Envoi après vérification", emoji = "🔒", value = "send_after_captcha")
                ]
            )
            async def join_settings_select_callback(self, select : discord.SelectMenu, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                def response_check(message):
                    return (message.author == interaction.user) and (message.channel == interaction.channel) and (message.content)
          
                if select.values[0] == "channel":
                    await interaction.response.defer()

                    message = await ctx.send("> Dans quel **salon** souhaitez-vous envoyer le message de bienvenue? Envoyez `cancel` pour annuler.")
                    try: response = await self.bot.wait_for("message", check = response_check, timeout = 60)
                    except asyncio.TimeoutError():
                        await ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                        return
                    except: return
                    finally: delete_message(message)
                    delete_message(response)

                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 3)
                        return
                    
                    searcher = Searcher(self.bot, ctx)
                    channel = await searcher.search_channel(response.content, interaction.guild)

                    if not channel:
                        await ctx.send("> Action annulée, merci de fournir un salon valide.", delete_after = 3)
                        return
                    
                    self.data["channel"] = channel.id
                    await interaction.message.edit(embed = await get_join_embed(self.data))

                if select.values[0] in ["message", "message_dm"]:
                    await interaction.response.defer()

                    option_name = [option for option in select.options if option.value == select.values[0]][0].label.lower()
                    message = await ctx.send(f"> Quel sera le nouveau contenu de votre **{option_name}** ? Envoyez `cancel` pour annuler et `remove` pour retirer le contenu actuel.")

                    try: response = await self.bot.wait_for("message", check = response_check, timeout = 60)
                    except asyncio.TimeoutError():
                        await ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                        return
                    finally: delete_message(message)
                    delete_message(response)

                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 3)
                        return

                    if response.content.lower() == "remove":
                        self.data[select.values[0]] = None
                    else:
                        if len(response.content) > 2000:
                            await ctx.send(f"> Votre **{option_name}** ne peut pas dépasser les 2000 caractères.", delete_after = 3)
                            return
                        
                        self.data[select.values[0]] = response.content

                    await interaction.message.edit(embed = await get_join_embed(self.data))
                
                if select.values[0] in ["enabled", "message_dm_enabled", "send_after_captcha"]:
                    self.data[select.values[0]] = not self.data[select.values[0]]
                    await interaction.message.edit(embed = await get_join_embed(self.data))
                    await interaction.response.defer()

                if select.values[0] == "embed":
                    await interaction.response.send_message(textwrap.dedent("""
                        **Configurer un embed de bienvenue est un jeu d'enfant. Suivez simplement ces étapes :**

                        1. **Lancez la commande `+embed`.**
                        2. **Personnalisez votre embed** grâce au menu interactif qui s'affiche.
                        3. **Appuyez sur le bouton "Envoyer"** pour finaliser votre création.
                        4. **Cliquez sur "Définir comme embed de bienvenue"** pour l'appliquer.
                        5. **Et voilà, votre configuration est terminée.**
                    """), ephemeral = True)

                if select.values[0] == "del_embed":
                    await self.bot.db.set_data("joins", "embed", None, guild_id = interaction.guild.id)
                    await interaction.message.edit(embed = await get_join_embed(self.data))
                    await interaction.response.defer()

            @discord.ui.button(label = "Sauvegarder", style = discord.ButtonStyle.success)
            async def save_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if self.data["enabled"]:
                    if (not self.data["channel"]) and (not interaction.guild.get_channel(self.data["channel"])):
                        await interaction.response.send_message("> Merci de donner un salon de bienvenue valide.", ephemeral = True)
                        return
                    if not interaction.guild.get_channel(self.data["channel"]).permissions_for(interaction.guild.me).send_messages:
                        await interaction.response.send_message(f"> Je n'ai pas les permissions nécessaires pour envoyer des messages dans le salon <#{self.data['channel']}>", ephemeral = True)
                        return
                    
                    if self.data["message_dm_enabled"]:
                        if not self.data["message_dm"]:
                            await interaction.response.send_message("> Vous avez activé l'envoi de message privé, donc vous devez fournir un message à envoyer.", ephemeral = True)
                            return
                        
                    embed_enabled = len(await self.bot.db.get_data("joins", "embed", False, True, guild_id = interaction.guild.id))
                    if (not embed_enabled) and (not self.data["message"]):
                        await interaction.response.send_message("> Vous devez fournir un message de bienvenue ou alors un embed de bienvenue.", ephemeral = True)
                        return

                for key, value in self.data.items():
                    if key in ["guild_id", "embed"]: continue
                    await self.bot.db.set_data("joins", key, value, guild_id = interaction.guild.id)
                
                embed = await get_join_embed(self.data)
                embed.title = "Paramètres de bienvenue sauvegardés"
                await interaction.message.edit(
                    embed = embed,
                    view = None
                )
                await interaction.response.defer()

            @discord.ui.button(emoji = "🗑", style = discord.ButtonStyle.danger)
            async def delete_button_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.message.edit(embed = discord.Embed(title = "Configuration du système de bienvenue annulé", color = await self.bot.get_theme(ctx.guild.id)), view = None)
                await interaction.response.defer()

        data = await get_join_data()
        await ctx.send(embed = await get_join_embed(data), view = JoinSettings(data, self.bot))


    @commands.command(description = "Configurer l'envoi automatique de message d'adieu")
    @commands.guild_only()
    async def leaves(self, ctx):
        async def get_leaves_data() -> dict:
            leaves_data = await self.bot.db.execute(f"SELECT * FROM leaves WHERE guild_id = {ctx.guild.id}", fetch = True)
            if not leaves_data:
                return {
                    "enabled": False,
                    "channel": None,
                    "message": "Aurevoir {MemberMention}"
                }
            
            leaves_table_columns = await self.bot.db.get_table_columns("leaves")
            leaves_data = dict(set(zip(leaves_table_columns, leaves_data[0])))
            return leaves_data

        async def get_leaves_embed(data) -> discord.Embed:
            embed = discord.Embed(
                title = "Paramètres d'adieu",
                color = await self.bot.get_theme(ctx.guild.id),
                description = f"*Vous pouvez vous aider de la commande `{ctx.clean_prefix}variables` pour voir les variables disponibles.*"
            )

            embed.add_field(name = "Système mis en place", value = "Oui" if data["enabled"] else "Non")
            embed.add_field(name = "Salon", value = f"<#{data['channel']}>" if data["channel"] else "*Aucun salon configuré*")
            embed.add_field(
                name = "Message",
                value = (
                    data["message"]
                    if (len(data["message"]) <= 500) 
                    else (data["message"][:500] + f"... (et {len(data['message']) - 500} caractères)")
                ) if data["message"] else "*Aucun message configuré*"
            )
            embed.add_field(name = "Embed", value = "Configuré" if len(await self.bot.db.get_data("leaves", "embed", False, True, guild_id = ctx.guild.id)) else "Non configuré")
            return embed

        class ChangeLeavesSettings(MyViewClass):
            def __init__(self, bot, data: dict):
                super().__init__(timeout = 180)
                self.bot = bot
                self.data = data

            @discord.ui.select(
                placeholder = "Choisir une option",
                options = [
                    discord.SelectOption(label = "Système mis en place", emoji = "❔", value = "enabled"),
                    discord.SelectOption(label = "Salon", emoji = "📌", value = "channel"),
                    discord.SelectOption(label = "Message", emoji = "💬", value = "message"),
                    discord.SelectOption(label = "Ajouter un embed", emoji = "📝", value = "add_embed"),
                    discord.SelectOption(label = "Retirer l'embed", emoji = "❌", value = "remove_embed")
                ]
            )
            async def leaves_select_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                def response_check(message):
                    return (message.author == interaction.user) and (message.channel == interaction.channel) and (message.content)

                if select.values[0] == "channel":
                    await interaction.response.defer()

                    message = await ctx.send("> Dans quel **salon** souhaitez-vous envoyer le message d'adieu? Envoyez `cancel` pour annuler.")
                    try: response = await self.bot.wait_for("message", check = response_check, timeout = 60)
                    except asyncio.TimeoutError():
                        await ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                        return
                    except: return
                    finally: delete_message(message)
                    delete_message(response)

                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 3)
                        return
                    
                    searcher = Searcher(self.bot, ctx)
                    channel = await searcher.search_channel(response.content, interaction.guild)

                    if not channel:
                        await ctx.send("> Action annulée, merci de fournir un salon valide.", delete_after = 3)
                        return
                    
                    self.data["channel"] = channel.id
                    await interaction.message.edit(embed = await get_leaves_embed(self.data))

                if select.values[0] == "message":
                    await interaction.response.defer()

                    message = await ctx.send(f"> Quel sera le nouveau contenu de votre **message d'adieu** ? Envoyez `cancel` pour annuler et `remove` pour retirer le contenu actuel.")

                    try: response = await self.bot.wait_for("message", check = response_check, timeout = 60)
                    except asyncio.TimeoutError():
                        await ctx.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                        return
                    finally: delete_message(message)
                    delete_message(response)

                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 3)
                        return

                    if response.content.lower() == "remove":
                        self.data["message"] = None
                    else:
                        if len(response.content) > 2000:
                            await ctx.send(f"> Votre **message d'adieu** ne peut pas dépasser les 2000 caractères.", delete_after = 3)
                            return
                        self.data["message"] = response.content

                    await interaction.message.edit(embed = await get_leaves_embed(self.data))
                
                if select.values[0] == "enabled":
                    self.data["enabled"] = not self.data["enabled"]
                    await interaction.message.edit(embed = await get_leaves_embed(self.data))
                    await interaction.response.defer()

                if select.values[0] == "add_embed":
                    await interaction.response.send_message(textwrap.dedent("""
                        **Configurer un embed d'adieu est un jeu d'enfant. Suivez simplement ces étapes :**

                        1. **Lancez la commande `+embed`.**
                        2. **Personnalisez votre embed** grâce au menu interactif qui s'affiche.
                        3. **Appuyez sur le bouton "Envoyer"** pour finaliser votre création.
                        4. **Cliquez sur "Définir comme embed d'adieu"** pour l'appliquer.
                        5. **Et voilà, votre configuration est terminée.**
                    """), ephemeral = True)

                if select.values[0] == "remove_embed":
                    await self.bot.db.set_data("leaves", "embed", None, guild_id = interaction.guild.id)
                    await interaction.message.edit(embed = await get_leaves_embed(self.data))
                    await interaction.response.defer()

            @discord.ui.button(label = "Sauvegarder", style = discord.ButtonStyle.success)
            async def save_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if self.data["enabled"]:
                    if (not self.data["channel"]) and (not interaction.guild.get_channel(self.data["channel"])):
                        await interaction.response.send_message("> Merci de donner un salon de d'adieu valide.", ephemeral = True)
                        return
                    if not interaction.guild.get_channel(self.data["channel"]).permissions_for(interaction.guild.me).send_messages:
                        await interaction.response.send_message(f"> Je n'ai pas les permissions nécessaires pour envoyer des messages dans le salon <#{self.data['channel']}>", ephemeral = True)
                        return
                        
                    embed_enabled = len(await self.bot.db.get_data("leaves", "embed", False, True, guild_id = interaction.guild.id))
                    if (not embed_enabled) and (not self.data["message"]):
                        await interaction.response.send_message("> Vous devez fournir un message d'adieu ou alors un embed d'adieu.", ephemeral = True)
                        return

                for key, value in self.data.items():
                    if key in ["guild_id", "embed"]: continue
                    await self.bot.db.set_data("leaves", key, value, guild_id = interaction.guild.id)
                
                embed = await get_leaves_embed(self.data)
                embed.title = "Paramètres d'adieu sauvegardés"
                await interaction.message.edit(
                    embed = embed,
                    view = None
                )
                await interaction.response.defer()

            @discord.ui.button(emoji = "🗑", style = discord.ButtonStyle.danger)
            async def delete_button_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.message.edit(embed = discord.Embed(title = "Configuration du système d'adieu annulé", color = await self.bot.get_theme(ctx.guild.id)), view = None)
                await interaction.response.defer()


        leaves_data = await get_leaves_data()
        await ctx.send(embed = await get_leaves_embed(leaves_data), view = ChangeLeavesSettings(self.bot, leaves_data))


    @commands.command(description = "Configurer l'ajout automatique d'un rôle lors de l'ajout d'une réaction sur un message", usage = "<add/del/list/reset> <emoji> <role> <message>")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles = True)
    async def rolereact(self, ctx, action : str, emoji : str = None, role : discord.Role = None, message : discord.Message = None):
        action = action.lower()
        if action not in ["add", "del", "list", "reset"]:
            await ctx.send(f"> L'action donnée est invalide. Les actions disponibles sont : `add`/`del`/`list`/`reset`.")
            return
        if (action in ["add", "del"]) and ((not emoji) or (not role) or (not message)):
            await ctx.send("> Si votre action est \"add\" ou \"del\", alors tous les paramètres de la commande deviennent obligatoires.")
            return
        
        if (action in ["add", "del"]):
            tools = Tools(self.bot)
            emoji = await tools.get_emoji(emoji)
            if not emoji:
                await ctx.send(f"> L'emoji donné est invalide.")
                return
        
        if action != "add":
            roles_react_data_sql = await self.bot.db.execute(f"SELECT * FROM role_react WHERE guild_id = {ctx.guild.id}", fetch = True)
            if not roles_react_data_sql:
                await ctx.send("> Il n'y a pas de role-react configuré sur ce serveur.")
                return
        
        # ------------------------------------- ACTION : LIST
        if action == "list": 
            role_react_table_columns = await self.bot.db.get_table_columns("role_react")
            roles_react_data = [dict(set(zip(role_react_table_columns, role_react_data))) for role_react_data in roles_react_data_sql] 
            roles_react_data = [
                f"{index}. <#{role_react_data['channel_id']}> > [Lien du message](https://discord.com/channels/{role_react_data['guild_id']}/{role_react_data['channel_id']}/{role_react_data['message_id']}) : {role_react_data['emoji']} : <@&{role_react_data['role']}>" for index, role_react_data in enumerate(roles_react_data)
            ]

            embed = discord.Embed(
                title = "Liste des role-react",
                color = await self.bot.get_theme(ctx.guild.id),
                description = "\n".join(roles_react_data)
            )
            await ctx.send(embed = embed)

        # ------------------------------------- ACTION : RESET
        if action == "reset":
            await self.bot.db.execute(f"DELETE FROM role_react WHERE guild_id = {ctx.guild.id}")
            await ctx.send("> Le système de role-react a correctement été supprimés.")

        # ------------------------------------- ACTION : ADD ROLE REACT
        if action == "add":
            already_exists = await self.bot.db.execute(f"SELECT * FROM role_react WHERE guild_id = %s AND channel_id = %s AND message_id = %s AND emoji = %s", (ctx.guild.id, message.channel.id, message.id, str(emoji),), fetch = True)
            if already_exists:
                await ctx.send("> Il éxiste déjà un role-react comme cela.")
                return
            
            gp_checker = GPChecker(ctx, self.bot)
            check = await gp_checker.we_can_add_role(role)
            if check != True:
                await ctx.send(check, allowed_mentions = AM.none())
                return
            
            await self.bot.db.execute("INSERT INTO role_react (guild_id, channel_id, message_id, emoji, role) VALUES (%s, %s, %s, %s, %s)", (ctx.guild.id, message.channel.id, message.id, str(emoji), role.id))
            
            try: await message.add_reaction(emoji)
            except: pass

            await ctx.send("> Votre role-react a bien été créé.")
        
        # ------------------------------------- ACTION : DEL ROLE REACT
        if action == "del":
            await self.bot.db.execute(f"DELETE FROM role_react WHERE guild_id = {ctx.guild.id} AND channel_id = {message.channel.id} AND message_id = {message.id} AND emoji = {emoji}")
            await ctx.send("> Le role-react donné a bien été supprimé.")


    @commands.command(description = "Gérer l'ajout de rôles à l'aide de boutons/sélécteurs")
    @commands.guild_only()
    async def roleinteract(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Configuration(bot))