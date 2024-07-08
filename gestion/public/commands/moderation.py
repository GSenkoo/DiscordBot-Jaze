import discord
import json
import asyncio
from discord import AllowedMentions as AM
from discord.ext import commands
from utils.Database import Database
from datetime import datetime, timedelta


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Bannir un membre du serveur")
    @commands.cooldown(rate = 5, per = 60)
    @commands.bot_has_permissions(ban_members = True)
    @commands.guild_only()
    async def ban(self, ctx, user : discord.User, *, reason = None):
        try:
            member = await ctx.guild.fetch_member(user.id)
        except: member = None

        if member:
            if member == ctx.author:
                await ctx.send("> Vous ne pouvez pas vous auto-bannir du serveur.")
                return
            if member == ctx.guild.owner:
                await ctx.send("> Vous ne pouvez pas bannir le propriétaire du serveur.")
                return
            if ctx.author != ctx.guild.owner:
                if member.top_role.position >= ctx.author.top_role.position:
                    await ctx.send("> Vous ne pouvez pas bannir un membre qui est suppérieur ou égal à vous hiérarchiquement.")
                    return
            if member.top_role.position >= ctx.guild.me.top_role.position:
                await ctx.send(f"> Je ne peux pas bannir {member.mention} car il est suppérieur ou égal à moi hiérarchiquement", allowed_mentions = AM.none())
                return
        
        bans = await ctx.guild.bans()
        banned_users = []
        if bans: banned_users = [usr.id for usr in bans]

        if user.id in banned_users:
            await ctx.send(f"> **{user.display_name}** est déjà banni du serveur.", allowed_mentions = AM.none())
            return
        
        if reason: log_reason = log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] Aucune raison specifiée"

        try: await ctx.guild.ban(user, reason = log_reason if len(log_reason) <= 512 else log_reason[:509] + "...")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative de bannissement de {member.mention}.", allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> {member.mention} a été banni du serveur" + ("." if not reason else f" pour `" + (reason.replace("`", "'") if len(reason) <= 500 else reason.replace("`", "'")[:497] + "...") + "`."), allowed_mentions = AM.none()) 

    
    @commands.command(description = "Kick un membre du serveur")
    @commands.cooldown(rate = 5, per = 60)
    @commands.bot_has_permissions(kick_members = True)
    @commands.guild_only()
    async def kick(self, ctx, member : discord.Member, *, reason = None):
        if member == ctx.author:
            await ctx.send("> Vous ne pouvez pas vous auto-kick du serveur.")
            return
        if member == ctx.guild.owner:
            await ctx.send("> Vous ne pouvez pas kick le propriétaire du serveur.")
            return
        if ctx.author != ctx.guild.owner:
            if member.top_role.position >= ctx.author.top_role.position:
                await ctx.send("> Vous ne pouvez pas kick un membre qui est suppérieur ou égal à vous hiérarchiquement.")
                return
        if member.top_role.position >= ctx.guild.me.top_role.position:
            await ctx.send(f"> Je ne peux pas kick {member.mention} car il est suppérieur ou égal à moi hiérarchiquement", allowed_mentions = AM.none())
            return
        
        if reason: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] Aucune raison specifiée"

        try: await member.kick(reason = log_reason if len(log_reason) <= 512 else log_reason[:509] + "...")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative d'expulsion de {member.mention}.", allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> {member.mention} a été expulsé du serveur" + ("." if not reason else f" pour `" + (reason.replace("`", "'") if len(reason) <= 500 else reason.replace("`", "'")[:497] + "...") + "`."), allowed_mentions = AM.none())


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
        if member == ctx.author:
            await ctx.send("> Vous ne pouvez pas vous auto-tempmute.")
            return
        if member.guild_permissions.administrator:
            await ctx.send("> Vous ne pouvez pas mute un utilisateur administrateur.")
            return
        if member.top_role.position >= ctx.author.top_role.position:
            await ctx.send("> Vous ne pouvez pas tempmute un utilisateur qui suppérieur ou égal à vous hiérarchiquement.")
            return
        if member.top_role.position >= ctx.guild.me.top_role.position:
            await ctx.send("> Je ne peux pas tempmute un utilisateur qui est suppérieur ou égal à moi hiérarchiquement.")
            return

        def find_duration(duration):
            duration_test = duration.replace("days", "").replace("day", "").replace("jours", "").replace("jour", "").replace("d", "").replace("j", "")
            if duration_test.isdigit():
                return timedelta(days = int(duration_test))
            
            duration_test = duration.replace("hours", "").replace("hour", "").replace("hours", "").replace("hour", "").replace("h", "")
            if duration_test.isdigit():
                return timedelta(hours = int(duration_test))
            
            duration_test = duration.replace("minutes", "").replace("minute", "").replace("min", "").replace("m", "")
            if duration_test.isdigit():
                return timedelta(minutes = int(duration_test))
            
            duration_test = duration.replace("secondes", "").replace("seconde", "").replace("seconds", "").replace("second", "").replace("sec", "").replace("s", "")
            if duration_test.isdigit():
                return timedelta(seconds = int(duration_test))

            return None
            

        duration_timedelta = find_duration(duration)
        if not duration_timedelta:
            await ctx.send(f"> La durée donnée est invalide, voici quelques exemples de durées valides : `5h`, `7minutes`, `3days`, `2secondes`, 7jours`.")
            return
        if duration_timedelta.days > 28:
            await ctx.send("> La durée maximale de timeout discord est limitée à 28 jours, vous ne pouvez donc pas dépasser cette limite.")
            return
        
        if reason: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] Aucune raison fournie"
        
        try:
            await member.timeout_for(duration_timedelta, reason = log_reason if len(log_reason) <= 512 else log_reason[:509] + "...")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative de tempmute de {member.mention}.", allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> {member.mention} a été tempmute `{duration}`" + (" pour " + reason.replace("`", "'") if len(reason) <= 500 else reason.replace("")))
        
    
    @commands.command(description = "Retirer tous les rôles d'un membre")
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles = True)
    async def derank(self, ctx, member : discord.Member):
        if member == ctx.author:
            await ctx.send("> Vous ne pouvez pas vous auto-derank.")
            return
        if member == ctx.guild.owner:
            await ctx.send("> Le propriétaire du serveur ne peut pas être derank.")
            return
        if member.top_role.position >= ctx.author.top_role.position:
            await ctx.send("> Vous ne pouvez pas derank un utilisateur suppérieur ou égal à vous hiérarchiquement.")
            return
        if member.top_role.position >= ctx.guild.me.top_role.position:
            await ctx.send("> Je ne peux pas derank un utilisateur suppérieur ou égal à moi hiérarchiquement.")
            return
        
        member_roles = [role for role in member.roles if role.is_assignable()]

        try: await member.remove_roles(*member_roles, reason = f"[{ctx.author.display_name} | {ctx.author.id}] Demande de derank")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative de derank de {member.mention}.", allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> Le membre {member.mention} a été derank.", allowed_mentions = AM.none())


    @commands.command(description = "Ajouter un rôle à un membre")
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles = True)
    async def addrole(self, ctx, role : discord.Role, member : discord.Member = None):
        """
        Note: les utilisateurs avec la permission owner peuvent ajouter n'importe quel rôle si ils ont accès à la commande.
        """
        if not member:
            member = ctx.author

        if not role.is_assignable():
            await ctx.send(f"> Le rôle {role.mention} n'est pas un rôle assignable.")
            return
        
        if role in getattr(member, "roles", []):
            await ctx.send("> " + ("Vous avez" if member == ctx.author else f"{member.mention} a") + f" déjà le rôle {role.mention}.", allowed_mentions = AM.none())
            return

        db = Database()
        await db.connect()
        owners = await db.get_data("guild", "owners", guild_id = ctx.guild.id)
        await db.disconnect()

        if owners: owners = json.loads(owners)
        else: owners = []

        if (ctx.author.id not in owners) and (ctx.author != ctx.guild.owner):
            if ctx.author.top_role.position <= role.position:
                await ctx.send("> Vous ne pouvez ajouter un rôle suppérieur ou égal hiérarchiquement à votre rôle le plus élevé.")
                return
        
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send("> Je ne peux pas ajouter un rôle qui est suppérieur ou égal hiérarchiquement à mon rôle le plus élevé.")
            return
        
        try: await member.add_roles(role, reason = f"[{ctx.author.display_name} | {ctx.author.id}] Demande d'ajout de rôle")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative d'ajout du rôle {role.mention}.", allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> Le rôle {role.mention} " + ("vous a été ajouté" if member == ctx.author else f"a été ajouté à {member.mention}") + ".", allowed_mentions = AM.none())
        

    @commands.command(description = "Retirer un rôle à un utilisateur", aliases = ["removerole"])
    @commands.guild_only()
    async def delrole(self, ctx, role : discord.Role, member : discord.Role = None):
        """
        Note: les utilisateurs avec la permission owner peuvent retirer n'importe quel rôle.
        """
        if not member:
            member = ctx.author

        if not role.is_assignable():
            await ctx.send(f"> Le rôle {role.mention} ne peut pas être retiré.")
            return

        db = Database()
        await db.connect()
        owners = await db.get_data("guild", "owners", guild_id = ctx.guild.id)
        await db.disconnect()

        if owners: owners = json.loads(owners)
        else: owners = []

        if (ctx.author.id not in owners) and (ctx.author != ctx.guild.owner):
            if ctx.author.top_role.position <= role.position:
                await ctx.send("> Vous ne pouvez retirer un rôle suppérieur ou égal hiérarchiquement à votre rôle le plus élevé.")
                return
            
        if role not in getattr(member, "roles", []):
            await ctx.send("> " + ("Vous n'avez" if member == ctx.author else f"{member.mention} n'a") + f" pas le rôle {role.mention}.", allowed_mentions = AM.none())
            return

        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send("> Je ne peux pas retirer un rôle qui est suppérieur ou égal hiérarchiquement à mon rôle le plus élevé.")
            return
        
        await member.remove_roles(role, reason = f"[{ctx.author.display_name} | {ctx.author.id}] Demande d'enlèvement de rôle")
        await ctx.send(f"> Le rôle {role.mention} " + ("vous a été retiré" if member == ctx.author else f"a été retiré à {member.mention}") + ".", allowed_mentions = AM.none())


    @commands.command(description = "Ajouter un avertissement à un membre")
    @commands.guild_only()
    async def warn(self, ctx, member : discord.Member, *, reason : str = None):
        if member == ctx.author:
            await ctx.send("> Vous ne pouvez pas vous auto-warn.")
            return
        if member == ctx.guild.owner:
            await ctx.send("> Vous ne pouvez pas warn le propriétaire du serveur.")
            return
        if ctx.author != ctx.guild.owner:
            if member.top_role.position >= ctx.author.top_role.position:
                await ctx.send("> Vous ne pouvez pas warn un membre qui est suppérieur ou égal à vous hiérarchiquement.")
                return
        
        database = Database()
        await database.connect()

        # Obtenir les warn de l'utilisateur dans une liste
        user_warns = await database.get_data("member", "warn", guild_id = ctx.guild.id, user_id = member.id)
        if not user_warns:
            user_warns = "[]"
        user_warns = json.loads(user_warns)


        if len(user_warns) >= 25:
            await ctx.send("> Pour des raisons d'optimisation, vous ne pouvez pas mettre plus de 25 avertissements à un membre.")
            return

        # Ajouter les données du warn
        user_warns.append({
            "moderator": ctx.author.id,
            "timestamp": round(datetime.now().timestamp()),
            "reason": (reason if len(reason) <= 500 else reason[:497] + "...") if reason else None
        })

        # Sauvegarder les données
        await database.set_data("member", "warn", json.dumps(user_warns), guild_id = ctx.guild.id, user_id = member.id)

        await ctx.send(f"> {member.mention} a été warn" + ("." if not reason else f" pour `" + (reason.replace("`", "'") if len(reason) <= 500 else reason[:497].replace("`", "'") + "...") + "`."), allowed_mentions = AM.none())
        await database.disconnect()
    

    @commands.command(description = "Voir et gérer les avertissements d'un utilisateur")
    @commands.guild_only()
    async def warns(self, ctx, member : discord.Member = None):
        if not member:
            member = ctx.author
            
        # Obtenir les avertissements de l'utilisateur
        async def get_warn_data() -> list:
            database = Database()
            await database.connect()
            user_warns = await database.get_data("member", "warn", guild_id = ctx.guild.id, user_id = member.id)
            await database.disconnect()

            if not user_warns:
                return []
            return json.loads(user_warns)
        
        user_warns = await get_warn_data()
        if not user_warns:
            await ctx.send(f"> " + (member.mention + " n'a" if member != ctx.author else "Vous n'avez") + " pas d'avertissement.", allowed_mentions = AM.none())
            return

        previous_warn_data = user_warns.copy()
        async def check_error(current_warn_data : list, warn_number : int):
            if not user_warns:
                return f"> {member.mention} n'a plus d'avertissement."
            if len(current_warn_data) - 1 < warn_number:
                return f"> L'avertissement n°{warn_number + 1} n'éxiste plus."
            if previous_warn_data[warn_number]["timestamp"] != current_warn_data[warn_number]["timestamp"]:
                return f"> Des avertissements ont étés supprimés entre temps, merci de réexécuter la commande pour éviter tout conflits."
            return None
        
        async def get_first_embed():
            user_warns = await get_warn_data()

            return discord.Embed(
                title = f"Avertissements de {member.display_name}",
                description = f"***{member.display_name}*** *a actuellement* ***{len(user_warns)}*** *avertissement, vous pouvez voir et gérer ces avertissement via le menu ci-dessous.*",
                color = await self.bot.get_theme(ctx.guild.id)
            )

        async def get_warn_embed(warn_number : int, tctx, user_warns):
            embed = discord.Embed(
                title = f"Avertissement n°{warn_number + 1}",
                color = await bot.get_theme(tctx.guild.id),
                thumbnail = tctx.guild.icon.url if tctx.guild.icon else None
            )
            concerned_warn = user_warns[warn_number]
            embed.add_field(name = "Utilisateur concerné", value = f"{member.mention} (**{member.display_name}**)")
            try:
                moderator = await bot.fetch_user(concerned_warn["moderator"])
                embed.add_field(name = "Modérateur", value = f"{moderator.mention} (**{moderator.display_name}**)")
            except: embed.add_field(name = "Modérateur", value = f"<@{concerned_warn['moderator']}>")
            embed.add_field(name = "Date", value = f"<t:{concerned_warn['timestamp']}> (<t:{concerned_warn['timestamp']}:R>)", inline = False)
            embed.add_field(name = "Raison", value = concerned_warn["reason"] if concerned_warn["reason"] else "*Aucune raison fournie*")

            return embed

        times = []
        for warn_data in user_warns:
            time_difference = datetime.now() - datetime.fromtimestamp(warn_data["timestamp"])

            # Calculer la durée qui s'est écoulée entre la date actuel et la date de l'avertissement
            days = time_difference.days
            seconds = time_difference.seconds
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            result = ""

            # Convertir les durées en texte
            if days: result += f"{days} jours, "
            if hours: result += f"{hours}h, "
            if minutes: result += f"{minutes}m"
            if result: result += f" et {seconds}s"
            else: result += f"{seconds}s"
            
            times.append(result)
        
        bot = self.bot
        class ManageWarn(discord.ui.View):
            async def on_timeout(self):
                try: await self.message.edit(view = None)
                except: pass

            @discord.ui.select(
                placeholder = "Choisir un avertissement",
                options = [
                    discord.SelectOption(label = f"Avertissement n°{i+1} (il y'a {times[i]})", value = str(i))
                    for i in range(len(user_warns)-1, -1, -1)
                ]
            )
            async def choose_warn_select(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
            
                user_warns = await get_warn_data()
                error = await check_error(user_warns, int(select.values[0]))
                if error:
                    await interaction.response.send_message(error, ephemeral = True)
                    return
                
                choose_warn_view = self
                warn_number = int(select.values[0])

                class EditWarn(discord.ui.View):
                    async def on_timeout(self):
                        try: await self.message.edit(view = None)
                        except: pass

                    @discord.ui.select(
                        placeholder = "Choisir une action",
                        options = [
                            discord.SelectOption(label = "Modifier la raison", emoji = "📜", value = "edit_reason"),
                            discord.SelectOption(label = "Supprimer l'avertissement", emoji = "🗑", value = "del_warn")
                        ]
                    )
                    async def select_action_callback(self, select, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return

                
                        user_warns = await get_warn_data()
                        error = await check_error(user_warns, warn_number)
                        if error:
                            await interaction.response.send_message(error, ephemeral = True)
                            return
                        
                        def response_checker(message):
                            return (message.content) and (message.author == ctx.author) and (message.channel == ctx.channel)
                        
                        await interaction.response.defer()
                        if select.values[0] == "edit_reason":
                            message = await ctx.send(f"Quel sera la nouvelle raison de l'avertissement n°{warn_number + 1} de **{member.display_name}** ?")
                            try:
                                response = await bot.wait_for("message", timeout = 60, check = response_checker)
                            except asyncio.TimeoutError:
                                await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                                return
                            finally: await message.delete()
                            await response.delete()

                            if len(response.content) > 500:
                                await ctx.send("> Action annulée, raison trop longue.", delete_after = 2)
                                return
                            
                            user_warns = await get_warn_data()
                            error = await check_error(user_warns, warn_number)
                            if error:
                                await ctx.send(f"> Action annulée. {error.removeprefix('> ')}")
                                return
                            
                            user_warns[warn_number]["reason"] = response.content
                            db = Database()
                            await db.connect()
                            await db.set_data("member", "warn", json.dumps(user_warns), guild_id = interaction.guild.id, user_id = member.id)
                            await db.disconnect()

                            await ctx.send(f"> La raison de l'avertissement n°{warn_number + 1} a été correctement modifiée.", delete_after = 2)
                            await interaction.message.edit(embed = await get_warn_embed(warn_number, interaction, user_warns))

                        if select.values[0] == "del_warn":
                            user_warns.pop(warn_number)

                            db = Database()
                            await db.connect()
                            await db.set_data("member", "warn", json.dumps(user_warns), guild_id = interaction.guild.id, user_id = member.id)
                            await db.disconnect()

                            await interaction.message.edit(
                                embed = discord.Embed(
                                    title = "L'avertissement demandé a été supprimé.",
                                    description = f"Lorsque vous réexécuterez la commande `+warns`, vous verrez peut-être un avertissement avec le même \"nom\" (Avertissement n°{warn_number + 1}), ce n'est pas un bug, c'est juste que nous énumerons chaques avertissements, les avertissements n'ont pas d'identifiants, ils sont associés à des index.",
                                    color = await bot.get_theme(interaction.guild.id)
                                ),
                                view = None
                            )

                    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                    async def comeback_callback_button(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        await interaction.response.defer()
                        await interaction.message.edit(view = choose_warn_view, embed = await get_first_embed())

                embed = await get_warn_embed(warn_number, interaction, user_warns)

                await interaction.message.edit(
                    embed = embed,
                    view = EditWarn(timeout = 300)
                )
                await interaction.response.defer()
            
            @discord.ui.button(label = "Tout supprimer", style = discord.ButtonStyle.danger)
            async def del_all_warn(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                db = Database()
                await db.connect()
                await db.set_data("member", "warn", json.dumps([]), guild_id = interaction.guild.id, user_id = member.id)
                await db.disconnect()

                await interaction.response.defer()
                await interaction.message.edit(embed = discord.Embed(title = f"Les avertissements de {member.display_name} ont étés supprimés.", color = await bot.get_theme(interaction.guild.id)), view = None)

        await ctx.send(embed = await get_first_embed(), view = ManageWarn(timeout = 300))

    
    @commands.command(description = "Supprimer un certains nombre de message")
    @commands.bot_has_permissions(manage_messages = True)
    @commands.guild_only()
    async def clear(self, ctx, count : int, member : discord.Member = None):
        if not 1 <= count <= 1000:
            await ctx.send("> Votre nombre de message à supprimer doit être entre 1 et 1000.")
            return
        
        await ctx.message.delete()
        def message_check(message):
            if member: return message.author == member
            return True
        
        await ctx.channel.purge(
            limit = count,
            check = message_check,
            reason = f"[{ctx.author.display_name} | {ctx.author.id}] Suppression de {count} messages" + (f" appartenants à {member.display_name}" if member else "")
        )


def setup(bot):
    bot.add_cog(Moderation(bot))