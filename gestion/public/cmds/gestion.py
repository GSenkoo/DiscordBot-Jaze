import discord
from discord.ext import commands

class Gestion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # credits : @koryai (discord)
    @commands.command(description = "Empêcher les membres d'envoyer des messages dans un salon")
    @commands.guild_only()
    async def lock(self, ctx, channel : discord.TextChannel = None):
        if not channel:
            channel = ctx.channel

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.edit(ctx.guild.default_role, overwrites = overwrite)
        await ctx.send(f"> Le salon {channel.mention} a été **lock**.")

    
    # credits : @koryai (discord)
    @commands.command(description = "Autoriser les membres d'envoyer des messages dans un salon")
    @commands.guild_only()
    async def unlock(self, ctx, channel : discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
            
        if channel.permissions_for(ctx.guild.default_role).send_messages:
            await ctx.send("> Les membres ne peuvent déjà plus envoyer de message dans ce salon.")
            return

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await channel.edit(ctx.guild.default_role, overwrites = overwrite)
        await ctx.send(f"> Le salon {channel.mention} a été **unlock**.")


    # credits : @koryai (discord)
    @commands.command(description = "Cacher un salon du serveur")
    @commands.guild_only()
    async def hide(self, ctx, channel : discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
            
        if channel.permissions_for(ctx.guild.default_role).send_messages:
            await ctx.send("> Les membres ne peuvent déjà plus envoyer de message dans ce salon.")
            return

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = True
        await channel.edit(ctx.guild.default_role, overwrites = overwrite)
        await ctx.send(f"> Le salon {channel.mention} a été **hide**.")


    # credits : @koryai (discord)
    @commands.command(description = "Cacher un salon du serveur.")
    @commands.guild_only()
    async def unhide(self, ctx, channel : discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
            
        if channel.permissions_for(ctx.guild.default_role).send_messages:
            await ctx.send("> Les membres ne peuvent déjà plus envoyer de message dans ce salon.")
            return

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        await channel.edit(ctx.guild.default_role, overwrites = overwrite)
        await ctx.send(f"> Le salon {channel.mention} a été **unhide**.")


    # credits : @koryai (discord)
    @commands.command(description = "Empêcher les membres d'envoyer des messages dans tous les salons.")
    @commands.guild_only()
    async def lockall(self, ctx):
        for channel in ctx.guild.channels:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            await channel.edit(ctx.guild.default_role, overwrites = overwrite)
            continue

        await ctx.send(f"> **Tous les salons** du serveur ont étés **lock**.")

    
    # credits : @koryai (discord)
    @commands.command(description = "Autoriser les membres à envoyer des messages dans tous les salons.")
    @commands.guild_only()
    async def unlockall(self, ctx):
        for channel in ctx.guild.channels:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = True
            await channel.edit(ctx.guild.default_role, overwrites = overwrite)
            continue

        await ctx.send(f"> **Tous les salon** du serveur a été **unlock**.")


    # credits : @koryai (discord)
    @commands.command(description = "Cacher tous les salons du serveur.")
    async def hideall(self, ctx):
        for channel in ctx.guild.channels:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = False
            await channel.edit(ctx.guild.default_role, overwrites = overwrite)

        await ctx.send("> **Tous les salons** du serveur sont désormais **visibles**.")


    # credits : @koryai (discord)
    @commands.command(description = "Rendre visible tous les salons du serveur.")
    @commands.guild_only()
    async def unhideall(self, ctx):
        for channel in ctx.guild.channels:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = True
            await channel.edit(ctx.guild.default_role, overwrites = overwrite)

        await ctx.send(f"> **Tous les salons** du serveur sont désormais **invisibles**.")


    @commands.command(description = "Enleve tous les rôles a un membre du serveur.")
    @commands.guild_only()
    async def derank(self, ctx, member : discord.Member):
        if ctx.author == member:
            await ctx.send("> Vous ne pouvez pas vous auto-dérank.")
            return
        if ctx.guild.owner == member:
            await ctx.send("> Je ne peux pas dérank le propriétaire du serveur.")
            return
        if member.top_role.position <= ctx.guild.me.top_role.position:
            await ctx.send(f"> Je ne peux pas dérank {member.mention} car il est au-dessus de moi dans la hiérarchie du serveur.", allowed_mentions = None)
            return

        member_roles = [role for role in member.roles if role.is_assignable()] 
        
        for role in member_roles:
            await member.remove_roles(role, atomic = True)

        await ctx.send(f"{member.mention} a été derank, {len(member_roles)} rôles lui ont étés retirés.")


def setup(bot):
    bot.add_cog(Gestion(bot))