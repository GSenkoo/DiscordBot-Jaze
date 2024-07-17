import discord
import json
import asyncio
import emoji
from discord.ext import commands
from discord import AllowedMentions as AM
from utils.Paginator import PaginatorCreator
from utils.Searcher import Searcher


class MyViewClass(discord.ui.View):
    def __init__(self):
        super().__init__(timeout = 180)
    
    async def on_timeout(self) -> None:
        try: message = await self.message.channel.fetch_message(self.message.id)
        except: return

        def check_is_equal(components1, components2):
            if len(components1) != len(components2):
                return False
            for index in range(len(components1)):
                if len(components1[index]["components"]) != len(components2[index]["components"]):
                    return False
                for index2 in range(len(components1[index]["components"])):
                    if components1[index]["components"][index2]["custom_id"] != components2[index]["components"][index2]["custom_id"]:
                        return False
            return True
        
        message_components = [component.to_dict() for component in message.components]
        
        if check_is_equal(message_components, self.to_components()):
            try: await message.edit(view = None)
            except: pass


class Configurations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Définir les rôles qui ne seront pas retirés lors des derank et blrank", usage = "<add/del/reset/view> [role]")
    @commands.guild_only()
    async def noderank(self, ctx, action : str, role : discord.Role = None):
        if action.lower() not in ["add", "del", "view", "reset"]:
            await ctx.send(f"> Action invalide, voici un rappel d'utilisation : `{await self.bot.get_prefix(ctx.message)}noderank <add/del/reset/view> [role]`.")
            return
        
        if (action.lower() not in ["view", "reset"]) and (not role):
            await ctx.send("> Si votre action n'est pas \"view\" ou \"reset\", alors le paramètre `role` devient obligatoire.")
            return

        noderank_roles = await self.bot.db.get_data("guild", "noderank_roles", True, guild_id = ctx.guild.id)

        if action.lower() == "view":
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


    @commands.command(description = "Ajouter/Supprimer des salons où les membres seront mentionné à l'arrivée", usage = "<add/del/reset/view> [channel]")
    @commands.guild_only()
    async def ghostping(self, ctx, action : str, channel : discord.TextChannel = None):
        if action.lower() not in ["add", "del", "view", "reset"]:
            await ctx.send(f"> Action invalide, rappel d'utilisation de la commande : `{await self.bot.get_prefix(ctx.message)}ghostping <add/del/reset/view> [channel]`")
            return
        
        if not channel:
            channel = ctx.channel
        
        ghostping_channels = await self.bot.db.get_data("guild", "ghostping_channels", True, guild_id = ctx.guild.id)
        if action.lower() == "view":
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

    
    @commands.command(description = "Définir des rôles qui seront automatiquements ajoutés aux nouveaux membres", usage = "<add/del/reset/view> [role]")
    @commands.guild_only()
    async def joinrole(self, ctx, action, role : discord.Role = None):
        if action.lower() not in ["add", "del", "view", "reset"]:
            await ctx.send(f"> Action invalide, rappel d'utilisation de la commande : `{await self.bot.get_prefix(ctx.message)}joinrole <add/del/reset/view> [role]`")
            return

        if (action.lower() in ["add", "del"]) and (not role):
            await ctx.send("> Si votre action est \"add\" ou \"del\", le paramètre `role` devient obligatoire.")
            return
        
        join_roles = await self.bot.db.get_data("guild", "join_roles", True, guild_id = ctx.guild.id)
        if action.lower() == "view":
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

    
    @commands.command(description = "Configurer les paramètres de suggestion")
    @commands.guild_only()
    async def suggestions(self, ctx):
        suggestions_found = await self.bot.db.execute(f"SELECT * FROM suggestions WHERE guild_id = {ctx.guild.id}", fetch = True)
        searcher = Searcher(self.bot, ctx)

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
                "channel": ctx.channel.id, "confirm_channel": suggestion_current_data["confirm_channel"],
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
                

                def get_emoji(query):
                    if emoji.is_emoji(query):
                        return query
                    
                    query = query.split(":")
                    if len(query) != 3:
                        return None
                    
                    query = query[2].replace(">", "")
                    try: query = bot.get_emoji(int(query))
                    except: return None
                    return query
                
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
                    found_emoji = get_emoji(response.content)
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




def setup(bot):
    bot.add_cog(Configurations(bot))