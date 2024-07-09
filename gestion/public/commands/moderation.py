import discord
import json
import asyncio
from discord import AllowedMentions as AM
from discord.ext import commands
from utils.Database import Database
from utils.GPChecker import GPChecker
from utils.Tools import Tools
from datetime import datetime, timedelta


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Bannir un membre du serveur")
    @commands.cooldown(rate = 5, per = 60)
    @commands.bot_has_permissions(ban_members = True)
    @commands.guild_only()
    async def ban(self, ctx, user : discord.User, *, reason = None):
        checker = GPChecker(ctx)
        tools = Tools()

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
        
        if reason: log_reason = log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] Aucune raison specifiée"

        try: await ctx.guild.ban(user, reason = log_reason if len(log_reason) <= 50 else log_reason[:47] + "...")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative de bannissement de {member.mention}.", allowed_mentions = AM.none())
            return
        
        await tools.add_sanction("ban", ctx, user, reason)
        await ctx.send(f"> {member.mention} a été banni du serveur" + ("." if not reason else f" pour `" + (reason.replace("`", "'") if len(reason) <= 50 else reason.replace("`", "'")[:47] + "...") + "`."), allowed_mentions = AM.none()) 

    
    @commands.command(description = "Kick un membre du serveur")
    @commands.cooldown(rate = 5, per = 60)
    @commands.bot_has_permissions(kick_members = True)
    @commands.guild_only()
    async def kick(self, ctx, member : discord.Member, *, reason = None):
        checker = GPChecker(ctx)
        tools = Tools()

        check = await checker.we_can_kick(member)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        if reason: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] Aucune raison specifiée"

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
        checker = GPChecker(ctx)
        tools = Tools()

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
        
        if reason: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] Aucune raison fournie"
        
        try:
            await member.timeout_for(duration_timedelta, reason = log_reason if len(log_reason) <= 50 else log_reason[:47] + "...")
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative de tempmute de {member.mention}.", allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> {member.mention} a été tempmute `{duration}`" + ((" pour " + reason.replace("`", "'") if len(reason) <= 50 else reason.replace("`", "")[:47] + "...") if reason else "."))
        await tools.add_sanction("tempmute", ctx, member, reason, duration_timedelta)


    @commands.command(description = "Unmute un membre ayant été mute avec le système d'exclusion")
    @commands.bot_has_permissions(moderate_members = True)
    @commands.guild_only()
    async def untempmute(self, ctx, member : discord.Member, reason : str = None):
        checker = GPChecker(ctx)

        check = await checker.we_can_untempmute(member)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        if reason: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] {reason}"
        else: log_reason = f"[{ctx.author.display_name} | {ctx.author.id}] Aucune raison fournie"

        try: await member.remove_timeout(reason = log_reason)
        except:
            await ctx.send("> Une erreur s'est produite lors de la tentive de untempmute.")
            return
        
        await ctx.send(f"> Le membre {member.mention} a été untempmute.", allowed_mentions = AM.none())
        try: await member.send(
            f"> Vous avez été untempmute manuellement du serveur **{ctx.guild.name}** par **{member.display_name}**"
            + ("." if not reason else " pour `" + reason.replace("`", "'") + "`.")
        )
        except: pass

    
    @commands.command(description = "Retirer tous les rôles d'un membre")
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles = True)
    async def derank(self, ctx, member : discord.Member, *, reason : str = None):
        checker = GPChecker(ctx)
        tools = Tools()

        check = await checker.we_can_derank(member)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        member_roles = [role for role in member.roles if role.is_assignable()]

        try: await member.remove_roles(*member_roles, reason = f"[{ctx.author.display_name} | {ctx.author.id}] Demande de derank")
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

        checker = GPChecker(ctx)
        check = await checker.we_can_add_role(member, role)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        try: await member.add_roles(role, reason = f"[{ctx.author.display_name} | {ctx.author.id}] Demande d'ajout de rôle")
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

        checker = GPChecker(ctx)
        check = await checker.we_can_remove_role(member, role)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        await member.remove_roles(role, reason = f"[{ctx.author.display_name} | {ctx.author.id}] Demande d'enlèvement de rôle")
        await ctx.send(f"> Le rôle {role.mention} " + ("vous a été retiré" if member == ctx.author else f"a été retiré à {member.mention}") + ".", allowed_mentions = AM.none())


    @commands.command(description = "Ajouter un avertissement à un membre")
    @commands.guild_only()
    async def warn(self, ctx, member : discord.Member, *, reason : str = None):
        checker = GPChecker(ctx)
        tools = Tools()

        check = await checker.we_can_warn(member)
        if check != True:
            await ctx.send(check, allowed_mentions = AM.none())
            return
        
        await ctx.send(f"> {member.mention} a été warn" + ("." if not reason else f" pour `" + (reason.replace("`", "'") if len(reason) <= 500 else reason[:497].replace("`", "'") + "...") + "`."), allowed_mentions = AM.none())
        await tools.add_sanction("warn", ctx, member, reason)

    
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