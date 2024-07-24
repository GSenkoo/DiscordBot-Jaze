import discord
import json
import asyncio
from discord.ui.item import Item
from discord.ext import commands
from discord import AllowedMentions as AM
from utils.Paginator import PaginatorCreator
from utils.Searcher import Searcher
from utils.MyViewClass import MyViewClass
from utils.Tools import Tools


class Configurations(commands.Cog):
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
        

        async def delete_message(message):
            async def task():
                try: await message.delete()
                except: pass
            loop = asyncio.get_event_loop()
            loop.create_task(task())

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
                    finally: await delete_message(message)
                    await delete_message(response)

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
                    finally: await delete_message(message)
                    await delete_message(response_message)

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
                
                
                for data, value in self.soutien_data.items():
                    await bot.db.set_data("soutien", data, value if type(value) != list else json.dumps(value), guild_id = interaction.guild.id)
                
                message_embed = interaction.message.embeds[0]
                message_embed.title = "Système de soutien sauvegardé"

                await interaction.message.edit(embed = message_embed, view = None)
                await interaction.response.defer()

        await ctx.send(embed = await get_soutien_embed(soutien_data, ctx.guild), view = ManageSoutien(soutien_data = soutien_data))
    


def setup(bot):
    bot.add_cog(Configurations(bot))