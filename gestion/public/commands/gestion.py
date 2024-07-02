import discord
from discord.ext import commands

class Gestion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Modifier la visiblitée/la permission d'envoi pour un salon", usage = "<lock/unlock/hide/unhide> [channel]")
    @commands.bot_has_permissions(manage_channels = True)
    @commands.guild_only()
    async def ch(self, ctx, action : str, channel : discord.ChannelType = None):
        if action.lower() not in ["lock", "unlock", "hide", "unhide"]:
            await ctx.send("> Merci de donner une action valide (lock/unlock/hide/unhide).")
            return
        
        if not channel:
            channel = ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)

        if action.lower() in ["lock", "unlock"]:
            send_messages_perm = False if action.lower() == "lock" else True
            if overwrite.send_messages == send_messages_perm:
                await ctx.send(f"> Ce salon est déjà **{action.lower()}**.")
                return
            overwrite.send_messages = send_messages_perm
        else:
            view_channel_perm = False if action.lower() == "hide" else True
            if overwrite.view_channel == view_channel_perm:
                await ctx.send(f"> Ce salon est déjà **{action.lower()}**.")
                return
            overwrite.view_channel = view_channel_perm

        await channel.set_permissions(
            ctx.guild.default_role,
            reason = f"{action.lower()} de {ctx.author.display_name} ({ctx.author.id})",
            overwrite = overwrite
        )

        if ctx.channel != channel:
            await ctx.send(f"> Le salon {channel.mention} a été **{action.lower()}**.")
        await channel.send(f"> Le salon {channel.mention} a été **{action.lower()}** par {ctx.author.mention}.", allowed_mentions = discord.AllowedMentions().none())


    @commands.command(description = "Modifier la visiblitée/la permission d'envoi pour tous les salons (dans une certaine catégorie, si spécifiée)", usage = "<lock/unlock/hide/unhide> [catégorie]")
    @commands.guild_only()
    async def chall(self, ctx, action, category : discord.CategoryChannel = None):
        """
        Lorsque vous spécifiez une catégorie, **uniquements** les salons de celle-ci seront affectés.
        Sinon, **tous les salons** seront affectés.
        """
        if action.lower() not in ["lock", "unlock", "hide", "unhide"]:
            await ctx.send("> Merci de donner une action valide (lock/unlock/hide/unhide).")
            return

        

        
        


    # credits : @koryai (discord)
    @commands.command(description = "Enleve tous les rôles d'un membre du serveur.")
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