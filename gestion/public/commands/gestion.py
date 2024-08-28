import discord
import json
import asyncio
import emoji
import random

from datetime import timedelta, datetime
from discord import AllowedMentions as AM
from discord.ext import commands
from utils.Tools import Tools
from utils.Searcher import Searcher
from utils.Paginator import PaginatorCreator
from utils.MyViewClass import MyViewClass
from utils.PermissionsManager import PermissionsManager

class Gestion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.massiverole_loading = {}

    async def cog_unload(self):
        for key in self.massiverole_loading.keys():
            self.massiverole_loading[key] = False


    @commands.Cog.listener()
    async def on_interaction(self, interaction : discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        if not interaction.custom_id.startswith("massiverole_stop"):
            return
        
        if not self.massiverole_loading.get(interaction.guild.id, False):
            await interaction.response.send_message("> Il n'y a aucun massiverole en cours sur ce serveur.", ephemeral = True)
            return
        
        if (interaction.user != interaction.guild.owner) and (str(interaction.user.id) not in interaction.custom_id):
            await interaction.response.send_message("> Seul l'auteur de l'action ou le propriétaire peut arrêter ce massiverole.")
            return
        
        del self.massiverole_loading[interaction.guild.id]

        class StopedMassiveRole(MyViewClass):
            @discord.ui.button(label = "Arrêter", style = discord.ButtonStyle.danger, disabled = True)
            async def stop_massiverole_callback(self, button, interaction):
                pass
        
        await interaction.channel.send(f"<@{interaction.custom_id.removeprefix('massiverole_stop_')}>", embed = discord.Embed(title = f"Massiverole annulé par {interaction.user.display_name}", color = await self.bot.get_theme(interaction.guild.id)))
        await interaction.response.defer()


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
                await interaction.edit("> Restauration des permissions en cours...", view = self)

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
                try: await interaction.edit(f"> Restauration de {len(self.permissions_data)} salons terminés.", view = self)
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


    @commands.command(description = "Synchroniser un salon, tous les salons d'une catégorie ou tous les salons", usage = "<channel/category/all>", aliases = ["synchronize"])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels = True)
    async def sync(self, ctx, param):
        """
        Exemples : 
        `sync #salon`
        `sync #category`
        `sync all`
        """
        searcher = Searcher(self.bot, ctx)

        # ------------------------------------- Channel
        channel = await searcher.search_channel(param)
        if channel:
            if not channel.category:
                await ctx.send(f"> Le salon {channel.mention} n'est pas dans une catégorie.")
                return
            if channel.permissions_synced:
                await ctx.send(f"> Le salon {channel.mention} est déjà synchronisé avec sa catégorie.")
                return
            
            try: await channel.edit(sync_permissions = True)
            except:
                await ctx.send(f"> Impossible de synchroniser le salon {channel.mention} avec sa catégorie.")
                return
            await ctx.send(f"> Le salon {channel.mention} a bien été synchronisé avec sa catégorie.")
            return
        
        # ------------------------------------- Category
        category = await searcher.search_category(param)
        if category:
            if not category.channels:
                await ctx.send(f"> La catégorie **{category.name}** ne possède pas de salon.")
                return
            if not [channel for channel in category.channels if not channel.permissions_synced]:
                await ctx.send(f"> Les salons de la catégorie **{category.name}** sont déjà tous synchronisés.")
                return
            
            message = None
            if len(category.channels) >= 3:
                message = await ctx.send(f"> Synchronisation des salons de la catégorie **{category.name}** en cours...")

            synchronized = 0
            synchronization_failed = 0

            for channel in category.channels:
                if channel.permissions_synced:
                    continue
                try: 
                    await channel.edit(sync_permissions = True)
                    synchronized += 1
                except: synchronization_failed += 1

            if message:
                try: await message.delete()
                except: pass

            await ctx.send(
                f"> Tentative de synchronisation de la catégorie **{category.name}** effectuée."
                + (f"\n> J'ai synchronisé un total de {synchronized} salon(s)." if synchronized else "")
                + (f"\n> Je n'ai pas pu synchroniser {synchronization_failed} salon(s)." if synchronization_failed else "")
            )
            return

        # ------------------------------------- ALL
        if param.lower() != "all":
            await ctx.send(f"> Le salon ou la catégorie donnée est invalide. Pour tous les salons utilisez `{ctx.clean_prefix}sync all`.")
            return
        
        channel_to_sync = [channel for channel in ctx.guild.channels if (type(channel) != discord.CategoryChannel) and (not channel.permissions_synced) and (channel.category)]
        if not channel_to_sync:
            await ctx.send(f"> Il n'y a pas de salon nécessitant une synchronisation avec sa catégorie.")
            return
        
        message = None
        if len(channel_to_sync) >= 3:
            message = await ctx.send(f"> Synchronisation de tous les salons du serveur en cours...")
            
        synchronized = 0
        synchronization_failed = 0
        for channel in channel_to_sync:
            if channel.permissions_synced:
                continue
            try: 
                await channel.edit(sync_permissions = True)
                synchronized += 1
            except: synchronization_failed += 1

        if message:
            try: await message.delete()
            except: pass

        await ctx.send(
            f"> Tentative de synchronisation de tous les salons effectuée."
            + (f"\n> J'ai synchronisé un total de {synchronized} salon(s)." if synchronized else "")
            + (f"\n> Je n'ai pas pu synchroniser {synchronization_failed} salon(s)." if synchronization_failed else "")
        )


    @commands.command(description = "Configurer et ensuite lancer un giveaway")
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
            embed.add_field(name = "Salon", value = f'<#{data["channel_id"]}>')
            embed.add_field(name = "Emoji", value = data["emoji"])
            embed.add_field(name = "Type d'intéraction", value = data["interaction_type"].capitalize())
            embed.add_field(name = "Couleur (Bouton)", value = data["button_color"].capitalize())
            embed.add_field(name = "Texte (Bouton)", value = data["button_text"])
            embed.add_field(name = "Nombre de gagnants", value = str(data["winners_count"]))
            embed.add_field(name = "Gagnant imposé", value = f"<@{data['imposed_winner']}>" if data["imposed_winner"] else "*Aucun gagnant imposé*")
            embed.add_field(name = "Rôle requis", value = f"<@&{data['required_role']}>" if data["required_role"] else "*Aucun rôle*")
            embed.add_field(name = "Rôle interdit", value = f"<@&{data['prohibited_role']}>" if data["prohibited_role"] else "*Aucun rôle*")
            embed.add_field(name = "Imposer la présence en vocal", value = "Oui" if data["in_vocal_required"] else "Non")

            return embed

        giveaway_data = {
            "reward": "Exemple de récompense",
            "end_at": "2h",
            "channel_id": ctx.channel.id,
            "emoji": "🎉",
            "interaction_type": "button",
            "button_color": "grey", # blue, green, gray or red
            "button_text": "Participer",
            "winners_count": 1,
            "imposed_winner": 0,
            "required_role": 0,
            "prohibited_role": 0,
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
                    discord.SelectOption(label = "Gagnant imposé", value = "imposed_winner", emoji = "👤"),
                    discord.SelectOption(label = "Rôle requis", value = "required_role", emoji = "⛓"),
                    discord.SelectOption(label = "Rôle interdit", value = "prohibited_role", emoji = "🚫"),
                    discord.SelectOption(label = "Imposition de la présence en vocal", value = "in_vocal_required", emoji = "🔊"),
                    discord.SelectOption(label = "Retirer une option", value = "remove_option", emoji = "❌")
                ]
            )
            async def edit_giveaway_select_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                async def delete_message(message):
                    try: await message.delete()
                    except: pass

                async def get_option_name(option_id):
                    for option in select.options:
                        if option.value == option_id:
                            return option.label
                    return None
                
                def check_message_validity(message):
                    return (message.channel == ctx.channel) and (message.author == ctx.author) and (message.content)
                
                await interaction.response.defer()

                # ----------------------------- Obtention d'une réponse
                notes = {
                    "end_at": "Voici quelques exemple de temps valides : `1jours`, `3d`, `4h` , `5minutes`. Maximum 30 jours.",
                    "interaction_type": "Types d'intéractions disponibles : `bouton` et `réaction`",
                    "button_color": "Couleurs disponibles : `bleu`, `rouge`, `vert` et `gris`",
                    "in_vocal_required": "Réponses possibles : `oui` et `non`",
                    "remove_option": "Les options qui peuvent être retiré sont : `gagnant imposé`, `rôle requis` et `rôle interdit`"
                }

                ask_message = await ctx.send(
                    f"> Quel(le) **{await get_option_name(select.values[0])}** souhaitez-vous définir à votre giveaway? Envoyez `cancel` pour annuler."
                    + (f"\n{notes[select.values[0]]}" if select.values[0] in list(notes.keys()) else "")
                )

                try: response_message = await bot.wait_for("message", timeout = 60, check = check_message_validity)
                except asyncio.TimeoutError:
                    await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                    return
                finally: await delete_message(ask_message)
                await delete_message(response_message)

                if response_message.content.lower() == "cancel":
                    await ctx.send("> Action annulée.", delete_after = 2)
                    return

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
                    self.giveaway_data["channel_id"] = channel.id

                if select.values[0] == "emoji":
                    found_emoji = await tools.get_emoji(response_message.content)
                    if not found_emoji:
                        await ctx.send("> Emoji invalide, merci de donner un emoji valide.", delete_after = 2)
                        return
                    self.giveaway_data["emoji"] = found_emoji

                if select.values[0] == "interaction_type":
                    if response_message.content.lower() in ["button", "buttons", "bouton", "boutons"]: new_def = "button"
                    elif response_message.content.lower() in ["reaction", "reactions", "réaction", "réactions"]: new_def = "reaction"
                    else:
                        await ctx.send("> Action annulée, type d'intéraction invalide.", delete_after = 2)
                        return
                    
                    if self.giveaway_data["interaction_type"] == new_def:
                        await ctx.send("> Action annulée, cette valeur est déjà définie.", delete_after = 2)
                        return
                    
                    self.giveaway_data["interaction_type"] = new_def

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
                    if not 1 <= int(response_message.content) <= 50:
                        await ctx.send("> Action annulée, votre nombre de gagnant doit être entre 1 et 50.", delete_after = 2)
                        return
                    if self.giveaway_data["imposed_winner"]:
                        await ctx.send("> Action annulée, votre nombre de gagnant doit forcément être définis à 1 si vous prédéfinissez un gagnant.", delete_after = 2)
                        return
                    
                    self.giveaway_data["winners_count"] = int(response_message.content)

                if select.values[0] == "imposed_winner":
                    user = await searcher.search_user(response_message.content)
                    if not user:
                        await ctx.send("> Action annulée, utilisateur invalide.", delete_after = 2)
                        return

                    self.giveaway_data["imposed_winner"] = user.id
                    self.giveaway_data["winners_count"] = 1

                if select.values[0] in ["required_role", "prohibited_role"]:
                    role = await searcher.search_role(response_message.content)
                    if not role:
                        await ctx.send("> Action annulée, rôle invalide.", delete_after = 2)
                        return
                    
                    previous_value = self.giveaway_data[select.values[0]]
                    self.giveaway_data[select.values[0]] = role.id

                    if self.giveaway_data["required_role"] == self.giveaway_data["prohibited_role"]:
                        self.giveaway_data[select.values[0]] = previous_value
                        await ctx.send("> Action annulée, le rôle requis et le rôle obligatoire ne peuvent pas être identiques.", delete_after = 2)
                        return

                if select.values[0] == "in_vocal_required":
                    if response_message.content.lower() in ["true", "yes", "oui", "o"]: new_def = True
                    elif response_message.content.lower() in ["false", "no", "non", "n"]: new_def = False
                    else:
                        await ctx.send("> Action annulée, réponse invalide.", delete_after = 2)
                        return
                    
                    self.giveaway_data["in_vocal_required"] = new_def                 

                if select.values[0] == "remove_option":
                    if response_message.content.lower() in ["rôle requis", "role requis", "rôle requi", "role requi", "required roles", "required role"]:
                        self.giveaway_data["required_role"] = None
                    elif response_message.content.lower() in ["rôle interdit", "role interdit", "rôle interdits", "rôle interdit", "prohibited role", "prohibited roles"]:
                        self.giveaway_data["prohibited_role"] = None
                    elif response_message.content.lower() in ["gagnant imposé", "gagnant impose", "gagnants imposé", "gagnants impose", "imposed winner", "imposed winners"]:
                        self.giveaway_data["imposed_winner"] = None
                    else:
                        await ctx.send("> Action annulée, réponse invalide.", delete_after = 2)
                        return

                # ----------------------------- Mettre à jours le message de giveaway
                await interaction.message.edit(embed = await get_giveaway_embed(self.giveaway_data))
            
            @discord.ui.button(label = "Envoyer", emoji = "✅")
            async def send_giveaway_button_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await ctx.send("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return

                time = await tools.find_duration(giveaway_data["end_at"]) + datetime.now()
                giveaway_embed = discord.Embed(
                    title = f"Giveaway: {giveaway_data['reward']}",
                    color = await bot.get_theme(interaction.guild.id),
                    description = f"*Intéragissez avec {giveaway_data['emoji']} pour participer.*\nNombre de gagnants : {giveaway_data['winners_count']}",
                ).add_field(
                    name = "Fin du giveaway",
                    value = f"<t:{round(time.timestamp())}:R>"
                )

                if giveaway_data["interaction_type"] == "button":
                    giveaway_embed.set_footer(text = "0 participants")
                
                class GiveawayButton(discord.ui.View):
                    @discord.ui.button(label = giveaway_data["button_text"], custom_id = "giveaway", emoji = giveaway_data["emoji"], style = getattr(discord.ButtonStyle, giveaway_data["button_color"].replace("blue", "blurple")))
                    async def callback(self, button, interaction):
                        pass
                
                channel : discord.Channel = await interaction.guild.fetch_channel(giveaway_data["channel_id"])
                message : discord.Message = await channel.send(embed = giveaway_embed, view = GiveawayButton(timeout = None) if giveaway_data["interaction_type"] == "button" else None)

                if giveaway_data["interaction_type"] == "reaction":
                    await message.add_reaction(giveaway_data["emoji"])

                for data, value in giveaway_data.items():
                    if data == "channel_id":
                        continue
                    if data == "end_at":
                        value = datetime.now() + await tools.find_duration(value)
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    await bot.db.set_data("giveaway", data, value, guild_id = ctx.guild.id, channel_id = channel.id, message_id = message.id)
                await bot.db.set_data("giveaway", "participations", json.dumps([]), guild_id = ctx.guild.id, channel_id = channel.id, message_id = message.id)
                await interaction.message.edit(view = None) 
                await interaction.response.send_message(f"> Votre giveaway **{self.giveaway_data['reward']}** a bien été envoyé dans le salon <#{self.giveaway_data['channel_id']}>.", ephemeral = True)
        
        await ctx.send(view = ManageGiveaway(giveaway_data), embed = await get_giveaway_embed(giveaway_data))


    @commands.command(description = "Mettre fin à un giveaway", usage = "<message>")
    @commands.guild_only()
    async def endgiveaway(self, ctx, giveaway_message : discord.Message):
        giveaway_data = await self.bot.db.execute(f"SELECT * FROM giveaway WHERE guild_id = {ctx.guild.id} AND message_id = {giveaway_message.id}", fetch = True)

        if not giveaway_data:
            await ctx.send(f"> Aucun giveaway actif ne possède l'identifiant `{giveaway_message.id}`.")
            return
        
        giveaway_table_columns = await self.bot.db.get_table_columns("giveaway")
        giveaway = dict(set(zip(giveaway_table_columns, giveaway_data[0])))
        giveaway_link = f"[giveaway {giveaway['reward']}](https://discord.com/channels/{giveaway['guild_id']}/{giveaway['channel_id']}/{giveaway['message_id']})"

        if giveaway["ended"]:
            await ctx.send(f"> Le {giveaway_link} est déjà terminé.")
            return

        now = datetime.now()
        await self.bot.db.set_data("giveaway", "end_at", now.strftime("%Y-%m-%d %H:%M:%S"), guild_id = ctx.guild.id, channel_id = giveaway_message.channel.id, message_id = giveaway_message.id)
        await ctx.send(f"> Le {giveaway_link} est désormais terminé.")


    @commands.command(description = "Reroll un giveaway toujours actif", usage = "<message>")
    @commands.guild_only()
    async def reroll(self, ctx, giveaway_message : discord.Message):
        giveaway_data = await self.bot.db.execute(f"SELECT * FROM giveaway WHERE guild_id = {ctx.guild.id} AND message_id = {giveaway_message.id}", fetch = True)

        if not giveaway_data:
            await ctx.send(f"> Aucun giveaway actif ne possède l'identifiant `{giveaway_message.id}`.")
            return
        
        giveaway_table_columns = await self.bot.db.get_table_columns("giveaway")
        giveaway = dict(set(zip(giveaway_table_columns, giveaway_data[0])))
        giveaway_link = f"[giveaway {giveaway['reward']}](https://discord.com/channels/{giveaway['guild_id']}/{giveaway['channel_id']}/{giveaway['message_id']})"

        if not giveaway["ended"]:
            await ctx.send(f"> Le {giveaway_link} n'est pas encore terminé.")
            return
        
        if giveaway["channel_id"] != ctx.channel:
            channel = ctx.guild.get_channel(giveaway["channel_id"])
            if not channel:
                await ctx.send(f"> Le salon du {giveaway_link} n'existe plus ou je ne peux pas y accéder.")
                return
        else: channel = ctx.channel

        try:
            message = self.bot.get_message(giveaway["message_id"])
            if not message:
                message = await channel.fetch_message(giveaway["message_id"])
        except:
            await ctx.send(f"> Le message du {giveaway_link} n'existe plus ou je ne peux pas y accéder.")
            return
        
        participants = json.loads(giveaway["participations"])
        if (giveaway["winners_count"] == 1) or (giveaway["imposed_winner"]) or (len(participants) == 1):
            await message.reply(f"> Giveaway reroll, le gagnant du giveaway **{giveaway['reward']}** est <@" + str(random.choice(participants) if not giveaway["imposed_winner"] else giveaway["imposed_winner"]) + ">")
        else:
            if len(participants) <= giveaway["winners_count"]:
                winners = [f"<@{user}>" for user in participants]
            else:
                winners = []
                for i in range(giveaway["winners_count"]):
                    winner = random.choice(participants)
                    winners.append(f"<@{winner}>")
                    participants.remove(winner)

            await message.reply(f"> Giveaway reroll, les gagnants du giveaway **{giveaway['reward']}** sont : " + ", ".join(winners[:-1]) + " et " + winners[-1])
        if message.channel != ctx.channel:
            await ctx.send(f"> Le giveaway **{giveaway['reward']}** a été reroll dans le salon {channel.mention}.")


    @commands.command(description = "Voir les giveaways actuellements actifs sur le serveur")
    @commands.guild_only()
    async def giveaways(self, ctx):
        paginator_creator = PaginatorCreator()
        giveaways = await self.bot.db.execute(f"SELECT * FROM giveaway WHERE guild_id = {ctx.guild.id} ORDER BY end_at DESC", fetch = True)

        if not giveaways:
            await ctx.send("> Il n'y a aucun giveaways actifs sur ce serveur.")
            return
        
        giveaways_columns = await self.bot.db.get_table_columns("giveaway")
        giveaways = [dict(set(zip(giveaways_columns, giveaway_data))) for giveaway_data in giveaways]
        giveaways_text_data = []

        for giveaway in giveaways:
            giveaway_link = f"[Giveaway {giveaway['reward']}](https://discord.com/channels/{giveaway['guild_id']}/{giveaway['channel_id']}/{giveaway['message_id']}) ({'Se termine' if giveaway['end_at'] > datetime.now() else 'Terminé'} <t:{round(giveaway['end_at'].timestamp())}:R>)"
            giveaways_text_data.append(giveaway_link)
        
        paginator = await paginator_creator.create_paginator(
            title = "Giveaways actifs",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = giveaways_text_data,
            comment = "*Les données d'un giveaway restent accessibles jusqu'à 3h après sa fin.\nDonc vous pouvez le reroll uniquements durant ce délai.*"
        )

        if type(paginator) == list: await ctx.send(embed = paginator[0])
        else: await paginator.send(ctx)


    @commands.command(description = "Ajouter/Retirer un ou plusieurs rôle à tous les membres/bots")
    @commands.guild_only()
    async def massiverole(self, ctx):
        class_self = self

        async def get_massiverole_embed(data):
            embed = discord.Embed(
                title = "Paramètres du massiverole",
                description = "*Si vous nous fournissez accidentellement un rôle à ajouter avec des permissions dangereuses, vous en assumerez la responsabilité.*",
                color = await self.bot.get_theme(ctx.guild.id)
            )

            # Calcul des estimations
            users = 0
            for member in ctx.guild.members:
                if not data["roles"]:
                    continue
                if ((member.bot) and ("bot" not in data["target"])) or ((not member.bot) and ("human" not in data["target"])):
                    continue

                member_roles_ids = [role.id for role in member.roles]
                
                if not all([ignored_role_id not in member_roles_ids for ignored_role_id in data["ignored_roles"]]): continue
                if not all([required_role_id in member_roles_ids for required_role_id in data["required_roles"]]): continue

                if data["action"] == "add":
                    if all([role_id in member_roles_ids for role_id in data["roles"]]): continue
                else:
                    if all([role_id not in member_roles_ids for role_id in data["roles"]]): continue
                users += 1

            hours, remainder = divmod(users, 3600)
            minutes, remainder = divmod(remainder, 60)
            seconds = remainder

            text = ""
            if hours and minutes: text = f"{hours} heures, {minutes} minutes"
            elif hours: text = f"{hours} heures"
            elif minutes: text = f"{minutes} minutes"
            if text: text += f" et {seconds} secondes"
            else: text += f"{seconds} secondes"

            embed.add_field(name = "Action", value = "Ajouter" if data["action"] == "add" else "Retirer")
            embed.add_field(name = "Cible", value = data["target"].replace("human", "Humains").replace("bot", "Bots").replace("_", " & "))
            embed.add_field(name = "Durée estimée", value = text)
            embed.add_field(name = "Rôles à ajouter/retirer", value = "<@&" + f">\n<@&".join([str(role_id) for role_id in data["roles"]]) + ">" if data["roles"] else "*Aucun rôles*")
            embed.add_field(name = "Rôles requis", value = "<@&" + f">\n<@&".join([str(role_id) for role_id in data["required_roles"]]) + ">" if data["required_roles"] else "*Aucun rôles*")
            embed.add_field(name = "Rôles ignorés", value = "<@&" + f">\n<@&".join([str(role_id) for role_id in data["ignored_roles"]]) + ">" if data["ignored_roles"] else "*Aucun rôles*")

            return embed

        massiverole_data = {
            "action": "add", # add/remove
            "roles": [],
            "target": "human_bot", # human/bot/human_bot
            "required_roles": [],
            "ignored_roles": [],
        }

        bot = self.bot
        class MangageMassiveRole(MyViewClass):
            def __init__(self, massiverole_data):
                super().__init__(timeout = 200)
                self.massiverole_data = massiverole_data

            @discord.ui.select(
                placeholder = "Choisir un paramètre",
                options = [
                    discord.SelectOption(label = "Action", emoji = "⚡", value = "action"),
                    discord.SelectOption(label = "Cible", emoji = "🎯", value = "target"),
                    discord.SelectOption(label = "Rôles à ajouter/retirer", emoji = "➕", value = "roles"),
                    discord.SelectOption(label = "Rôles requis", emoji = "📌", value = "required_roles"),
                    discord.SelectOption(label = "Rôles ignorés", emoji = "🚫", value = "ignored_roles")
                ]
            )
            async def select_manage_massiverole_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if select.values[0] == "action":
                    if self.massiverole_data["action"] == "add": self.massiverole_data["action"] = "remove"
                    else: self.massiverole_data["action"] = "add"

                    await interaction.edit(embed = await get_massiverole_embed(self.massiverole_data))
                
                if select.values[0] == "target":
                    previous_view = self
                    class ChooseTarget(MyViewClass):
                        def __init__(self):
                            super().__init__(timeout = 180)

                        @discord.ui.select(
                            placeholder = "Choisir des cibles",
                            options = [
                                discord.SelectOption(label = "Humains", value = "human", emoji = "👤"),
                                discord.SelectOption(label = "Bots", value = "bot", emoji = "🤖")
                            ],
                            max_values = 2
                        )
                        async def choose_target_callback(self, select, interaction):
                            if interaction.user != ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                return
                            
                            previous_view.massiverole_data["target"] = "_".join(select.values)
                            await interaction.edit(view = previous_view, embed = await get_massiverole_embed(previous_view.massiverole_data))
                            
                        @discord.ui.button(label = "Choisissez des cibles", style = discord.ButtonStyle.primary, disabled = True)
                        async def button_indicator_callback(self, button, interaction):
                            pass

                        @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                        async def comeback_button_callback(self, button, interaction):
                            if interaction.user != ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                return
                            
                            await interaction.edit(view = previous_view)

                    await interaction.edit(view = ChooseTarget())

                if select.values[0] in ["roles", "ignored_roles", "required_roles"]:
                    def get_option_name(option_id):
                        return [option.label for option in select.options if option.value ==option_id][0]
                    
                    option_id = select.values[0]
                    option_name = get_option_name(option_id)

                    if len(self.massiverole_data[option_id]) >= 10:
                        await interaction.response.send_message(f"> Vous ne pouvez pas ajouter plus de 10 rôles à vos {option_name}.", ephemeral = True)
                        return

                    previous_view = self
                    class ChooseRole(MyViewClass):
                        def __init__(self):
                            super().__init__(timeout = 180)

                        @discord.ui.select(
                            placeholder = "Choisir des rôles",
                            select_type = discord.ComponentType.role_select,
                            max_values = 10
                        )
                        async def choose_role_callback(self, select, interaction):
                            if interaction.user != ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                return
                            
                            if option_id == "roles":
                                not_assignable = []
                                
                                for role in select.values:
                                    role_instance = interaction.guild.get_role(role.id)
                                    if not role_instance.is_assignable():
                                        not_assignable.append(role_instance.mention)

                                if not_assignable:
                                    await interaction.response.send_message("> Vos modifications n'ont pas étés prises en comptes, " + ("les rôles suivants ne sont pas assignables" if len(not_assignable) > 1 else "le rôle suivant n'est pas assignable") + " : \n" + ", ".join(not_assignable) + ".", ephemeral = True)
                                    return
                            
                            opposed_options = ["roles", "ignored_roles", "required_roles"]
                            opposed_options.remove(option_id)
                            opposed_roles = previous_view.massiverole_data[opposed_options[0]] + previous_view.massiverole_data[opposed_options[1]]

                            previous_view.massiverole_data[option_id] = [role.id for role in select.values if role.id not in opposed_roles]
                            not_added_roles_count = sum([1 for role in select.values if role.id in opposed_roles])

                            await interaction.message.edit(view = previous_view, embed = await get_massiverole_embed(previous_view.massiverole_data))
                            
                            if not not_added_roles_count:
                                await interaction.response.defer()
                            else:
                                await interaction.response.send_message(f"> Vos modifications ont bien étés prises en compte, mais un total de {not_added_roles_count} rôle(s) n'a pas été ajouté car les {option_name.lower()} ne peuvent pas être dans les {get_option_name(opposed_options[0]).lower()} ou dans les rôles {get_option_name(opposed_options[1]).lower()}.", ephemeral = True)
   
                        @discord.ui.button(label = f"Choisissez des {option_name.lower()}", style = discord.ButtonStyle.primary, disabled = True)
                        async def button_indicator_callback(self, button, interaction):
                            pass

                        @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                        async def comeback_button_callback(self, button, interaction):
                            if interaction.user != ctx.author:
                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                return
                            
                            await interaction.edit(view = previous_view)
                        
                    await interaction.edit(view = ChooseRole())

            @discord.ui.button(label = "Lancer", emoji = "👥")
            async def launch_button_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if not self.massiverole_data["roles"]:
                    await interaction.response.send_message("> Vous n'avez pas fournis de rôle à ajouter.", ephemeral = True)
                    return
                
                roles_to_edit = []
                for role_id in self.massiverole_data["roles"]:
                    role = interaction.guild.get_role(role_id)
                    if not role:
                        await interaction.response.send_message(f"> L'id de rôle `{role_id}` n'éxiste plus ou alors je n'y ai plus accès.", ephemeral = True)
                        return
                    roles_to_edit.append(role)

                if class_self.massiverole_loading.get(interaction.guild.id, False):
                    await interaction.response.send_message("> Un massiverole est déjà en cours sur ce serveur, merci de patienter que celui-ci se termine.", ephemeral = True)
                    return

                class StopMassiveRole(MyViewClass):
                    @discord.ui.button(label = "Arrêter", style = discord.ButtonStyle.danger, custom_id = f"massiverole_stop_{interaction.user.id}")
                    async def stop_massiverole_callback(self, button, interaction):
                        pass

                async def get_massiverole_loading_embed(added_count : int):
                    embed = discord.Embed(
                        title = "Massiverole en cours...",
                        color = await bot.get_theme(interaction.guild.id),
                    )

                    embed.add_field(name = "Membres affectés", value = str(added_count))
                    return embed

                class_self.massiverole_loading[interaction.guild.id] = True
                await interaction.edit(embed = await get_massiverole_loading_embed(0), view = StopMassiveRole(timeout = None))

                added_count = 0
                for member in interaction.guild.members:
                    if not class_self.massiverole_loading.get(interaction.guild.id, False):
                        break
                    if ((member.bot) and ("bot" not in self.massiverole_data["target"]) or ((not member.bot) and ("human" not in self.massiverole_data["target"]))):
                        continue
                        
                    member_roles_ids = [role.id for role in member.roles]
                    if self.massiverole_data["required_roles"]:
                        if not all([role_id in member_roles_ids for role_id in self.massiverole_data["required_roles"]]):
                            continue
                    if self.massiverole_data["ignored_roles"]:
                        if not all([role_id not in member_roles_ids for role_id in self.massiverole_data["ignored_roles"]]):
                            continue
                    if self.massiverole_data["action"] == "add":
                        if all([role_id in member_roles_ids for role_id in self.massiverole_data["roles"]]):
                            continue
                    else:
                        if all([role_id not in member_roles_ids for role_id in self.massiverole_data["roles"]]):
                            continue

                    try:
                        if self.massiverole_data["action"] == "add":
                            await member.add_roles(*roles_to_edit, reason = f"[{interaction.user.display_name} - {interaction.user.id}] Massiverole")
                        else:
                            await member.remove_roles(*roles_to_edit, reason = f"[{interaction.user.display_name} - {interaction.user.id}] Massiverole")
                        added_count += 1

                        if (added_count) and (added_count % 5 == 0):
                            try: await interaction.message.edit(embed = await get_massiverole_loading_embed(added_count))
                            except: pass

                        await asyncio.sleep(1)
                    except: pass

                massiverole_loading_embed = await get_massiverole_loading_embed(added_count)
                massiverole_loading_embed.title = "Massiverole terminé" if class_self.massiverole_loading.get(interaction.guild.id, None) else "Massiverole annulé"
                
                try: await interaction.message.edit(embed = massiverole_loading_embed, view = None)
                except: pass
                if class_self.massiverole_loading.get(interaction.guild.id, False):
                    await interaction.channel.send(interaction.user.mention, embed = discord.Embed(title = f"Massiverole terminé", color = await bot.get_theme(interaction.guild.id)))
                if interaction.guild.id in class_self.massiverole_loading.keys():
                    del class_self.massiverole_loading[interaction.guild.id]                

            @discord.ui.button(emoji = "🗑", style = discord.ButtonStyle.danger)
            async def delete_button_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.edit(embed = discord.Embed(title = "Configuration du massiverole annulée", color = await bot.get_theme(interaction.guild.id)), view = None)

        await ctx.send(embed = await get_massiverole_embed(massiverole_data), view = MangageMassiveRole(massiverole_data))


    @commands.command(description = "Afficher un menu intéractif pour créer et envoyer un embed")
    @commands.bot_has_permissions(embed_links = True, manage_messages = True, read_messages = True)
    @commands.guild_only()
    async def embed(self, ctx):
        embed = discord.Embed(description = "ㅤ" )
        bot = self.bot

        def formate_embed(data) -> discord.Embed:
            embed = discord.Embed(
                title = data["title"],
                description = data["description"],
                color = data["color"],
                timestamp = data["timestamp"],
                thumbnail = data["thumbnail"]
            )

            if data["footer"]["text"]:
                embed.set_footer(text = data["footer"]["text"], icon_url = data["footer"]["icon_url"])
            if data["author"]["name"]:
                embed.set_author(name = data["author"]["name"], icon_url = data["author"]["icon_url"], url = data["author"]["url"])
            if data["fields"]:
                for field_data in data["fields"]:
                    embed.add_field(name = field_data["name"], value = field_data["value"], inline = field_data["inline"])
            if data["image"]:
                embed.set_image(url = data["image"])

            return embed

        def get_total_characters(data):
            total = 0
            if data["title"]: total += len(data["title"])
            if data["description"]: total += len(data["description"])
            for field_data in data["fields"]: total += len(field_data["name"]) + len(field_data["value"])
            if data["footer"]["text"]: total += len(data["footer"]["text"])
            if data["author"]["name"]: total += len(data["author"]["name"])
            return total

        def get_an_update_of_backups_buttons(current_self):
            back = current_self.get_item("back")
            current_self.remove_item(back)
            back.disabled = False if current_self.embeds_backup else True
            current_self.add_item(back)

            restaure = current_self.get_item("restaure")
            current_self.remove_item(restaure)
            restaure.disabled = False if current_self.embeds_backup_of_backup else True
            current_self.add_item(restaure)

            return current_self
        
        async def delete_message(message):
            async def task(message):
                await message.delete()
            loop = asyncio.get_event_loop()
            try: loop.create_task(task(message))
            except: pass


        max_sizes = {
            "title": 256,
            "description": 4096,
            "fields": 25,
            "field_name": 256,
            "field_value": 1024,
            "footer_text": 2048,
            "author_name": 256,
            "sum": 6000
        }

        class EmbedCreator(discord.ui.View):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.embed = {
                    "title": None,
                    "description": "ㅤ",
                    "color": None,
                    "footer": {
                        "text": None,
                        "icon_url": None
                    },
                    "timestamp": None,
                    "thumbnail": None,
                    "image": None,
                    "author": {
                        "name": None,
                        "icon_url": None,
                        "url": None
                    },
                    "fields": [
                        # field exemple {"name": "My field name", "value": "My field value", "inline": True}
                    ],
                }
                self.embeds_backup = []
                self.embeds_backup_of_backup = []

            async def on_timeout(self):
                try: await self.message.edit(view = None)
                except: pass
            
            @discord.ui.select(
                placeholder = "Modifier l'embed",
                options = [
                    discord.SelectOption(label = "Titre", emoji = "✏", value = "title"),
                    discord.SelectOption(label = "Description", emoji = "📝", value = "description"),
                    discord.SelectOption(label = "Couleur", emoji = "⚪", value = "color"),
                    discord.SelectOption(label = "Footer", emoji = "🏷", value = "footer"),
                    discord.SelectOption(label = "Timestamp", emoji = "⏱", value = "timestamp"),
                    discord.SelectOption(label = "Image", emoji = "🖼", value = "image"),
                    discord.SelectOption(label = "Thumbnail", emoji = "🎴", value = "thumbnail"),
                    discord.SelectOption(label = "Auteur", emoji = "👤", value = "author"),
                    discord.SelectOption(label = "Ajouter un champ", emoji = "➕", value = "field_add"),
                    discord.SelectOption(label = "Retirer un champ", emoji = "➖", value = "field_remove"),
                    discord.SelectOption(label = "Copier un embed", emoji = "⤵", value = "copy_embed")
                ]
            )
            async def select_callback(self, select, interaction):
                if interaction.user != ctx.author: 
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                await interaction.response.defer()
                
                # Données temporaires utile pour check par exemple : si le nombre de caractère total > 6000, sans modifier self.embed / Ou alors pour éviter les problèmes d'objets / Ou alors pour éviter de devoir faire de grosse manipulation pour revenir en arrière quand une valeure est fausse.
                temporary_data = self.embed.copy()
                # Sauvegarder une ancienne version de self.embed pour ensuite l'ajouter dans self.embed_backups si des changements ont eu lieu
                previous_embed_copy = self.embed.copy()

                def response_check(message):
                    return (message.author == ctx.author) and (message.channel == ctx.channel)
                
                message = None
                if select.values[0] not in ["footer", "author", "field_add", "field_remove", "timestamp", "copy_embed"]:
                    message = await ctx.send(f"Quel sera la nouvelle valeur de votre **{select.values[0].replace('color', 'couleur')}** ? Envoyez `cancel` pour annuler")

                    # Attendre la réponse de l'utilisateur, après 60 secondes d'attente, l'action est annulée
                    try: response = await bot.wait_for('message', timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                        return
                    finally:
                        await delete_message(message)
                    await delete_message(response)

                    # @Check Annulation
                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 3)
                        return

                # ---------------------------- TITRE & DESCRIPTION ----------------------------
                if select.values[0] in ["title", "description"]:
                    if len(response.content) == 0:
                        await ctx.send(f"> Votre {select.values[0]} ne peut pas être vide.")
                        return
                    if len(response.content) > max_sizes[select.values[0]]:
                        await ctx.send(f"> Vous ne pouvez pas dépasser {max_sizes[select.values[0]]} caractères pour votre **{select.values[0]}**.", delete_after = 3)
                        return
                    
                    # @Check total embed < 6000 caractères
                    temporary_data[select.values[0]] = response.content
                    if get_total_characters(temporary_data) > 6000:
                        await ctx.send("> Le nombre total de charactère dans votre embed ne doit pas dépasser les 6000 caractères.", delete_after = 3)
                        return

                    temporary_data[select.values[0]] = response.content
                    self.embed = temporary_data.copy()

                # ---------------------------- IMAGE & THUMBNAIL ----------------------------
                if select.values[0] in ["image", "thumbnail"]:
                    if not response.content.startswith(("https://", "http://")) or " " in response.content:
                        await ctx.send("> Action annulée, lien d'image invalide.", delete_after = 3)
                        return
                    
                    temporary_data[select.values[0]] = response.content
                    self.embed = temporary_data.copy()

                # ---------------------------- COLOUR ----------------------------
                if select.values[0] == "color":
                    try: temporary_data["color"] = int(response.content.removeprefix("#"), 16)
                    except:
                        await ctx.send("> La couleur HEX donnée est invalide (exemple valide : `#FF12F4`).", delete_after = 3)
                        return

                    self.embed = temporary_data.copy()

                # ---------------------------- FOOTER ----------------------------
                if select.values[0] == "footer":
                    # -------------- FOOTER / TEXT
                    message1 = await ctx.send("Quel sera le **texte** de votre **footer** ? Envoyez `cancel` pour annuler.")
                    
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                        return
                    finally:
                        await delete_message(message1)
                    await delete_message(response)

                    # @Check pas vide
                    if not response.content:
                        await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_fater = 2)
                        return

                    # @Check annulation
                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 3)
                        return
                     
                    # @Check taille footer text < max(taille_footer_text)
                    if len(response.content) > max_sizes["footer_text"]:
                        await ctx.send(f"> Vous ne pouvez pas dépasser {max_sizes['footer_text']} caractères pour votre **footer**.", delete_after = 3)
                        return
                    
                    # Pour éviter les bug dans la liste des données d'embed self.embed_backups (car le dictionnaire footer est considéré comme le même objet PARTOUT)
                    temporary_data["footer"] = temporary_data["footer"].copy()

                    # @Check total embed < 6000 caractères
                    temporary_data["footer"]["text"] = response.content
                    if get_total_characters(temporary_data) > 6000:
                        await ctx.send(f"> Le nombre total de charactère dans votre embed ne doit pas dépasser les 6000 caractères.", delete_after = 3)

                    # -------------- FOOTER / ICON
                    message2 = await ctx.send("Quel sera l'**icône** du **footer** (un lien)? Envoyez `skip` pour ne pas modifier et `delete` pour retirer.")
                    try: response : discord.Message = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée.", delete_after = 3)
                        return
                    finally:
                        await delete_message(message2)
                    await delete_message(response)

                    if not response.content:
                        await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_fater = 2)
                        return
                    if response.content.lower() == "delete":
                        temporary_data["footer"]["icon_url"] = None
                    
                    if response.content.lower() not in ["skip", "delete"]:
                        if not response.content.startswith(("https://", "http://")) or " " in response.content:
                            await ctx.send("> Votre image doit être un lien valide.")
                            return
                        
                        temporary_data["footer"]["icon_url"] = response.content
                    self.embed = temporary_data.copy()

                # ---------------------------- TIMESTAMP ----------------------------
                if select.values[0] == "timestamp":
                    message1 = await ctx.send(
                        "Quel est la date de votre timestamp? Utilisez `cancel` pour annuler.\n"
                        + "Votre date doit être sous forme `30/12/2000 15:30` ou alors `now` pour la date actuel."
                    )

                    try:
                        response = await bot.wait_for("message", check = response_check, timeout = 60)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                        return
                    finally:
                        await delete_message(message1)
                    await delete_message(response)

                    if response.content.lower() != "now":
                        try: date = datetime.strptime(response.content, '%d/%m/%Y %H:%M')
                        except:
                            await ctx.send("> Action annulée, durée invalide.", delete_after = 3)
                            return
                    else: date = datetime.now()
                    temporary_data["timestamp"] = date
                    self.embed = temporary_data.copy()

                # ---------------------------- AUTHOR ----------------------------
                if select.values[0] == "author":

                    # -------------- AUTHOR / NAME
                    message1 = await ctx.send("Quel sera le **texte** (ou nom) de l'auteur? Evnoyez `cancel` pour annuler.")
                    try:
                        response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                        return
                    finally: await delete_message(message1)
                    await delete_message(response)

                    if not response.content:
                        await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_fater = 2)
                        return
                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 3)
                        return
                    if len(response.content) > max_sizes["author_name"]:
                        await ctx.send(f"> Action annulée, nom d'auteur trop long (plus de {max_sizes['author_name']} caractères).", delete_after = 3)
                        return
                    
                    temporary_data["author"]["name"] = response.content
                    if get_total_characters(temporary_data) > 6000:
                        await ctx.send(f"> Action annulée, le nombre total de caractère dans votre embed ne doit pas dépasser 6000 caractères.", delete_after = 3)
                        return
                    
                    # -------------- AUTHOR / ICON_URL
                    message2 = await ctx.send("Quel sera l'**icône** de l'auteur? Envoyez `skip` pour ne pas en mettre ou `delete` pour supprimer celle actuelle.")
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                        return
                    finally: await delete_message(message2)
                    await delete_message(response)

                    if not response.content:
                        await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_after = 2)
                        return
                    if response.content.lower() == "delete":
                        temporary_data["author"]["icon_url"] = None
                    if response.content.lower() not in ["skip", "delete"]:
                        if not response.content.startswith(("https://", "http://")) or " " in response.content:
                            await ctx.send("> Action annulée, image invalide.", delete_after = 3)
                            return
                        temporary_data["author"]["icon_url"] = response.content

                    # -------------- AUTHOR / URL
                    message3 = await ctx.send("Quel sera l'**url** vers lequel sera redirigé les utilisateurs qui appuiyeront sur le nom de l'auteur? Envoyez `skip` pour ne pas en mettre ou `delete` pour supprimer celui actuel.")
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                        return
                    finally:
                        await delete_message(message3)
                    await delete_message(response)

                    if not response.content:
                        await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_fater = 2)
                        return
                    if response.content.lower() == "delete":
                        temporary_data["author"]["url"] = None
                    if response.content.lower() not in ["delete", "skip"]:
                        if not response.content.startswith(("https://", "http://")) or " " in response.content:
                            await ctx.send("> Action annulée, lien invalide.", delete_after = 3)
                            return
                        
                        temporary_data["author"]["url"] = response.content
                    
                    self.embed = temporary_data.copy()

                # ---------------------------- ADD FIELD ----------------------------
                if select.values[0] == "field_add":
                    # J'ajoute cette ligne pour que tous les dictionnaires dans self.embed_backups n'est pas en valeur "fields" un même OBJET, sinon, quand on modifie une valeur ici, alors on modifie PARTOUT.
                    temporary_data["fields"] = temporary_data["fields"].copy()

                    # -------------- ADD FIELD / FIELD NAME & FIELD VALUE
                    for data_type in ["name", "value"]:
                        message = await ctx.send(f"Quel sera la valeur de votre **{data_type}** de field? Envoyez `cancel` pour annuler.")
                        try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                        except asyncio.TimeoutError:
                            await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                            return
                        finally: await delete_message(message)
                        await delete_message(response)

                        if not response.content:
                            await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_fater = 2)
                            return
                        if response.content.lower() == "cancel":
                            await ctx.send("> Action annulée.", delete_after = 3)
                            return
                        if len(response.content) > max_sizes["field_name"]:
                            await ctx.send(f"> Action annulée, la valeur de vote {data_type} peut pas dépasser {max_sizes[data_type]} caractères.", delete_after = 3)
                            return
                        
                        if data_type == "name":
                            temporary_data["fields"].append(
                                {"name": response.content, "value": "", "inline": None}
                            )
                        else: temporary_data["fields"][-1]["value"] = response.content
                        
                        if get_total_characters(temporary_data) > 6000:
                            await ctx.send("> Action annulée, votre embed ne peut pas faire plus de 6000 caractères.", delete_after = 3)
                            return

                    # -------------- FIELD INLINE OR NOT
                    message = await ctx.send("Souhaitez-vous que votre field soit aligné avec les autres fields (Répondez par `Oui` ou par `Non`)?")
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                        return
                    finally: await delete_message(message)
                    await delete_message(response)
                    
                    if response.content.lower() in ["yes", "oui"]: temporary_data["fields"][-1]["inline"] = True
                    else: temporary_data["fields"][-1]["inline"] = False

                    self.embed = temporary_data.copy()

                # ---------------------------- REMOVE FIELD ----------------------------
                if select.values[0] == "field_remove":
                    if not len(self.embed["fields"]):
                        await ctx.send("> Aucun field n'a été créé.", delete_after = 3)
                        return

                    message = await ctx.send("Quel est la **position** du field (avec un chiffre de 1 à 25) ou alors le nom du field (chaîne de cractère)?")
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                        return
                    finally: await delete_message(message)
                    await delete_message(response)

                    if response.content.isdigit():
                        index = int(response.content)
                        if not 1 <= index <= len(self.embed["fields"]):
                            await ctx.send("> Action annulé, position de field inéxistant.", delete_after = 3)
                            return
                        
                        index -= 1
                        del self.embed["fields"][index]
                    else:
                        field_names = [field_data["name"].lower() for field_data in self.embed["fields"]]
                        if response.content.lower() not in field_names:
                            await ctx.send("> Action annulée, nom de field invalide.", delete_after = 3)
                            return
                        self.embed["fields"] = [field_data for field_data in self.embed["fields"] if field_data["name"].lower() != response.content.lower()]
                
                # -------------- COPY EMBED
                if select.values[0] == "copy_embed":
                    message = await ctx.send("Quel est le **lien du message** contenant l'embed?")
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                        return
                    finally: await delete_message(message)
                    await delete_message(response)

                    response_content = response.content.removeprefix(f"https://discord.com/channels/{interaction.guild.id}/")
                    response_content = response_content.split("/")

                    if not ((len(response_content) == 2) or (all(element.isdigit() for element in response_content))):
                        await ctx.send("> Action annulée, Le lien donné n'est pas valide.", delete_after = 3)
                        return
                    channel = interaction.guild.get_channel(int(response_content[0]))
                    if not channel:
                        await ctx.send("> Action annulée, le salon du lien est invalide ou inaccessible.", delete_after = 3)
                        return
                    try:
                        message : discord.Message = await channel.fetch_message(int(response_content[1]))
                    except:
                        await ctx.send("> Action annulée, Le message du lien donné est invalide ou inaccessible.", delete_after = 3)
                        return
                    
                    if not message.embeds:
                        await ctx.send("> Action annulée, le message donné ne contient pas d'embed.", delete_after = 3)
                        return

                    embed_to_copy = message.embeds[0].to_dict()
                    self.embed["title"] = embed_to_copy.get("title", None)
                    self.embed["description"] = embed_to_copy.get("description", None)
                    self.embed["color"] = embed_to_copy.get("color", None)
                    self.embed["footer"]["text"] = embed_to_copy.get("footer", {}).get("text", None)
                    self.embed["footer"]["icon_url"] = embed_to_copy.get("footer", {}).get("icon_url", None)
                    self.embed["timestamp"] = embed_to_copy.get("timestamp", None)
                    self.embed["thumbnail"] = embed_to_copy.get("thumbnail", None)
                    self.embed["image"] = embed_to_copy.get("image", None)
                    self.embed["author"]["name"] = embed_to_copy.get("author", {}).get("name", None)
                    self.embed["author"]["url"] = embed_to_copy.get("author", {}).get("url", None)
                    self.embed["author"]["icon_url"] = embed_to_copy.get("author", {}).get("icon_url", None)
                    self.embed["fields"] = embed_to_copy.get("fields", None)

                # Mettre à jour les backups
                self.embeds_backup.append(previous_embed_copy.copy())
                self.embeds_backup_of_backup = []

                # Mettre à jours les bouttons backups
                self = get_an_update_of_backups_buttons(self)
                
                # Mettre à jours l'embed
                await interaction.message.edit(embed = formate_embed(self.embed), view = self)

            @discord.ui.button(label = "Envoyer", emoji = "✅", style = discord.ButtonStyle.success)
            async def send(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                embed_to_send = self.embed
                if embed_to_send["description"] == "ㅤ": embed_to_send["description"] = None

                if get_total_characters(embed_to_send) <= 1:
                    await interaction.response.send_message("> Vous ne pouvez pas envoyer un embed vide.", ephemeral = True)
                    return
                
                embed_menu = self

                class ChooseDestination(discord.ui.View):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)

                    async def on_timeout(self):
                        try: self.message.edit(view = None)
                        except: pass

                    @discord.ui.button(
                        label = "Envoyer dans un salon",
                        emoji = "📩"
                    )
                    async def button_channel_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        await interaction.response.defer()
                        
                        def response_check(message):
                            return (message.author == ctx.author) and (message.channel == ctx.channel)
                        
                        msg = await interaction.channel.send("Dans quel salon souhaitez-vous envoyer l'embed?")
                        try: response = await bot.wait_for("message", check = response_check, timeout = 60)
                        except asyncio.TimeoutError:
                            await interaction.channel.send("> Action annulée, 1 minute dépassée.", delete_after = 3)
                            return
                        finally:
                            await delete_message(msg)

                        searcher = Searcher(bot, interaction)
                        channel = await searcher.search_channel(response.content)

                        if not channel:
                            await interaction.channel.send("> Salon invalide.")
                            return
                        
                        try: await channel.send(embed = formate_embed(embed_to_send))
                        except:
                            await interaction.channel.send("> Impossible d'envoyer l'embed dans le salon demandé, vérifiez mes permissions.", delete_after = 3)
                            return
                        
                        await interaction.message.edit(
                            embed = discord.Embed(
                                title = f"Message envoyé dans le salon #{channel.name}.",
                                color = await bot.get_theme(interaction.guild.id),
                                url = f"https://discord.com/channels/{interaction.guild.id}/{channel.id}"
                            ),
                            view = None
                        )

                    @discord.ui.button(
                        label = "Modifier un message du bot",
                        emoji = "✏"
                    )
                    async def button_message_edit_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        await interaction.response.defer()

                        def response_check(message):
                            return (message.author == ctx.author) and (message.channel == ctx.channel)
                        
                        msg = await interaction.channel.send("Quel est le **lien** du message?")
                        try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                        except asyncio.TimeoutError:
                            await interaction.channel.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 3)
                            return
                        finally: await delete_message(msg)
                        await delete_message(response)

                        result = response.content.removeprefix(f"https://discord.com/channels/{interaction.guild.id}/")
                        result = result.split("/")

                        if len(result) != 2:
                            await interaction.channel.send_message("> Lien de message invalide.", delete_after = 3)
                            return
                        for number in result:
                            if not number.isdigit():
                                await interaction.channel.send_message("> Lien de message invalide.", delete_after = 3)
                                return

                        try: channel = await interaction.guild.fetch_channel(int(result[0]))
                        except:
                            await interaction.channel.send_message("> Lien de message invalide.", delete_after = 3)
                            return

                        try: message = await channel.fetch_message(int(result[1]))
                        except:
                            await interaction.channel.send_message("> Lien de message invalide.", delete_after = 3)
                            return
                        
                        if message.author != bot.user:
                            await interaction.channel.send("> Je ne suis pas l'auteur du message donné.", delete_after = 3)
                            return
                        
                        try: await message.edit(embed = formate_embed(embed_to_send))
                        except:
                            await interaction.channel.send("> Impossible de modifier le message, vérifiez que j'ai les permissions nécessaires pour le faire.", delete_after = 3)
                            return

                        await interaction.message.edit(
                            embed = discord.Embed(
                                title = "Le message donné a été modifié.",
                                url = response.content,
                                color = await bot.get_theme(ctx.guild.id)
                            ),
                            view = None
                        )   

                    @discord.ui.button(
                        label = "Envoyer à un utilisateur",
                        emoji = "📧",
                        row  = 0
                    )
                    async def button_user_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        def response_check(message):
                            return (message.author == ctx.author) and (message.channel == ctx.channel)
                        
                        await interaction.response.defer()
                        msg = await interaction.channel.send("Quel sera l'**utilisateur** qui recevra le message?")
                        try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                        except asyncio.TimeoutError:
                            await interaction.channel.send("> Action annulée, 1 minute écoulée.", delete_after = 3)
                            return
                        finally: await delete_message(msg)
                        await delete_message(response)

                        searcher = Searcher(bot, ctx)
                        user = await searcher.search_user(response.content)

                        if not user:
                            await ctx.send("> Utilisateur invalide.", delete_after = 3)
                            return
                        
                        try: await user.send(embed = formate_embed(embed_to_send))
                        except:
                            await interaction.channel.send(f"> Impossible d'envoyer l'embed à {user.mention}, vérifiez l'autorisation des messages privés avec le bot.", allowed_mentions = None, delete_after = 3)
                            return
                        
                        await interaction.message.edit(
                            embed = discord.Embed(
                                title = f"L'embed a correctement été envoyé à {user.display_name}.",
                                color = await bot.get_theme(ctx.guild.id)
                            ),
                            view = None
                        )

                    @discord.ui.button(
                        label = "Définir comme embed de bienvenue",
                        emoji = "📝",
                        row = 1
                    )
                    async def button_set_joins_embed_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        permission_manager = PermissionsManager(bot)
                        configuration_cog = bot.get_cog("Configuration")
                        joins_command = [command for command in configuration_cog.get_commands() if command.name == "joins"][0]
                        bot_prefix = await bot.get_prefix(ctx.message)

                        if not await permission_manager.can_use_cmd(ctx, joins_command):
                            await interaction.response.send_message(f"> Pour définir un embed de bienvenue, vous devez avoir accès à la commande `{bot_prefix}joins`.")
                            return

                        await bot.db.set_data("joins", "embed", json.dumps(embed_menu.embed), guild_id = interaction.guild.id)
                        await interaction.message.edit(
                            embed = discord.Embed(
                                title = f"L'embed de bienvenue a correctement été définis",
                                color = await bot.get_theme(ctx.guild.id)
                            ),
                            view = None
                        )

                    @discord.ui.button(
                        label = "Définir comme embed d'adieu",
                        emoji = "📝",
                        row = 1
                    )
                    async def button_set_leaves_embed_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        permission_manager = PermissionsManager(bot)
                        configuration_cog = bot.get_cog("Configuration")
                        leaves_command = [command for command in configuration_cog.get_commands() if command.name == "leaves"][0]
                        bot_prefix = await bot.get_prefix(ctx.message)

                        if not await permission_manager.can_use_cmd(ctx, leaves_command):
                            await interaction.response.send_message(f"> Pour définir un embed d'adieu, vous devez avoir accès à la commande `{bot_prefix}leaves`.")
                            return                        

                        await bot.db.set_data("leaves", "embed", json.dumps(embed_menu.embed), guild_id = interaction.guild.id)
                        await interaction.message.edit(
                            embed = discord.Embed(
                                title = f"L'embed d'adieu a correctement été définis",
                                color = await bot.get_theme(ctx.guild.id)
                            ),
                            view = None
                        )

                    @discord.ui.button(
                        label = "Revenir à la configuration",
                        emoji = "↩",
                        row = 4
                    )
                    async def button_comback_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        await interaction.edit(
                            embed = formate_embed(embed_menu.embed),
                            view = embed_menu
                        )
           
                await interaction.edit(
                    embed = discord.Embed(
                        title = "> Que souhaitez-vous faire de cet embed?",
                        color = await bot.get_theme(ctx.guild.id)
                    ),
                    view = ChooseDestination()
                )

            @discord.ui.button(label = "Annuler", emoji = "❎", style = discord.ButtonStyle.danger)
            async def cancel(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return

                self.embeds_backup.append(self.embed.copy())
                self.embeds_backup_of_backup = []
                self.embed = {
                    "title": None, "description": "ㅤ", "color": None,
                    "footer": {"text": None, "icon_url": None}, "timestamp": None,
                    "thumbnail": None, "image": None,
                    "author": {"name": None, "icon_url": None, "url": None}, "fields": [],
                }

                self = get_an_update_of_backups_buttons(self)
                await interaction.edit(embed = formate_embed(self.embed), view = self)

            @discord.ui.button(emoji = "🗑", style = discord.ButtonStyle.danger)
            async def delete(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await delete_message(interaction.message)

            @discord.ui.button(label = "Revenir en arrière", emoji = "↩", style = discord.ButtonStyle.secondary, row = 2, custom_id = "back", disabled = True)
            async def back(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if not self.embeds_backup:
                    await interaction.response.send_message("> Aucune sauvegarde disponible.", ephemeral = True)
                    return

                self.embeds_backup_of_backup.append(self.embed.copy())
                self.embed = self.embeds_backup[-1].copy()
                del self.embeds_backup[-1]

                self = get_an_update_of_backups_buttons(self)
                await interaction.edit(embed = formate_embed(self.embed), view = self)

            @discord.ui.button(label = "Restaurer", emoji = "↪", style = discord.ButtonStyle.secondary, row = 2, custom_id = "restaure", disabled = True)
            async def restaure(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return

                if not self.embeds_backup_of_backup:
                    await interaction.response.send_message("> Il n'y a aucun embed a restorer pour le moment.", ephemeral = True)
                    return
                
                self.embeds_backup.append(self.embed.copy())
                self.embed = self.embeds_backup_of_backup[-1].copy()
                del self.embeds_backup_of_backup[-1]

                self = get_an_update_of_backups_buttons(self)
                await interaction.edit(embed = formate_embed(self.embed), view = self)

        await ctx.send(embed = embed, view = EmbedCreator())


def setup(bot):
    bot.add_cog(Gestion(bot))