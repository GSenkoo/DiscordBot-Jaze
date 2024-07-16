import discord
import json
from discord.ext import commands
from discord import AllowedMentions as AM
from utils.Paginator import PaginatorCreator


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
        suggestions_found = await self.bot.db.execute(f"SELECT * FROM suggestions WHERE guild_id = {ctx.guild.id}")
        """"
                "channel": "BIGINT DEFAULT 0",
                "confirm_channel": "BIGINT DEFAULT 0",
                "denied_channel": "BITINT DEFAULT 0",
                "moderator_roles": "VARCHAR(237) DEFAULT '[]'",
                "enabled
        """
        if not suggestions_found:
            suggestion_data = {
                "channel": ctx.channel.id, "confirm_channel": None,
                "denied_channel": None, "moderator_roles": [],
                "enabled": False, "for_emoji": "✅", "against_emoji": "❌"
            }
        else:
            suggesiton_columns = await self.bot.db.get_columns("suggestions")
            suggestion_current_data = dict(set(zip(suggesiton_columns, suggestions_found[0])))
            suggestion_data = {
                "channel": ctx.channel.id, "confirm_channel": suggestion_current_data["confirm_channel"],
                "denied_channel": suggestion_current_data["denied_channel"], "moderator_roles": json.loads(suggestion_current_data["moderator_roles"]),
                "enabled": suggestion_current_data["enabled"], "for_emoji": suggestion_current_data["for_emoji"], "against_emoji": suggestion_current_data["against_emoji"]
            }
        
        async def get_suggestion_settings_embed(data : dict):
            embed = discord.Embed(
                title = "Paramètres de suggestions",
                color = await self.bot.get_theme(ctx.guild.id),
                description = "*Si aucun salon de confirmation ou de refus n'est donné, alors les suggestions ne seront pas vérifiés.* "
                + "*Les utilisateurs avec la permission owner, le propriétaire et ceux ayant accès à cette commande peuvent confirmer les suggestions sans avoir à avoir un rôle modérateur.*"
            )

            embed.add_field(name = "Statut", value = "Activé" if data["enabled"] else "Désactivé")
            embed.add_field(name = "Salon de suggestion", value = f"<#{data['channel']}>" if data['channel'] else "*Aucun salon*")
            embed.add_field(name = "Salon de confirmation", value = f"<#{data['confirm_channel']}>" if data['confirm_channel'] else "*Aucun salon*")
            embed.add_field(name = "Salon de refus", value = f"<#{data['denied_channel']}>" if data['denied_channel'] else "*Aucun salon*")
            embed.add_field(name = "Emoji \"pour\"", value = data["for_emoji"])
            embed.add_field(name = "Emoji \"contre\"", value = data["against_emoji"])
            embed.add_field(name = "Rôles modérateurs", value = "<#" + ">\n<#".join(data['moderator_roles']) + ">" if data['moderator_roles'] else "*Aucun rôles modérateurs*")

            return embed
        

        class Suggestions(discord.ui.View):
            async def on_timeout(self):
                try: await self.message.edit(view = None)
                except: pass

            @discord.ui.select(
                placeholder = "Modifier un paramètre",
                options = [
                    discord.SelectOption(label = "Statut des suggestions", emoji = "⏳", value = "enabled"),
                    discord.SelectOption(label = "Salon de suggestion", emoji = "💡", value = "channel"),
                    discord.SelectOption(label = "Salon de confirmation", emoji = "🔎", value = "confirm_channel"),
                    discord.SelectOption(label = "Salon de refus", emoji = "🚫", value = "denied_channel"),
                    discord.SelectOption(label = "Emoji \"pour\"", emoji = "✅", value = "for_emoji"),
                    discord.SelectOption(label = "Emoji \"contre\"", emoji = "❌", value = "against_emoji"),
                    discord.SelectOption(label = "Ajouter un rôle modérateur", emoji = "➕", value = "add_moderator_roles"),
                    discord.SelectOption(label = "Supprimer un rôle modérateur", emoji = "➖", value = "remove_moderator_roles")
                ]
            )
            async def select_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.response.defer()

            
            @discord.ui.button(label = "Sauvegarder", style = discord.ButtonStyle.primary)
            async def button_save_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.response.defer()
                
                # message de sauvegarde : > Modifications sauvegardés, 3 changements ont étés effectués.
                

        await ctx.send(embed = await get_suggestion_settings_embed(suggestion_data), view = Suggestions(timeout = 600))




def setup(bot):
    bot.add_cog(Configurations(bot))