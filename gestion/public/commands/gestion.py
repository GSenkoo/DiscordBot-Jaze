import discord
from discord import AllowedMentions as AM
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
            await ctx.send(f"> Le salon {channel.mention} a été **{action.lower()}**.", delete_after = 10)
        await channel.send(f"> Le salon {channel.mention} a été **{action.lower()}** par {ctx.author.mention}.", allowed_mentions = discord.AllowedMentions().none())


    @commands.command(description = "Modifier la visiblitée/la permission d'envoi pour tous les salons", usage = "<lock/unlock/hide/unhide> [category]")
    @commands.bot_has_permissions(manage_channels = True, send_messages = True)
    @commands.guild_only()
    async def chall(self, ctx, action : str, category : discord.CategoryChannel = None):
        """
        Lorsque vous spécifiez une catégorie, **uniquements** les salons de celle-ci seront affectés.
        Sinon, **tous les salons** seront affectés.
        """
        if action.lower() not in ["lock", "unlock", "hide", "unhide"]:
            await ctx.send("> Merci de donner une action valide (lock/unlock/hide/unhide).")
            return

        if category: channels = category.channels
        else: channels = ctx.guild.channels

        msg = await ctx.send(f"> Action {action}all en cours...")

        if action.lower() in ["lock", "unlock"]: perms = {"send_messages": False if action.lower() == "lock" else True}
        else: perms = {"view_channel": False if action.lower() == "hide" else True}

        saves = []
        for channel in channels:
            channel_overwrites = channel.overwrites_for(ctx.guild.default_role)
            perm_to_def = list(perms.keys())[0]
            current_channel_perm_value = getattr(channel_overwrites, perm_to_def)
            perm_to_def_value = perms[perm_to_def]

            if current_channel_perm_value == perm_to_def_value:
                continue
        
            saves.append(channel.id)
            setattr(channel_overwrites, perm_to_def, perm_to_def_value)
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite = channel_overwrites,
                reason = f"{action.lower()} (pour tous les salons{'' if not category else f' de la catégorie {category.name}'}) de {ctx.author.display_name} ({ctx.author.id})"
            )

            try: await channel.send(f"> Le salon {channel.mention} a été **{action.lower()}**.", delete_after = 10)
            except: pass

        class RestorePermissions(discord.ui.View):
            def __init__(self, permission_data):
                super().__init__(timeout = 600)
                self.permissions_data = permission_data

            async def on_timeout(self):
                try:
                    self.disable_all_items()
                    await self.message.edit(view = self)
                except: pass

            @discord.ui.button(
                label = "Restaurer les permissions",
                style = discord.ButtonStyle.danger,
                custom_id = "restore"
            )
            async def restore_permission(self, button, interaction):
                if (interaction.user != ctx.author) and (interaction.user != ctx.guild.owner):
                    await interaction.response.send_message(f"> Seul {interaction.user.mention} peut intéragir avec ceci (ou le propriétaire du serveur).", ephemeral = True)
                    return
                
                button.disabled = True
                await interaction.response.defer()
                await interaction.message.edit("> Restauration des permissions en cours...", view = self)

                for channel in interaction.guild.channels:
                    if channel.id not in self.permissions_data:
                        continue
                    
                    channel_overwrites = channel.overwrites_for(interaction.guild.default_role)
                    setattr(channel_overwrites, perm_to_def, not perm_to_def_value)
                    await channel.set_permissions(
                        interaction.guild.default_role,
                        overwrite = channel_overwrites,
                        reason = f"Restauration de permission par {interaction.user.display_name} ({interaction.user.id})"
                    )
                try: await interaction.message.edit(f"> Restauration de {len(self.permissions_data)} salons terminés.", view = self)
                except: pass
        
        try:
            await msg.edit(
                f"> Tous les salons {'du serveur' if not category else f'de la catégorie **{category.name}**'} ont étés **{action}**.\n\n"
                + "*Pour restorer les permissions, intéragissez avec le boutton ci-dessous dans les 10 minutes qui suivent.*",
                view = RestorePermissions(saves)
            )
        except:
            await ctx.send(
                f"> Tous les salons {'du serveur' if not category else f'de la catégorie **{category.name}**'} ont étés **{action}**.\n\n"
                + "*Pour restorer les permissions, intéragissez avec le boutton ci-dessous dans les 10 minutes qui suivent.*",
                view = RestorePermissions(saves)
            )


    @commands.command(description = "Duppliquer un salon et ensuite supprimer le salon initial.")
    @commands.bot_has_guild_permissions(manage_channels = True)
    @commands.guild_only()
    async def renew(self, ctx, channel : discord.ChannelType = None):
        if not channel:
            channel = ctx.channel

        if channel == ctx.guild.rules_channel:
            await ctx.send("> Le salon des règles ne peut pas être supprimé.")
            return
        if channel == ctx.guild.public_updates_channel:
            await ctx.send("> Le salon de mise à jour de la communauté ne peut pas être supprimé.")
            return
        
        new_channel = await channel.clone(reason = f"[{ctx.author.display_name} | {ctx.author.id}] Demande de renew")
        await channel.delete()

        await new_channel.send(f"> Le salon a était renew par {ctx.author.mention}.", allowed_mentions = AM.none(), delete_after = 10)
            


def setup(bot):
    bot.add_cog(Gestion(bot))