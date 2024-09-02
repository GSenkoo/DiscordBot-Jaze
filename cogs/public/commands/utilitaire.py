import discord
import sympy
import sys
import asyncio
import wikipedia
import deepl
import dotenv
import os
import json
import aiohttp
import random

from discord import AllowedMentions as AM
from discord.ext.pages import Page, PaginatorButton
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from discord.ext import commands
from utils.Searcher import Searcher
from utils.Paginator import CustomPaginator
from utils.PermissionsManager import PermissionsManager

sys.set_int_max_str_digits(999999999) # Pour la commande +calc
dotenv.load_dotenv()
deppl_api_key = os.getenv("DEEPL_KEY") # Pour la commande +translate
google_api_key = os.getenv("GOOGLE_API_SEARCH_KEY") # Pour la commande +image
google_api_cse = os.getenv("GOOGLE_API_SEARCH_CSE")


"""
Liens des documentations :
    API DEEPL : https://developers.deepl.com/docs/api-reference/translate
    API/Package Wikipedia : https://wikipedia.readthedocs.io/en/latest/
"""


class Utilitaire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Chercher le salon vocal dans lequel se situe un utilisateur")
    @commands.guild_only()
    async def find(self, ctx, member : discord.Member):
        translation = await self.bot.get_translation("find", ctx.guild.id)

        if not member.voice:
            await ctx.send("> " + (translation["Vous n'êtes pas dans un salon vocal"] if member == ctx.author else translation["[data_user] n'est pas dans un salon vocal"].replace("[data_user]", member.mention)) + ".", allowed_mentions = None)
            return
        
        await ctx.send(
            f"> " + (translation["Vous êtes actuelllement dans [data_channel]"].replace("[data_channel]", member.voice.channel.mention) 
            if member == ctx.author
            else translation["[data_user] est actuellement dans [data_channel]"].replace("[data_user]", member.mention).replace("[data_channel]", member.voice.channel.mention)) + ".",
            allowed_mentions = None
        )


    @commands.command(usage = "<calcul>", description = "Faire un calcul", aliases = ["calculate"])
    @commands.guild_only()
    async def calc(self, ctx, *, calcul):
        translation = await self.bot.get_translation("calc", ctx.guild.id)

        calcul = calcul.replace("\"", "").replace("x", "*").replace(",", ".").replace("÷", "/").replace("^^", "**")
        try:
            result = sympy.sympify(calcul)
        except:
            await ctx.send(f"> {translation['Syntaxe de calcul invalide']}.")
            return
        
        try:
            embed = discord.Embed(
                title = translation["Résultat"],
                description = f"```yml\n" + (str(result) if len(str(result)) < 500 else str(result)[:500] + "...") + "\n```",
                color = 0xFFFFFF
            )
        except:
            await ctx.send(f"> {translation['Résultat trop grand']}.")
            return

        await ctx.send(embed = embed)


    @commands.command(aliases = ["ping"], description = "Voir la vitesse actuel du bot")
    @commands.guild_only()
    async def speed(self, ctx):
        await ctx.send(
            embed = discord.Embed(
                title = "Vitesse du bot",
                description = "**`" + str(round(self.bot.latency * 1000)) + "ms`**",
                color = await self.bot.get_theme(ctx.guild.id),
            )
        )


    @commands.command(description = "Afficher un bouton pour inviter le bot")
    @commands.guild_only()
    async def invite(self, ctx):
        translation = await self.bot.get_translation("invite", ctx.guild.id)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style = discord.ButtonStyle.link,
            label = translation["Inviter [data_user]"].replace("[data_user]", self.bot.user.display_name),
            url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot+applications.commands"
        ))

        await ctx.send(
            embed = discord.Embed(
                author = discord.EmbedAuthor(name = self.bot.user.display_name, icon_url = self.bot.user.avatar.url),
                description = translation["Utilisez le bouton ci-dessous pour m'inviter"],
                color = await self.bot.get_theme(ctx.guild.id)
            ),
            view = view
        )


    @commands.command(usage = "<search>", description = "Faire une recherche wikipedia", aliases = ["wikipedia", "wkp"])
    @commands.guild_only()
    async def wiki(self, ctx, *, search):
        translation = await self.bot.get_translation("wiki", ctx.guild.id)
        langage = await self.bot.get_translations_langage(ctx.guild.id)
        message = await ctx.send(f"> {translation['Recherche wikipedia en cours']}...")

        if len(search) > 100:
            await message.edit(f"{translation['Votre recherche est trop longue (plus de 100 caractères)']}.")
            return
        
        def get_summary(topic, sentences):
            wikipedia.set_lang(langage)
            try:
                summary = wikipedia.summary(topic, sentences)
                return summary
            except: pass
            return wikipedia.summary(topic[1:], sentences)

        async def get_summary_async(topic, sentences):
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(pool, get_summary, topic, sentences)
            return result
        
        try:
            summary = await get_summary_async(search.lower(), 500)
        except:
            await message.edit("> " + translation["Aucun résultat pour [data_query]"].replace("[data_query]", search), allowed_mentions = None)
            return

        if not summary:
            await message.edit("> " + translation["Aucun résultat pour [data_query]"].replace("[data_query]", search), allowed_mentions = None)
            return

        await message.edit(
            content = None,
            embed = discord.Embed(
                title = translation["Recherche : [data_query]"].replace("[data_query]", search),
                description = summary.replace("====", "**").replace(" ====", "").replace("===", "###").replace(" ###", "").replace("==", "## ").replace(" ##", ""),
                color = await self.bot.get_theme(ctx.guild.id),
                timestamp = datetime.now()
            )
        )


    @commands.command(description = "Rechercher des images avec l'API Google")
    @commands.bot_has_permissions(embed_links = True)
    @commands.guild_only()
    async def images(self, ctx, *, query: str):
        if not len(query) <= 50:
            await ctx.send("> Votre recherche doit faire moins de 50 caractères.")
            return
        
        message = await ctx.send("> Recherche de l'image en cours...")
        params = {
            "q": query,
            "key": google_api_key,
            "cx":google_api_cse,
            "searchType": "image",
            "imgSize": "huge"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get("https://customsearch.googleapis.com/customsearch/v1", params = params) as response:
                await message.edit("> Recherche terminée.", delete_after = 3)
                
                if response.status != 200:
                    await ctx.send("> Une erreur s'est produite lors de la requête, merci de reéssayer plus tards.")
                    return
                
                data = await response.json()
                if not data.get("items", None):
                    await ctx.send(f"> Requête aboutie, mais aucun résultats pour `" + query.replace("`", "'") + "`.")
                    return
                
                pages = []

                for item in data["items"]:
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(style = discord.ButtonStyle.link, url = "https://" + item["displayLink"], label = "Source"))

                    pages.append(
                        Page(
                            embeds = [
                                discord.Embed(
                                    title = item["title"],
                                    color = await self.bot.get_theme(ctx.guild.id)
                                ).set_image(url = item["link"])
                            ],
                            custom_view = view
                        )
                    )

                buttons = [
                    PaginatorButton("prev", label = "◀", style=discord.ButtonStyle.primary),
                    PaginatorButton("next", label = "▶", style=discord.ButtonStyle.primary),
                ]
                paginator = CustomPaginator(
                    pages = pages,
                    custom_buttons = buttons,
                    use_default_buttons = False
                )

                await paginator.send(ctx)


    @commands.command(usage = "<text>", description = "Traduir un texte dans un langage que vous choisirez sur un menu", aliases = ["tsl"])
    @commands.guild_only()
    @commands.cooldown(rate = 5, per = 60, type = commands.BucketType.guild)
    async def translate(self, ctx, *, text):
        translation = await self.bot.get_translation("translate", ctx.guild.id)

        if len(text) <= 5:
            await ctx.send(f"> {translation['Demande de traduction trop courte']}.")
            return
        if len(text) > 500:
            await ctx.send(f"> {translation['Demande de traduction trop longue (plus de 500 caractères)']}.")
            return
        
        translator = deepl.Translator(deppl_api_key)

        embed = discord.Embed(
            title = translation["Choisissez une langue cible"],
            color = await self.bot.get_theme(ctx.guild.id)
        ).add_field(
            name = translation["Votre texte"],
            value = text
        )

        def get_translation(text, target):
            result = translator.translate_text(text = text, target_lang = target)
            assert result
            return result

        async def get_translation_async(text, target):
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(pool, get_translation, text, target)
            return result

        with open("cogs/private/data/deepl_langage_select.json", encoding = "utf-8") as file:
            langages_dict = json.load(file)

        class ChooseLangage(discord.ui.View):
            def __init__(self, bot, ctx, text, translator, *args, **kwargs):
                super().__init__(*args, **kwargs, timeout = 15)
                self.bot = bot
                self.ctx = ctx
                self.text = text
                self.translator = translator

            async def on_timeout(self) -> None:
                if self.message:
                    try: await self.message.edit(view = None)
                    except: pass
            
            @discord.ui.select(
                placeholder = translation["Choisir une langue"],
                options = [
                    discord.SelectOption(
                        label = langage,
                        emoji = values[1],
                        value = values[0]
                    ) for langage, values in langages_dict.items()
                ],
                custom_id = "translate"
            )
            async def select_callback(self, select, interaction):
                if interaction.user != self.ctx.author:
                    await ctx.respond("> " + translation["> Vous n'êtes pas autorisés à intéragir avec ceci"] + ".", ephemeral = True)
                    return
                
                for option in self.get_item("translate").options:
                    option.default = (select.values[0] == option.value)
                
                try: translation_deepl = await get_translation_async(self.text, select.values[0])
                except:
                    await interaction.edit(
                        embed = discord.Embed(
                            title = translation["La traduction de votre texte n'a pas pu aboutir"] + ".",
                            color = self.bot.get_theme(self.ctx.guild.id)
                        )
                    )

                embed = discord.Embed(
                    title = translation["Traduction de texte"],
                    color = await self.bot.get_theme(self.ctx.guild.id)
                )
                embed.add_field(name = translation["Texte d'origine"], value = self.text)
                embed.add_field(name = translation["Texte traduit ([data_langage])"].replace("[data_langage]", select.values[0]), value = translation_deepl)

                await interaction.edit(embed = embed, view = self)
                
        await ctx.send(embed = embed, view = ChooseLangage(self.bot, ctx, text, translator))


    @commands.command(description = "Voir le dernier message supprimé du salon")
    @commands.guild_only()
    async def snipe(self, ctx):
        translation = await self.bot.get_translation("snipe", ctx.guild.id)
        author_id = await self.bot.db.get_data("snipe", "author_id", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        if not author_id:
            await ctx.send(f"> " + translation["Aucun récent message supprimé n'a été enregistré"] + ".")
            return
            
        author_name = await self.bot.db.get_data("snipe", "author_name", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        author_avatar = await self.bot.db.get_data("snipe", "author_avatar", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        message_content = await self.bot.db.get_data("snipe", "message_content", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        message_datetime = await self.bot.db.get_data("snipe", "message_datetime", guild_id = ctx.guild.id, channel_id = ctx.channel.id)

        snipe_view = discord.ui.View(timeout = None)
        snipe_view.add_item(discord.ui.Button(emoji = "🗑", custom_id = f"snipedelete_{ctx.author.id}_{author_id}"))
        
        embed = discord.Embed(
            author = discord.EmbedAuthor(name = author_name, icon_url = author_avatar, url = "https://discord.com/users/" + str(author_id)),
            description = message_content,
            color = await self.bot.get_theme(ctx.guild.id),
            timestamp = message_datetime
        )

        await ctx.send(embed = embed, view = snipe_view)

    
    @commands.command(description = "Voir le dernier message modifié du salon")
    @commands.guild_only()
    async def esnipe(self, ctx):
        translation = await self.bot.get_translation("esnipe", ctx.guild.id)
        author_id = await self.bot.db.get_data("snipe_edit", "author_id", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        if not author_id:
            await ctx.send(f"> " + translation["Aucun récent message modifié n'a été enregistré"] + ".")
            return

        author_name = await self.bot.db.get_data("snipe_edit", "author_name", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        author_avatar = await self.bot.db.get_data("snipe_edit", "author_avatar", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        message_content_before = await self.bot.db.get_data("snipe_edit", "message_content_before", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        message_content_after = await self.bot.db.get_data("snipe_edit", "message_content_after", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        message_datetime = await self.bot.db.get_data("snipe_edit", "message_datetime", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        
        snipe_view = discord.ui.View(timeout = None)
        snipe_view.add_item(discord.ui.Button(emoji = "🗑", custom_id = f"snipedelete_{ctx.author.id}_{author_id}"))

        embed = discord.Embed(
            author = discord.EmbedAuthor(name = author_name, icon_url = author_avatar, url = "https://discord.com/users/" + str(author_id)),
            color = await self.bot.get_theme(ctx.guild.id),
            timestamp = message_datetime
        )

        embed.add_field(name = "Précédent contenu", value = message_content_before)
        embed.add_field(name = "Nouveau contenu", value = message_content_after, inline = False)

        await ctx.send(embed = embed, view = snipe_view)


    @commands.command(description = "Obtenir des/un utilisateur(s) choisi au hasard")
    @commands.guild_only()
    async def randommember(self, ctx, count : int = None, type = commands.BucketType.user):
        if count is None: count = 1

        if not 1 <= count <= 50:
            await ctx.send("> Merci de donner un nombre d'utilisateur choisis au hasard à mentionner entre 1 et 50.")
            return
        
        if count > len(ctx.guild.members):
            await ctx.send("> Votre nombre d'utilisateur choisi au hasard à mentionner ne peut pas être suppérieur à votre nombre de membres.")
            return
        
        if count == 1:
            await ctx.send(f"> Utilisateur choisi au hasard : {random.choice(ctx.guild.members).mention}", allowed_mentions = AM.none())
            return
        
        members = ctx.guild.members
        choosed_members = []
        for i in range(count):
            choice = random.choice(members)
            choosed_members.append(choice.mention)
            members.remove(choice)

        await ctx.send(f"> Voici une liste de {count} utilisateurs choisi au hasard :\n\n{', '.join(choosed_members)}", allowed_mentions = AM.none())


    @commands.command(description = "Faire une suggestion au serveur")
    @commands.cooldown(rate = 5, per = 60, type = commands.BucketType.guild)
    @commands.guild_only()
    async def suggest(self, ctx, *, suggestion : str):
        if len(suggestion) > 2000:
            await ctx.send("> Votre suggestion ne peut pas dépasser 2000 caractères.")
            return
        
        suggestion_enabled = await self.bot.db.get_data("suggestions", "enabled", guild_id = ctx.guild.id)
        if not suggestion_enabled:
            await ctx.send(f"> Les suggestions ne sont pas activés sur ce serveur (utilisez `{await self.bot.get_prefix(ctx.message)}suggestions` pour les configurer).")
            return
        
        suggestion_channel = await self.bot.db.get_data("suggestions", "channel", guild_id = ctx.guild.id)
        suggestion_channel = ctx.guild.get_channel(suggestion_channel)

        if not suggestion_channel:
            await ctx.send("> Le salon de suggestion configuré n'est plus d'actualité.")
            return
        
        confirmation_channel = await self.bot.db.get_data("suggestions", "confirm_channel", guild_id = ctx.guild.id)
        confirmation_channel = ctx.guild.get_channel(confirmation_channel)

        if confirmation_channel:
            confirm_view = discord.ui.View(timeout = None)
            confirm_view.add_item(discord.ui.Button(label = "Confirmer", style = discord.ButtonStyle.success, custom_id = f"suggestion_confirm_{ctx.author.id}"))
            confirm_view.add_item(discord.ui.Button(label = "Rejeter", style = discord.ButtonStyle.danger, custom_id = f"suggestion_denied_{ctx.author.id}"))
            confirm_view.add_item(discord.ui.Button(emoji = "🗑", custom_id = f"suggestion_delete_{ctx.author.id}"))

            await confirmation_channel.send(
                embed = discord.Embed(
                    author = discord.EmbedAuthor(name = ctx.author.display_name, icon_url = ctx.author.avatar.url if ctx.author.avatar else None),
                    title = "Suggestion en attente",
                    description = suggestion,
                    color = await self.bot.get_theme(ctx.guild.id)
                ),
                view = confirm_view
            )
        else:
            for_emoji = await self.bot.db.get_data("suggestions", "for_emoji", guild_id = ctx.guild.id)
            if not for_emoji:
                for_emoji = "✅"
            against_emoji = await self.bot.db.get_data("suggestions", "against_emoji", guild_id = ctx.guild.id)
            if not against_emoji:
                against_emoji = "❌"

            message = await suggestion_channel.send(
                embed = discord.Embed(
                    author = discord.EmbedAuthor(name = ctx.author.display_name, icon_url = ctx.author.avatar.url if ctx.author.avatar else None),
                    description = suggestion,
                    color = await self.bot.get_theme(ctx.guild.id)
                )
            )

            async def add_reaction(message, reaction, if_connot_reaction):
                try: await message.add_reaction(reaction)
                except:
                    try: await message.add_reaction(if_connot_reaction)
                    except: pass

            await add_reaction(message, for_emoji, "✅")
            await add_reaction(message, against_emoji, "❌")

        await ctx.send(f"> Votre suggestion a été bien été envoyé" + (", il doit désormais être confirmé." if confirmation_channel else "."))
    

    @commands.command(description = "Faire envoyer un message avec un contenu donné")
    @commands.cooldown(rate = 5, per = 60, type = commands.BucketType.guild)
    @commands.guild_only()
    async def say(self, ctx : commands.Context, *, message : str):
        if len(message) > 2000:
            await ctx.send("> Je ne peux pas envoyer de message contentant plus de 2000 caractères.")
            return
        
        allowed_mentions = AM.all() if ctx.author.guild_permissions.mention_everyone else AM.none()
        await ctx.send(message, allowed_mentions = allowed_mentions)


    @commands.command(description = "Retirer les boutons et sélecteurs d'un message du bot", aliases = ["clearcomponent"])
    @commands.guild_only()
    async def clearcomponents(self, ctx, message : discord.Message):
        if message.author != ctx.guild.me:
            await ctx.send(f"> Je ne suis pas l'ateur de ce [message](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}).")
            return
        
        if not message.components:
            await ctx.send("> Le message donné ne contient pas de bouton.")
            return
        
        try:
            await message.edit(view = None)
            await ctx.send(f"> Les boutons et sélecteurs du [message](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}) donné ont tous étés retirés.")
        except: 
            await ctx.send(f"> Il me paraît pour le moment impossible de modifier le [message](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}) donné.")


def setup(bot):
    bot.add_cog(Utilitaire(bot))