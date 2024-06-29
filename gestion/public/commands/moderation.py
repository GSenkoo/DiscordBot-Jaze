import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # credits : @koryai (discord) -> reworked by @senkoo.g4l (discord)
    @commands.command(description = "Bannir un membre du serveur")
    @commands.bot_has_permissions(ban_members = True, send_messages = True)
    @commands.guild_only()
    async def ban(self, ctx, member : discord.Member, *, reason = None):
        if member == ctx.author:
            await ctx.send("> Vous ne pouvez pas vous auto-bannir du serveur.")
            return
        if member == ctx.guild.owner:
            await ctx.send("> Vous ne pouvez pas bannir le propriétaire du serveur.")
            return
        if member.top_role.position <= ctx.author.top_role.position:
            await ctx.send("> Vous ne pouvez pas bannir un membre qui est suppérieur ou égal à vous hiérarchiquement.")
            return
        if member.top_role.position <= ctx.guild.me.top_role.position:
            await ctx.send(f"> Je ne peux pas bannir {member.mention} car il est suppérieur ou égal à moi hiérarchiquement", allowed_mentions = None)
            return
        
        if reason is None: reason = f'Aucune raison specifié par {ctx.author.name}'
        try: await member.ban(reason = reason)
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative de bannissement de {member.mention}.", allowed_mentions = None)
            return
        
        await ctx.send(f"> {member.mention} a été banni du serveur" + ("." if not reason else f" pour `" + reason.replace("`", "'") + "`."), allowed_mentions = None) 

    
    # credits : @koryai (discord) -> reworked by @senkoo.g4l (discord)
    @commands.command(description = "Kick un membre du serveur")
    @commands.bot_has_permissions(kick_members = True, send_messages = True)
    @commands.guild_only()
    async def kick(self, ctx, member : discord.Member, *, reason = None):
        if member == ctx.author:
            await ctx.send("> Vous ne pouvez pas vous auto-kick du serveur.")
            return
        if member == ctx.guild.owner:
            await ctx.send("> Vous ne pouvez pas kick le propriétaire du serveur.")
            return
        if member.top_role.position <= ctx.author.top_role.position:
            await ctx.send("> Vous ne pouvez pas kick un membre qui est suppérieur ou égal à vous hiérarchiquement.")
            return
        if member.top_role.position <= ctx.guild.me.top_role.position:
            await ctx.send(f"> Je ne peux pas kick {member.mention} car il est suppérieur ou égal à moi hiérarchiquement", allowed_mentions = None)
            return
        
        if reason is None: reason = f'Aucune raison specifié par {ctx.author.name}'
        try: await member.ban(reason = reason)
        except:
            await ctx.send(f"> Une erreur s'est produite lors de la tentative d'expulsion de {member.mention}.", allowed_mentions = None)
            return
        
        await ctx.send(f"> {member.mention} a été expulsé du serveur" + ("." if not reason else f" pour `" + reason.replace("`", "'") + "`."), allowed_mentions = None) 

def setup(bot):
    bot.add_cog(Moderation(bot))