import discord
import json
import asyncio
import emoji

from datetime import timedelta
from discord import AllowedMentions as AM
from discord.ext import commands
from utils.Tools import Tools
from utils.Searcher import Searcher

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
            

    @commands.command(description = "Lancer un giveaway")
    @commands.guild_only()
    async def giveaway(self, ctx):
        tools = Tools(self.bot)
        searcher = Searcher(self.bot, ctx)

        async def get_giveaway_embed(data) -> discord.Embed:
            embed = discord.Embed(
                title = "Giveaway",
                color = await self.bot.get_theme(ctx.guild.id)
            )

            embed.add_field(name = "Récompense", value = data["reward"])
            embed.add_field(name = "Durée", value = data["end_at"])
            embed.add_field(name = "Salon", value = f'<#{data["channel"]}>')
            embed.add_field(name = "Emoji", value = data["emoji"])
            embed.add_field(name = "Type d'intéraction", value = data["interaction_type"].capitalize())
            embed.add_field(name = "Couleur (Bouton)", value = data["button_color"].capitalize())
            embed.add_field(name = "Texte (Button)", value = data["button_text"])
            embed.add_field(name = "Nombre de gagnants", value = str(data["winners_count"]))
            embed.add_field(name = "Gagnant imposé", value = f"<@{data['imposed_winner']}>" if data["imposed_winner"] else "*Aucun gagnant imposé*")
            embed.add_field(name = "Rôles requis", value = "<@&" + f">\n<@&".join(data["required_roles"]) if data["required_roles"] else "*Aucun rôles*")
            embed.add_field(name = "Rôles interdits", value = "<@&" + f">\n<@&".join(data["prohibited_roles"]) if data["prohibited_roles"] else "*Aucun rôles*")
            embed.add_field(name = "Imposer la présence en vocal", value = "Oui" if data["in_vocal_required"] else "Non")

            return embed


        giveaway_data = {
            "reward": "Exemple de récompense",
            "end_at": "2h",
            "channel": ctx.channel.id,
            "emoji": "🎉",
            "interaction_type": "button",
            "button_color": "blue", # blue, green, gray or red
            "button_text": "Participer",
            "winners_count": 1,
            "imposed_winner": 0,
            "required_roles": [],
            "prohibited_roles": [],
            "in_vocal_required": False
        }

        bot = self.bot
        class ManageGiveaway(discord.ui.View):
            def __init__(self, giveaway_data : dict):
                super().__init__(timeout = 180)
                self.giveaway_data = giveaway_data

            async def on_timeout(self) -> None:
                try: await self.message.edit(view = None)
                except: pass

            @discord.ui.select(
                placeholder = "Modifier une valeur",
                options = [
                    discord.SelectOption(label = "Récompense", value = "reward", emoji = "🎁"),
                    discord.SelectOption(label = "Durée", value = "end_at", emoji = "⏱️"),
                    discord.SelectOption(label = "Salon", value = "channel", emoji = "🏷"),
                    discord.SelectOption(label = "Emoji", value = "emoji", emoji = "⚪"),
                    discord.SelectOption(label = "Type d'intéraction", value = "interaction_type", emoji = "💥"),
                    discord.SelectOption(label = "Couleur (Bouton)", value = "button_color", emoji = "🎨"),
                    discord.SelectOption(label = "Texte (Bouton)", value = "button_text", emoji = "📝"),
                    discord.SelectOption(label = "Nombre de gagnant", value = "winners_count", emoji = "👥"),
                    discord.SelectOption(label = "Gagnants imposés", value = "imposed_winner", emoji = "👤"),
                    discord.SelectOption(label = "Rôles requis", value = "allowed_roles", emoji = "⛓"),
                    discord.SelectOption(label = "Rôles interdits", value = "prohibited_roles", emoji = "🚫"),
                    discord.SelectOption(label = "Imposition de la présence en vocal", value = "in_vocal_required", emoji = "🔊")
                ]
            )
            async def edit_giveaway_select_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                async def delete_message(message):
                    try: await message.delete()
                    except: pass

                async def get_emoji(query):
                    if emoji.is_emoji(query):
                        return query
                    
                    query = query.split(":")
                    if len(query) != 3:
                        return None
                    
                    query = query[2].replace(">", "")
                    try: query = bot.get_emoji(int(query))
                    except Exception as e:
                        print(e)
                        return None
                    return query

                async def get_option_name(option_id):
                    for option in select.options:
                        if option.value == option_id:
                            return option.label
                    return None
                
                async def check_message_validity(message):
                    return (message.channel == ctx.channel) and (message.author == ctx.author) and (message.content)
                
                await interaction.response.defer()

                # ----------------------------- Obtention d'une réponse
                notes = {
                    "end_at": "Voici quelques exemple de temps valides : `1jours`, `3d`, `4h` , `5minutes`. Maximum 30 jours.",
                    "interaction_type": "Types d'intéractions disponibles : `bouton` et `réaction`",
                    "button_color": "Couleurs disponibles : `bleu`, `rouge`, `vert` et `gris`"
                }

                ask_message = await ctx.send(
                    f"> Quel **{await get_option_name(select.values[0])}** souhaitez-vous définir à votre giveaway?"
                    + (f"\n{notes[select.values[0]]}" if select.values[0] in list(notes.keys()) else "")
                )

                try: response_message = await bot.wait_for("message", timeout = 60, check = check_message_validity)
                except asyncio.TimeoutError:
                    await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                    return
                finally: await delete_message(ask_message)
                await delete_message(response_message)


                # ----------------------------- S'occuper de la valeur
                if select.values[0] == "reward":
                    if len(response_message.content) > 100:
                        await ctx.send("> Action annulée, votre nom de récompense est trop long (plus de 100 caractères).", delete_after = 2)
                        return
                    
                    self.giveaway_data["reward"] = response_message.content

                if select.values[0] == "end_at":
                    time = await tools.find_duration(response_message.content)

                    if not time:
                        await ctx.send("> Action annulée, durée invalide.", delete_after = 2)
                        return
                    if time > timedelta(days = 30):
                        await ctx.send("> Action annulée, durée trop longue. Vous ne pouvez pas définir une durée suppérieure à 30 jours.", delete_after = 2)
                        return
                    
                    self.giveaway_data["end_at"] = response_message.content

                if select.values[0] == "channel":
                    channel = await searcher.search_channel(response_message.content)

                    if not channel:
                        await ctx.send("> Action annulée, salon invalide.", delete_after = 2)
                        return
                    
                    self.giveaway_data["channel"] = channel.id

                if select.values[0] == "emoji":
                    found_emoji = await get_emoji(response_message.content)

                    if not found_emoji:
                        await ctx.send("> Emoji invalide, merci de donner un emoji valide.", delete_after = 2)
                        return
                    
                    self.giveaway_data["emoji"] = found_emoji

                if select.values[0] == "interaction_type":
                    if response_message.content.lower() in ["button", "buttons", "bouton", "boutons"]: self.giveaway_data["interaction_type"] = "button"
                    elif response_message.content.lower() in ["reaction", "reactions", "réaction", "réactions"]: self.giveaway_data["interaction_type"] = "reaction"
                    else:
                        await ctx.send("> Action annulée, type d'intéraction invalide.", delete_after = 2)
                        return

                if select.values[0] == "button_color":
                    if response_message.content.lower() in ["blue", "bleu"]: self.giveaway_data["button_color"] = "blue"
                    elif response_message.content.lower() in ["green", "vert"]: self.giveaway_data["button_color"] = "green"
                    elif response_message.content.lower() in ["red", "rouge"]: self.giveaway_data["button_color"] = "red"
                    elif response_message.content.lower() in ["gray", "gris"]: self.giveaway_data["button_color"] = "grey"
                    else:
                        await ctx.send("> Action annulée, couleur invalide.", delete_after = 2)
                        return

                if select.values[0] == "button_text":
                    if len(response_message.content) > 80:
                        await ctx.send("> Action annulée, vous ne pouvez pas définir un texte de bouton de plus de 80 caractères.", delete_after = 2)
                        return
                    
                    self.giveaway_data["button_text"] = response_message.content

                if select.values[0] == "winners_count":
                    if not response_message.content.isdigit():
                        await ctx.send("> Action annulée, vous n'avez pas donner de nombre valide.", delete_after = 2)
                        return
                    if not 1 <= int(response_message.content) <= 100:
                        await ctx.send("> Action annulée, votre nombre de gagnant doit être entre 1 et 100.", delete_after = 2)
                        return
                    
                    self.giveaway_data["winners_count"] = int(response_message.content)
                 

                # ----------------------------- Mettre à jours le message de giveaway
                await interaction.message.edit(embed = await get_giveaway_embed(self.giveaway_data))




            
            @discord.ui.button(label = "Envoyer", emoji = "✅")
            async def send_giveaway_button_callback(self, button, interaction):
                ...


        await ctx.send(view = ManageGiveaway(giveaway_data), embed = await get_giveaway_embed(giveaway_data))

        """
        "primary_keys": {"guild_id": "BIGINT NOT NULL", "channel_id": "BIGINT NOT NULL", "message_id": "BIGINT NOT NULL UNIQUE"},
        "keys": {
            "reward": "VARCHAR(255) DEFAULT 'Acune récompense'",
            "end_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "channel": "BIGINT DEFAULT 0",
            "emoji": "VARCHAR(10)",
            "interaction_type": "VARCHAR(10) DEFAULT 'reaction'",
            "button_color": "VARCHAR(10) DEFAULT 'blue'",
            "button_text": "VARCHAR(80) DEFAULT 'Participer'",
            "winners_count": "INTEGER DEFAULT 1",
            "participations": "MEDIUMTEXT",
            "imposed_winner": "BIGINT DEFAULT 0",
            "required_roles": "BIGINT DEFAULT 0",
            "prohibited_role": "BIGINT DEFAULT 0",
            "in_vocal_required": "BOOLEAN DEFAULT 0"
        }
        """


def setup(bot):
    bot.add_cog(Gestion(bot))