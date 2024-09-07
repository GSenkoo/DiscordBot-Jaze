import discord
from discord.ext import commands
from utils import Tools


class SuggestionsManagerInteractionEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.Cog.listener()
    async def on_interaction(self, interaction : discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        if not interaction.custom_id.startswith("suggestion"):
            return
        
        suggestion_enabled = await self.bot.db.get_data("suggestions", "enabled", guild_id = interaction.guild.id)
        if not suggestion_enabled:
            await interaction.response.send_message("> Les suggestions ont étés désactivés sur ce serveur.", ephemeral = True)
            return
        
        
        can_use = False
        guild_owners = await self.bot.db.get_data("guild", "owners", True, guild_id = interaction.guild.id)
        if not (
                (interaction.user.id in guild_owners)
                or (interaction.guild.owner == interaction.user)
                or (interaction.user.id == int(interaction.custom_id.split("_")[2]) and interaction.custom_id.startswith("suggestion_delete"))
            ):
            moderator_roles = await self.bot.db.get_data("guild", "moderator_roles", True, guild_id = interaction.guild.id)
            for role in interaction.user.roles:
                if role.id in moderator_roles:
                    can_use = True
        else:
            can_use = True

        if not can_use:
            if interaction.custom_id.startswith("suggestion_delete"):
                await interaction.response.send_message("> Seul l'auteur de la suggestion et les utilisateurs ayant les permissions nécessaires peuvent supprimer cette suggestion.", ephemeral = True)
            else:
                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return

        if interaction.custom_id.startswith("suggestion_delete"):
            await interaction.message.delete()
        
        if interaction.custom_id.startswith("suggestion_confirm"):
            suggestion_channel = await self.bot.db.get_data("suggestions", "channel", guild_id = interaction.guild.id)
            suggestion_channel = interaction.guild.get_channel(suggestion_channel)

            if not suggestion_channel:
                await interaction.response.send_message("> Aucun salon de suggestion valide (ou auquel j'ai accès) n'a été défini.", ephemeral = True)
                return

            for_emoji = await self.bot.db.get_data("suggestions", "for_emoji", guild_id = interaction.guild.id)
            against_emoji = await self.bot.db.get_data("suggestions", "against_emoji", guild_id = interaction.guild.id)

            current_message_embed = interaction.message.embeds[0]
            current_message_embed.title = None

            try:
                message = await suggestion_channel.send(
                    embed = current_message_embed
                )
            except:
                await interaction.response.send_message(f"> La tentative de l'envoi du message de la suggestion dans le salon <#{suggestion_channel.mention}> a échoué, merci de vérifier que j'ai les permissions nécessaires pour faire ceci.", ephemeral = True)
                return

            current_message_embed.title = "Suggestion confirmée"
            current_message_embed.color = 0x00aa53
            await interaction.edit(embed = current_message_embed, view = None)

            async def add_reaction(message, reaction, if_connot_reaction):
                tools = Tools(self.bot)
                emoji = await tools.get_emoji(reaction)

                emoji_to_add = str(emoji) if emoji else if_connot_reaction

                try: await message.add_reaction(emoji_to_add)
                except: pass

            await add_reaction(message, for_emoji, "✅")
            await add_reaction(message, against_emoji, "❌")

        
        if interaction.custom_id.startswith("suggestion_denied"):
            suggestion_embed = interaction.message.embeds[0]
            message = interaction.message
            bot = self.bot
            
            class ReasonModal(discord.ui.Modal):
                def __init__(self, *args, **kwargs) -> None:
                    super().__init__(*args, **kwargs)

                    self.add_item(discord.ui.InputText(label = "Raison", style = discord.InputTextStyle.long, required = False, placeholder = "Exemple de raison", max_length = 1024))

                async def callback(self, interaction: discord.Interaction):
                    reason = self.children[0].value

                    denied_channel = await bot.db.get_data("suggestions", "denied_channel", guild_id = interaction.guild.id)
                    denied_channel = interaction.guild.get_channel(denied_channel)

                    suggestion_embed.title = "Suggestion refusée"
                    suggestion_embed.color = 0xe70000
                    if reason:
                        suggestion_embed.add_field(name = "Raison du refus", value = reason)

                    await message.edit(view = None, embed = suggestion_embed)
                    await interaction.response.defer()

            await interaction.response.send_modal(ReasonModal(title = "Souhaitez-vous ajouter une raison?"))
        

def setup(bot):
    bot.add_cog(SuggestionsManagerInteractionEvent(bot))