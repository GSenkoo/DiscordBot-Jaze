import discord
import json
import asyncio
from discord import AllowedMentions as AM
from discord.ext import commands
from utils.GPChecker import GPChecker
from utils.Tools import Tools
from utils.Paginator import PaginatorCreator
from datetime import datetime, timedelta


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.command(description = "Voir et gérer les sanctions d'un membre")
    @commands.guild_only()
    async def sanctions(self, ctx, user : discord.User = None):
        if not user: user = ctx.author

        paginator_creator = PaginatorCreator()

        sanctions = await self.bot.db.get_data("member", "sanctions", guild_id = ctx.guild.id, user_id = user.id)

        if not sanctions or not json.loads(sanctions):
            await ctx.send(f"> Le membre {user.mention} n'a pas de sanction.", allowed_mentions = AM.none())
            return
        
        """
        Sanctions format : 
        
        {
            "type": "sanction_type",
            "moderator": moderator_id,
            "timestamp": sanction_timestamp_id,
            "reason": "sanction_reason"
        }
        """

        type_converter = {
            "warn": "Avertissement",
            "derank": "Retrait des rôles",
            "ban": "Bannissement",
            "kick": "Expulsion",
            "tempmute": "Exclusion temporaire",
            "blrank": "Blrank",
            "blvoc": "Blvoc"
        }
        
        sanctions = json.loads(sanctions)
        sanctions_formated = []
        for index in range(len(sanctions)):
            sanction_data = sanctions[index]
            sanctions_formated.append(
                f"{index + 1}. <t:{sanction_data['timestamp']}:d> : {type_converter[sanction_data['type']]} "
                + (f"de `{sanction_data['time']}` " if sanction_data['type'] == "tempmute" else "")
                + f" par <@{sanction_data['moderator']}> "
                + (f"pour `{sanction_data['reason']}`" if sanction_data['reason'] else "")
            )

        custom_select = []
        bot = self.bot
        for index in range(0, len(sanctions), 10):
            class EditSanctions(discord.ui.View):
                async def on_timeout(self) -> None:
                    if self.to_components != self.message.components:
                        return
                    
                    try: await self.message.edit(view = None)
                    except: pass

                @discord.ui.select(
                    placeholder = "Choisir une sanction à supprimer",
                    options = [
                        discord.SelectOption(
                            label = str(i + 1),
                            emoji = "🗑",
                            value = str(i)
                        ) for i in range(index, index + 10 if len(sanctions) > index + 10 else len(sanctions))
                    ]
                )
                async def edit_sanction_select_callback(self, select, interaction):
                    if interaction.user != ctx.author:
                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                        return
                    
                    user_sanctions = json.loads(await bot.db.get_data("member", "sanctions", guild_id = interaction.guild.id, user_id = user.id))
                    
                    if not len(user_sanctions) > int(select.values[0]):
                        await interaction.response.send_message(f"> La sanction n°{select.values[0]} n'éxiste plus.", ephemeral = True)
                        return
                    
                    user_sanctions.pop(int(select.values[0]))
                    await bot.db.set_data("member", "sanctions", json.dumps(user_sanctions), guild_id = interaction.guild.id, user_id = user.id)
                    
                    await interaction.response.defer()
                    await interaction.message.edit(
                        embed = discord.Embed(
                            author = discord.EmbedAuthor(name = user.display_name, icon_url = user.avatar.url if user.avatar else None),
                            color = await bot.get_theme(interaction.guild.id),
                            description = f"*Sanction n°{int(select.values[0]) + 1} supprimée.*"    
                        ),
                        view = None
                    )
                    

                @discord.ui.button(label = "Tout supprimer", style = discord.ButtonStyle.danger, row = 4)
                async def delete_all_button_callback(self, button, interaction):
                    if interaction.user != ctx.author:
                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                        return
                    
                    await bot.db.set_data("member", "sanctions", json.dumps([]), guild_id = interaction.guild.id, user_id = user.id)

                    await interaction.response.defer()
                    await interaction.message.edit(
                        embed = discord.Embed(
                            title = "Sanctions",
                            author = discord.EmbedAuthor(name = user.display_name, icon_url = user.avatar.url if user.avatar else None),
                            color = await bot.get_theme(interaction.guild.id),
                            description = f"*Sanctions supprimées par {ctx.author.mention}*"
                        ),
                        view = None
                    )

            custom_select.append(EditSanctions(timeout = 300))
        
        paginator = await paginator_creator.create_paginator(
            title = "Sanctions",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = sanctions_formated,
            without_button_if_onepage = False,
            custom_rows = custom_select,
            timeout = 180,
            embed_author = discord.EmbedAuthor(name = user.display_name, icon_url = user.avatar.url if user.avatar else None)
        )

        await paginator.send(ctx)


    @commands.command(description = "Bannir un membre du serveur")
    @commands.cooldown(rate = 5, per = 60, type = commands.BucketType.guild)
    @commands.bot_has_permissions(ban_members = True)
    @commands.guild_only()
    async def ban(self, ctx, user : discord.User, *, reason = None):
        checker = GPChecker(ctx, self.bot)
        tools = Tools(self.bot)

        try:
            member = await ctx.guild.fetch_member(user.id)
        except: member = None

        check = await checker.we_can_ban(user, member)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return

        banned_users = []
        async for banned in ctx.guild.bans():
            banned_users.append(banned.user.id)

        if user.id in banned_users:
            await ctx.send(f"> **{user.display_name}** est déjà banni du serveur.", allowed_mentions = AM.none())
            return
        
        if reason: log_reason = log_reason = f"[{ctx.author.display_name} - {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} - {ctx.author.id}] Aucune raison specifiée"

        try: await ctx.guild.ban(user, reason = log_reason if len(log_reason) <= 50 else log_reason[:47] + "...")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative de bannissement de {user.mention}.", allowed_mentions = AM.none())
            return
        
        await tools.add_sanction("ban", ctx, user, reason)
        await ctx.send(f"> L'utilisateur **{user}** a été banni du serveur" + ("." if not reason else f" pour `" + (reason.replace("`", "'") if len(reason) <= 50 else reason.replace("`", "'")[:47] + "...") + "`."), allowed_mentions = AM.none()) 


    @commands.command(description = "Débannir un membre du serveur")
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members = True)
    @commands.cooldown(rate = 5, per = 60, type = commands.BucketType.guild)
    async def unban(self, ctx, user : discord.User):
        banned_users = []
        async for banned in ctx.guild.bans():
            banned_users.append(banned.user)
        
        if user not in banned_users:
            await ctx.send(f"> L'utilisateur **{user.display_name}** n'est pas banni du serveur.", allowed_mentions = AM.none())
            return
        
        try: await ctx.guild.unban(user, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande de débannissement")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative de débannissement, merci de réessayer.")
            return
        
        await ctx.send(f"> L'utilisateur **{user}** a été débanni du serveur.")

    
    @commands.command(description = "Débannir tous les utilisateurs banni")
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members = True)
    async def unbanall(self, ctx):
        unbanned = 0
        total_banned = 0
        banned_users = await ctx.guild.bans().flatten()
        
        if not banned_users:
            await ctx.send("> Sur ce serveur, il n'y a pas d'utilisateur banni.")
            return
        
        message = await ctx.send("> Débannissement des utilisateurs banni en cours...")

        for ban_entry in banned_users:
            total_banned += 1
            try: await ctx.guild.unban(ban_entry.user, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande de débanissement de tous les utilisateurs bannis")
            except: continue
            unbanned += 1

        try: await message.delete()
        except: pass

        await ctx.send("> Tentative de débannissement de tous les utilisateurs banni effectué." + (f"\n> Je compte un total de {unbanned} utilisateur(s) débanni. " if unbanned else "") + (f"\n> Je n'ai pas pu bannir {total_banned - unbanned} utilisateurs." if total_banned - unbanned else ""))

    
    @commands.command(description = "Kick un membre du serveur")
    @commands.cooldown(rate = 5, per = 60, type = commands.BucketType.guild)
    @commands.bot_has_permissions(kick_members = True)
    @commands.guild_only()
    async def kick(self, ctx, member : discord.Member, *, reason = None):
        checker = GPChecker(ctx, self.bot)
        tools = Tools(self.bot)

        check = await checker.we_can_kick(member)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        if reason: log_reason = f"[{ctx.author.display_name} - {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} - {ctx.author.id}] Aucune raison specifiée"

        try: await member.kick(reason = log_reason if len(log_reason) <= 50 else log_reason[:50] + "...")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative d'expulsion de {member.mention}.", allowed_mentions = AM.none())
            return
        
        await tools.add_sanction("kick", ctx, member, reason)
        await ctx.send(f"> {member.mention} a été expulsé du serveur" + ("." if not reason else f" pour `" + (reason.replace("`", "'") if len(reason) <= 50 else reason.replace("`", "'")[:47] + "...") + "`."), allowed_mentions = AM.none())


    @commands.command(description = "Temporairement mute un membre avec le système d'exclusion")
    @commands.bot_has_permissions(moderate_members = True)
    @commands.guild_only()
    async def tempmute(self, ctx, member : discord.Member, duration : str, *, reason : str = None):
        """
        Voici des exemples d'utilisation :
        `+tempmute @user123 3j` (mute 3 jours)
        `+tempmute @user123 10s` (mute 10 secondes)
        `+tempmute @user123 10jours` (mute 10 jours)
        `+tempute @user123 10m` (mute 10 minutes)
        `+tempmute @user123 10h` (mute 10h)

        Note : La durée maximum de mute est de 28 jours.
        """
        checker = GPChecker(ctx, self.bot)
        tools = Tools(self.bot)

        check = await checker.we_can_tempmute(member)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return

        duration_timedelta = await tools.find_duration(duration)
        if not duration_timedelta:
            await ctx.send(f"> La durée donnée est invalide, voici quelques exemples de durées valides : `5h`, `7minutes`, `3days`, `2secondes`, `7jours`.")
            return
        if duration_timedelta.days > 28:
            await ctx.send("> La durée maximale de timeout discord est limitée à 28 jours, vous ne pouvez donc pas dépasser cette limite.")
            return
        
        if reason: log_reason = f"[{ctx.author.display_name} - {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} - {ctx.author.id}] Aucune raison fournie"
        
        try:
            await member.timeout_for(duration_timedelta, reason = log_reason if len(log_reason) <= 50 else log_reason[:47] + "...")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative de tempmute de {member.mention}.", allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> {member.mention} a été tempmute `{duration}`" + ("." if not reason else (" pour `" + (reason if len(reason) <= 50 else reason[:47] + "...") + "`")))
        await tools.add_sanction("tempmute", ctx, member, reason, duration)


    @commands.command(description = "Unmute un membre ayant été mute avec le système d'exclusion")
    @commands.bot_has_permissions(moderate_members = True)
    @commands.guild_only()
    async def untempmute(self, ctx, member : discord.Member, reason : str = None):
        checker = GPChecker(ctx, self.bot)

        check = await checker.we_can_untempmute(member)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        if reason: log_reason = f"[{ctx.author.display_name} - {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} - {ctx.author.id}] Aucune raison fournie"

        try: await member.remove_timeout(reason = log_reason)
        except:
            await ctx.send("> Une erreur s'est produite lors de la tentive de untempmute.")
            return
        
        await ctx.send(f"> Le membre {member.mention} a été untempmute" + ("." if not reason else " pour `" + reason.replace("`", "'") + "`.") , allowed_mentions = AM.none())
        try: await member.send(
            f"> Vous avez été untempmute manuellement du serveur **{ctx.guild.name}** par **{ctx.author.display_name}**"
            + ("." if not reason else " pour `" + (reason.replace("`", "'") if len(reason) <= 50 else reason[:47] + "...") + "`.")
        )
        except: pass

    
    @commands.command(description = "Retirer tous les rôles d'un membre")
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles = True)
    async def derank(self, ctx, member : discord.Member, *, reason : str = None):
        checker = GPChecker(ctx, self.bot)
        tools = Tools(self.bot)

        check = await checker.we_can_derank(member)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return

        noderank_roles = await self.bot.db.get_data("guild", "noderank_roles", guild_id = ctx.guild.id)
        if not noderank_roles:
            noderank_roles = "[]"
        noderank_roles = json.loads(noderank_roles)


        member_roles = [role for role in member.roles if (role.is_assignable()) and (role.id not in noderank_roles)]

        try: await member.remove_roles(*member_roles, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande de derank")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative de derank de {member.mention}.", allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> Le membre {member.mention} a été derank" + (f" pour `" + reason.replace("`", "'") + "`." if reason else "."), allowed_mentions = AM.none())
        await tools.add_sanction("derank", ctx, member, reason)


    @commands.command(description = "Ajouter un rôle à un membre")
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles = True)
    async def addrole(self, ctx, role : discord.Role, member : discord.Member = None):
        """
        Note: les utilisateurs avec la permission owner peuvent ajouter n'importe quel rôle si ils ont accès à la commande.
        """
        if not member:
            member = ctx.author

        checker = GPChecker(ctx, self.bot)
        check = await checker.we_can_add_role(member, role)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        try: await member.add_roles(role, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande d'ajout de rôle")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative d'ajout du rôle {role.mention}.", allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> Le rôle {role.mention} " + ("vous a été ajouté" if member == ctx.author else f"a été ajouté à {member.mention}") + ".", allowed_mentions = AM.none())


    @commands.command(description = "Retirer un rôle à un utilisateur", aliases = ["removerole"])
    @commands.bot_has_permissions(manage_roles = True)
    @commands.guild_only()
    async def delrole(self, ctx, role : discord.Role, member : discord.Role = None):
        """
        Note: les utilisateurs avec la permission owner peuvent retirer n'importe quel rôle.
        """
        if not member:
            member = ctx.author

        checker = GPChecker(ctx, self.bot)
        check = await checker.we_can_remove_role(member, role)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        await member.remove_roles(role, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande d'enlèvement de rôle")
        await ctx.send(f"> Le rôle {role.mention} " + ("vous a été retiré" if member == ctx.author else f"a été retiré à {member.mention}") + ".", allowed_mentions = AM.none())


    @commands.command(description = "Ajouter un avertissement à un membre")
    @commands.guild_only()
    async def warn(self, ctx, member : discord.Member, *, reason : str = None):
        checker = GPChecker(ctx, self.bot)
        tools = Tools(self.bot)

        check = await checker.we_can_warn(member)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> {member.mention} a été warn" + ("." if not reason else f" pour `" + (reason.replace("`", "'") if len(reason) <= 50 else reason[:47].replace("`", "'") + "...") + "`."), allowed_mentions = AM.none())
        await tools.add_sanction("warn", ctx, member, reason)

    
    @commands.command(description = "Supprimer un certains nombre de message")
    @commands.bot_has_permissions(manage_messages = True)
    @commands.guild_only()
    async def clear(self, ctx, count : int, user : discord.User = None):
        clear_limit = await self.bot.db.get_data("guild", "clear_limit", guild_id = ctx.guild.id)

        if not 1 <= count <= clear_limit:
            await ctx.send(f"> Votre nombre de message à supprimer doit être entre 1 et {clear_limit}.")
            return
        
        await ctx.message.delete()
        def message_check(message):
            if user: return message.author == user
            return True
        
        await ctx.channel.purge(
            limit = count,
            check = message_check,
            reason = f"[{ctx.author.display_name} - {ctx.author.id}] Suppression de {count} messages" + (f" appartenants à {user.display_name}" if user else "")
        )

    
    @commands.command(description = "Déconnecter un membre d'un salon vocal")
    @commands.bot_has_guild_permissions(move_members = True)
    async def deco(self, ctx, member : discord.Member):
        if not member.voice:
            await ctx.send("> " + (f"{member.mention} n'est" if member != ctx.author else "Vous n'êtes") + " pas dans un salon vocal.", allowed_mentions = AM.none())
            return

        await member.move_to(None, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande de deco")
        await ctx.send("> " + (f"Le membre {member.mention} a" if member != ctx.author else "Vous avez") + " été déconnecté.", allowed_mentions = AM.none())

    @commands.command(description = "Déconnecter tous les membres actuellement dans un salon vocal.")
    @commands.bot_has_guild_permissions(move_members = True)
    async def cleanup(self, ctx, channel : discord.VoiceChannel):
        if not channel.members:
            await ctx.send(f"> Il n'y a personne dans le salon {channel.mention}.")
            return

        for member in channel.members:
            await member.move_to(None, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande de cleanup")
        await ctx.send(f"> Tous les membres du salon {channel.mention} ont étés déconnectés.", allowed_mentions = AM.none())
    
    @commands.command(description = "Déplacer un membre dans un salon vocal")
    @commands.bot_has_guild_permissions(move_members = True)
    async def bring(self, ctx, member : discord.Member, channel : discord.VoiceChannel):
        if not member.voice:
            await ctx.send("> " + (f"{member.mention} n'est" if member != ctx.author else "Vous n'êtes") + " pas dans un salon vocal.")
            return
        if member.voice.channel == channel:
            await ctx.send("> " + (f"{member.mention} est" if member != ctx.author else "Vous êtes") + f" déjà dans le salon {channel.mention}.")
            return
        
        await member.move_to(channel, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande de bring vers le salon #{channel.name}")
        await ctx.send("> " + (f"Le membre {member.mention} a" if member != ctx.author else "Vous avez") + f" été déplacé vers le salon {channel.mention}.", allowed_mentions = AM.none())        

    
    @commands.command(description = "Déplacer tous les membres en vocals vers un salon vocal")
    @commands.bot_has_guild_permissions(move_members = True)
    async def bringall(self, ctx, channel : discord.VoiceChannel):
        moved_members = 0
        for _channel in ctx.guild.channels:
            if type(_channel) != discord.VoiceChannel: continue
            if not _channel.members: continue
            if _channel == channel: continue

            for member in _channel.members:
                try:
                    await member.move_to(channel, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande de bringall vers le salon #{channel.name}")
                    moved_members += 1
                except: pass

        if not moved_members:
            await ctx.send("> Il n'y aucun membre actuellement dans un salon vocal.")
            return
        
        if moved_members != 1: await ctx.send(f"> Un total de **{moved_members}** membres ont étés déplacé vers le salon {channel.mention}.")
        else: await ctx.send(f"> Un membre a été déplacé vers le salon {channel.mention}.")


    @commands.command(description = "Empêcher un membre de recevoir des rôles qui ne sont pas noderank", usage = "<add/del/list> [member] [reason]")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles = True)
    async def blrank(self, ctx, action, member : discord.Member = None, *, reason : str = None):
        checker = GPChecker(ctx, self.bot)
        paginator_creator = PaginatorCreator()
        tools = Tools(self.bot)

        if action not in ["add", "del", "list"]:
            await ctx.send(f"> Action invalide, voici un rappel d'utilisation : `{await self.bot.get_prefix(ctx.message)}blrank <add/del/list> [member] [reason]`.")
            return
        
        if (action != "list") and (not member):
            await ctx.send("> Si votre action n'est pas \"list\", alors le paramètre `member` devient obligatoire.")
            return

        blrank_users = await self.bot.db.get_data("guild", "blrank_users", True, guild_id = ctx.guild.id)

        if action == "list":
            blrank_users = [f"<@{user}>" for user in blrank_users]

            paginator = await paginator_creator.create_paginator(
                title = "Membres blrank",
                embed_color = await self.bot.get_theme(ctx.guild.id),
                data_list = blrank_users,
                no_data_message = "*Aucun utilisateur blrank*"
            )

            if type(paginator) == list: await ctx.send(embed = paginator[0])
            else: await paginator.send(ctx)
            
            return
        
        check = await checker.we_can_blrank(member, action)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return

        if action == "add": blrank_users.append(member.id)
        else: blrank_users.remove(member.id)

        await ctx.send(f"> Le membre {member.mention} " + ("ne pourras désormais plus recevoir de rôle n'étant pas noderank" if action == "add" else "pourra désormais recevoir n'importe quel rôle") + ("." if not reason else " pour `" + (reason if len(reason) <= 50 else reason[:47] + "...") + "`" + "."), allowed_mentions = AM.none())
        await self.bot.db.set_data("guild", "blrank_users", json.dumps(blrank_users), guild_id = ctx.guild.id)

        # ------------------ Deletes the roles
        if action != "add": 
            return

        noderank_roles = await self.bot.db.get_data("guild", "noderank_roles", True, guild_id = ctx.guild.id)

        roles_to_remove = [role for role in member.roles if (not role.is_assignable()) or (role.id in noderank_roles)]
        for role in roles_to_remove:
            try: member.remove_roles(role, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande de blrank")
            except: pass

        # ------------------ Add sanctions
        await tools.add_sanction("blrank", ctx, member, reason)



    @commands.command(description = "Empêcher un membre de recevoir des rôles qui ne sont pas noderank", usage = "<add/del/list> [member] [reason]")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles = True)
    async def blvoc(self, ctx, action, member : discord.Member = None, *, reason : str = None):
        checker = GPChecker(ctx, self.bot)
        paginator_creator = PaginatorCreator()
        tools = Tools(self.bot)

        if action not in ["add", "del", "list"]:
            await ctx.send(f"> Action invalide, voici un rappel d'utilisation : `{await self.bot.get_prefix(ctx.message)}blvoc <add/del/list> [member] [reason]`.")
            return
        
        if (action != "list") and (not member):
            await ctx.send("> Si votre action n'est pas \"list\", alors le paramètre `member` devient obligatoire.")
            return

        blvoc_users = await self.bot.db.get_data("guild", "blvoc_users", True, guild_id = ctx.guild.id)

        if action == "list":
            blvoc_users = [f"<@{user}>" for user in blvoc_users]

            paginator = await paginator_creator.create_paginator(
                title = "Membres blvoc",
                embed_color = await self.bot.get_theme(ctx.guild.id),
                data_list = blvoc_users,
                no_data_message = "*Aucun utilisateur blvoc*"
            )

            if type(paginator) == list: await ctx.send(embed = paginator[0])
            else: await paginator.send(ctx)
            
            return

        check = await checker.we_can_blvoc(member, action)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return

        if action == "add": blvoc_users.append(member.id)
        else: blvoc_users.remove(member.id)

        await ctx.send(f"> Le membre {member.mention} " + ("ne pourras désormais plus rejoindre de salon vocal" if action == "add" else "pourra désormais rejoindre n'import quel salon vocal") + (("." if not reason else " pour `" + (reason if len(reason) <= 50 else reason[:47] + "...") + "`" + ".") if action == "add" else "."), allowed_mentions = AM.none())
        await self.bot.db.set_data("guild", "blvoc_users", json.dumps(blvoc_users), guild_id = ctx.guild.id)

        # ------------------ Remove from voice
        if action != "add": 
            return
        
        if member.voice:
            await member.move_to(None, reason = f"[{ctx.author.display_name} - {ctx.author.id}] Demande de blvoc")

        # ------------------ Add sanctions
        await tools.add_sanction("blvoc", ctx, member, reason)


def setup(bot):
    bot.add_cog(Moderation(bot))