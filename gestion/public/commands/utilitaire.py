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

from discord.ext.pages import Page, PaginatorButton
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from discord.ext import commands
from utils.Searcher import Searcher
from utils.Paginator import CustomPaginator

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
                    PaginatorButton("prev", label="◀", style=discord.ButtonStyle.primary),
                    PaginatorButton("next", label="▶", style=discord.ButtonStyle.primary),
                ]
                paginator = CustomPaginator(
                    pages = pages,
                    custom_buttons = buttons,
                    use_default_buttons = False
                )

                await paginator.send(ctx)


    @commands.command(usage = "<text>", description = "Traduir un texte dans un langage que vous choisirez sur un menu", aliases = ["tsl"])
    @commands.guild_only()
    @commands.cooldown(rate = 5, per = 60)
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

        with open("gestion/private/data/deepl_langage_select.json", encoding = "utf-8") as file:
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
                ]
            )
            async def select_callback(self, select, interaction):
                if interaction.user != self.ctx.author:
                    await ctx.respond("> " + translation["> Vous n'êtes pas autorisés à intéragir avec ceci"] + ".", ephemeral = True)
                    return
                
                try: translation_deepl = await get_translation_async(self.text, select.values[0])
                except:
                    await interaction.message.edit(
                        embed = discord.Embed(
                            title = translation["La traduction de votre texte n'a pas pu aboutir"] + ".",
                            color = self.bot.get_theme(self.ctx.guild.id)
                        )
                    )
                    await interaction.response.defer()

                embed = discord.Embed(
                    title = translation["Traduction de texte"],
                    color = await self.bot.get_theme(self.ctx.guild.id)
                )
                embed.add_field(name = translation["Texte d'origine"], value = self.text)
                embed.add_field(name = translation["Texte traduit ([data_langage])"].replace("[data_langage]", select.values[0]), value = translation_deepl)

                await interaction.message.edit(embed = embed)
                await interaction.response.defer()

        await ctx.send(embed = embed, view = ChooseLangage(self.bot, ctx, text, translator))


    @commands.command(description = "Voir le dernier message supprimé du salon")
    @commands.guild_only()
    async def snipe(self, ctx):
        translation = await self.bot.get_translation("snipe", ctx.guild.id)

        author_id = await self.bot.db.get_data("snipe", "author_id", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        author_name = await self.bot.db.get_data("snipe", "author_name", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        author_avatar = await self.bot.db.get_data("snipe", "author_avatar", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        message_content = await self.bot.db.get_data("snipe", "message_content", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        message_datetime = await self.bot.db.get_data("snipe", "message_datetime", guild_id = ctx.guild.id, channel_id = ctx.channel.id)

        if not author_id:
            await ctx.send(f"> " + translation["Aucun récent message supprimé n'a été enregistré"] + ".")
            return
        
        embed = discord.Embed(
            author = discord.EmbedAuthor(name = author_name, icon_url = author_avatar, url = "https://discord.com/users/" + str(author_id)),
            description = message_content,
            color = await self.bot.get_theme(ctx.guild.id),
            timestamp = message_datetime
        )

        await ctx.send(embed = embed)

    
    @commands.command(description = "Voir le dernier message modifié du salon")
    @commands.guild_only()
    async def esnipe(self, ctx):
        translation = await self.bot.get_translation("esnipe", ctx.guild.id)

        author_id = await self.bot.db.get_data("snipe_edit", "author_id", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        author_name = await self.bot.db.get_data("snipe_edit", "author_name", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        author_avatar = await self.bot.db.get_data("snipe_edit", "author_avatar", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        message_content_before = await self.bot.db.get_data("snipe_edit", "message_content_before", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        message_content_after = await self.bot.db.get_data("snipe_edit", "message_content_after", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        message_datetime = await self.bot.db.get_data("snipe_edit", "message_datetime", guild_id = ctx.guild.id, channel_id = ctx.channel.id)

        if not author_id:
            await ctx.send(f"> " + translation["Aucun récent message modifié n'a été enregistré"] + ".")
            return
        
        embed = discord.Embed(
            author = discord.EmbedAuthor(name = author_name, icon_url = author_avatar, url = "https://discord.com/users/" + str(author_id)),
            color = await self.bot.get_theme(ctx.guild.id),
            timestamp = message_datetime
        )

        embed.add_field(name = "Précédent contenu", value = message_content_before)
        embed.add_field(name = "Nouveau contenu", value = message_content_after, inline = False)

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
                if self.message: await self.message.edit(view = None)
            
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
                    discord.SelectOption(label = "Retirer un champ", emoji = "➖", value = "field_remove")
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
                if select.values[0] not in ["footer", "author", "field_add", "field_remove", "timestamp"]:
                    message = await ctx.send(f"Quel sera la nouvelle valeur de votre **{select.values[0]}** ? Envoyez `cancel` pour annuler")

                    # Attendre la réponse de l'utilisateur, après 60 secondes d'attente, l'action est annulée
                    try: response = await bot.wait_for('message', timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                        return
                    finally:
                        await message.delete()
                    await response.delete()

                    # @Check Annulation
                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 2)
                        return
                

                # ---------------------------- TITRE & DESCRIPTION ----------------------------
                if select.values[0] in ["title", "description"]:
                    if len(response.content) == 0:
                        await ctx.send(f"> Votre {select.values[0]} ne peut pas être vide.")
                        return
                    if len(response.content) > max_sizes[select.values[0]]:
                        await ctx.send(f"> Vous ne pouvez pas dépasser {max_sizes[select.values[0]]} caractères pour votre **{select.values[0]}**.", delete_after = 2)
                        return
                    
                    # @Check total embed < 6000 caractères
                    temporary_data[select.values[0]] = response.content
                    if get_total_characters(temporary_data) > 6000:
                        await ctx.send("> Le nombre total de charactère dans votre embed ne doit pas dépasser les 6000 caractères.", delete_after = 2)
                        return

                    temporary_data[select.values[0]] = response.content
                    self.embed = temporary_data.copy()


                # ---------------------------- IMAGE & THUMBNAIL ----------------------------
                if select.values[0] in ["image", "thumbnail"]:
                    if not response.content.startswith(("https://", "http://")) or " " in response.content:
                        await ctx.send("> Action annulée, lien d'image invalide.", delete_after = 2)
                        return
                    
                    temporary_data[select.values[0]] = response.content
                    self.embed = temporary_data.copy()

                # ---------------------------- COLOUR ----------------------------
                if select.values[0] == "color":
                    try: temporary_data["color"] = int(response.content.removeprefix("#"), 16)
                    except:
                        await ctx.send("> La couleur HEX (exemple : `#FF12F4`) donnée est invalide.", delete_after = 2)
                        return

                    self.embed = temporary_data.copy()


                # ---------------------------- FOOTER ----------------------------
                if select.values[0] == "footer":
                    # -------------- FOOTER / TEXT
                    message1 = await ctx.send("Quel sera le **texte** de votre **footer** ? Envoyez `cancel` pour annuler.")
                    
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                        return
                    finally:
                        await message1.delete()
                    await response.delete()

                    # @Check pas vide
                    if not response.content:
                        await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_fater = 2)
                        return

                    # @Check annulation
                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 2)
                        return
                     
                    # @Check taille footer text < max(taille_footer_text)
                    if len(response.content) > max_sizes["footer_text"]:
                        await ctx.send(f"> Vous ne pouvez pas dépasser {max_sizes['footer_text']} caractères pour votre **footer**.", delete_after = 2)
                        return
                    
                    # Pour éviter les bug dans la liste des données d'embed self.embed_backups (car le dictionnaire footer est considéré comme le même objet PARTOUT)
                    temporary_data["footer"] = temporary_data["footer"].copy()

                    # @Check total embed < 6000 caractères
                    temporary_data["footer"]["text"] = response.content
                    if get_total_characters(temporary_data) > 6000:
                        await ctx.send(f"> Le nombre total de charactère dans votre embed ne doit pas dépasser les 6000 caractères.", delete_after = 2)

                    # -------------- FOOTER / ICON
                    message2 = await ctx.send("Quel sera l'**icône** du **footer** (un lien)? Envoyez `skip` pour ne pas modifier et `delete` pour retirer.")
                    try: response : discord.Message = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée.", delete_after = 2)
                        return
                    finally:
                        await message2.delete()
                    await response.delete()

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
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                        return
                    finally:
                        await message1.delete()
                    await response.delete()

                    if response.content.lower() != "now":
                        try: date = datetime.strptime(response.content, '%d/%m/%Y %H:%M')
                        except:
                            await ctx.send("> Action annulée, durée invalide.", delete_after = 2)
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
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                        return
                    finally: await message1.delete()
                    await response.delete()

                    if not response.content:
                        await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_fater = 2)
                        return
                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 2)
                        return
                    if len(response.content) > max_sizes["author_name"]:
                        await ctx.send(f"> Action annulée, nom d'auteur trop long (plus de {max_sizes['author_name']} caractères).", delete_after = 2)
                        return
                    
                    temporary_data["author"]["name"] = response.content
                    if get_total_characters(temporary_data) > 6000:
                        await ctx.send(f"> Action annulée, le nombre total de caractère dans votre embed ne doit pas dépasser 6000 caractères.", delete_after = 2)
                        return
                    
                    # -------------- AUTHOR / ICON_URL
                    message2 = await ctx.send("Quel sera l'**icône** de l'auteur? Envoyez `skip` pour ne pas en mettre ou `delete` pour supprimer celle actuelle.")
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                        return
                    finally: await message2.delete()
                    await response.delete()

                    if not response.content:
                        await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_fater = 2)
                        return
                    if response.content.lower() == "delete":
                        temporary_data["author"]["icon_url"] = None
                    if response.content.lower() not in ["skip", "delete"]:
                        if not response.content.startswith(("https://", "http://")) or " " in response.content:
                            await ctx.send("> Action annulée, image invalide.", delete_after = 2)
                            return
                        temporary_data["author"]["icon_url"] = response.content

                    # -------------- AUTHOR / URL
                    message3 = await ctx.send("Quel sera l'**url** vers lequel sera redirigé les utilisateurs qui appuiyeront sur le nom de l'auteur? Envoyez `skip` pour ne pas en mettre ou `delete` pour supprimer celui actuel.")
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                        return
                    finally:
                        await message3.delete()
                    await response.delete()

                    if not response.content:
                        await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_fater = 2)
                        return
                    if response.content.lower() == "delete":
                        temporary_data["author"]["url"] = None
                    if response.content.lower() not in ["delete", "skip"]:
                        if not response.content.startswith(("https://", "http://")) or " " in response.content:
                            await ctx.send("> Action annulée, lien invalide.", delete_after = 2)
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
                            await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                            return
                        finally: await message.delete()
                        await response.delete()

                        if not response.content:
                            await ctx.send("> Action annulée, vous n'avez pas donné de réponse.", delete_fater = 2)
                            return
                        if response.content.lower() == "cancel":
                            await ctx.send("> Action annulée.", delete_after = 2)
                            return
                        if len(response.content) > max_sizes["field_name"]:
                            await ctx.send(f"> Action annulée, la valeur de vote {data_type} peut pas dépasser {max_sizes[data_type]} caractères.", delete_after = 2)
                            return
                        
                        if data_type == "name":
                            temporary_data["fields"].append(
                                {"name": response.content, "value": "", "inline": None}
                            )
                        else: temporary_data["fields"][-1]["value"] = response.content
                        
                        if get_total_characters(temporary_data) > 6000:
                            await ctx.send("> Action annulée, votre embed ne peut pas faire plus de 6000 caractères.", delete_after = 2)
                            return

                    # -------------- FIELD INLINE OR NOT
                    message = await ctx.send("Souhaitez-vous que votre field soit aligné avec les autres fields (Répondez par `Oui` ou par `Non`)?")
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                        return
                    finally: await message.delete()
                    await response.delete()
                    
                    if response.content.lower() in ["yes", "oui"]: temporary_data["fields"][-1]["inline"] = True
                    else: temporary_data["fields"][-1]["inline"] = False

                    self.embed = temporary_data.copy()

                
                # ---------------------------- REMOVE FIELD ----------------------------
                if select.values[0] == "field_remove":
                    if not len(self.embed["fields"]):
                        await ctx.send("> Aucun field n'a été créé.", delete_after = 2)
                        return

                    message = await ctx.send("Quel est la **position** du field (avec un chiffre de 1 à 25) ou alors le nom du field (chaîne de cractère)?")
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                        return
                    finally: await message.delete()
                    await response.delete()

                    if response.content.isdigit():
                        index = int(response.content)
                        if not 1 <= index <= len(self.embed["fields"]):
                            await ctx.send("> Action annulé, position de field inéxistant.", delete_after = 2)
                            return
                        
                        index -= 1
                        del self.embed["fields"][index]
                    else:
                        field_names = [field_data["name"].lower() for field_data in self.embed["fields"]]
                        if response.content.lower() not in field_names:
                            await ctx.send("> Action annulée, nom de field invalide.", delete_after = 2)
                            return
                        self.embed["fields"] = [field_data for field_data in self.embed["fields"] if field_data["name"].lower() != response.content.lower()]


                await ctx.send(f"Votre **embed** a été mis à jours.", delete_after = 2)

                # Mettre à jour les backups
                self.embeds_backup.append(previous_embed_copy.copy())
                self.embeds_backup_of_backup = []

                # Mettre à jours les bouttons backups
                self = get_an_update_of_backups_buttons(self)
                
                # Mettre à jours l'embed
                await interaction.message.edit(embed = formate_embed(self.embed), view = self)

            @discord.ui.button(label = "Envoyer", emoji = "✅", style = discord.ButtonStyle.secondary)
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
                        if self.message: self.message.edit(view = None)

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
                            await interaction.channel.send("> Action annulée, 1 minute dépassée.", delete_after = 2)
                            return
                        finally:
                            await msg.delete()

                        searcher = Searcher(bot, interaction)
                        channel = await searcher.search_channel(response.content)

                        if not channel:
                            await interaction.channel.send("> Salon invalide.")
                            return
                        
                        try: await channel.send(embed = formate_embed(embed_to_send))
                        except:
                            await interaction.channel.send("> Impossible d'envoyer l'embed dans le salon demandé, vérifiez mes permissions.", delete_after = 2)
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
                        emoji = "✏",
                        row = 1
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
                            await interaction.channel.send("> Action annulée, 1 minute s'est écoulée.", delete_after = 2)
                            return
                        finally: await msg.delete()
                        await response.delete()

                        result = response.content.removeprefix(f"https://discord.com/channels/{interaction.guild.id}/")
                        result = result.split("/")

                        if len(result) != 2:
                            await interaction.channel.send_message("> Lien de message invalide.", delete_after = 2)
                            return
                        for number in result:
                            if not number.isdigit():
                                await interaction.channel.send_message("> Lien de message invalide.", delete_after = 2)
                                return

                        try: channel = await interaction.guild.fetch_channel(int(result[0]))
                        except:
                            await interaction.channel.send_message("> Lien de message invalide.", delete_after = 2)
                            return

                        try: message = await channel.fetch_message(int(result[1]))
                        except:
                            await interaction.channel.send_message("> Lien de message invalide.", delete_after = 2)
                            return
                        
                        if message.author != bot.user:
                            await interaction.channel.send("> Je ne suis pas l'auteur du message donné.", delete_after = 2)
                            return
                        
                        try: await message.edit(embed = formate_embed(embed_to_send))
                        except:
                            await interaction.channel.send("> Impossible de modifier le message, vérifiez que j'ai les permissions nécessaires pour le faire.", delete_after = 2)
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
                        row  = 2
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
                            await interaction.channel.send("> Action annulée, 1 minute écoulée.", delete_after = 2)
                            return
                        finally: await msg.delete()
                        await response.delete()

                        searcher = Searcher(bot, ctx)
                        user = await searcher.search_user(response.content)

                        if not user:
                            await ctx.send("> Utilisateur invalide.", delete_after = 2)
                            return
                        
                        try: await user.send(embed = formate_embed(embed_to_send))
                        except:
                            await interaction.channel.send(f"> Impossible d'envoyer l'embed à {user.mention}, vérifiez l'autorisation des messages privés avec le bot.", allowed_mentions = None, delete_after = 2)
                            return
                        
                        await interaction.message.edit(
                            embed = discord.Embed(
                                title = f"L'embed a correctement été envoyé à {user.display_name}.",
                                color = await bot.get_theme(ctx.guild.id)
                            ),
                            view = None
                        )


                    @discord.ui.button(
                        label = "Revenir à la configuration",
                        emoji = "↩",
                        row = 3
                    )
                    async def button_here_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        await interaction.message.edit(
                            embed = formate_embed(embed_menu.embed),
                            view = embed_menu
                        )
           
                
                await interaction.message.edit(
                    embed = discord.Embed(
                        title = "> Où souhaitez-vous envoyer l'embed?",
                        color = await bot.get_theme(ctx.guild.id)
                    ),
                    view = ChooseDestination()
                )
                await interaction.response.defer()


            @discord.ui.button(label = "Annuler", emoji = "❌", style = discord.ButtonStyle.secondary)
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
                await interaction.response.defer()
                await interaction.message.edit(embed = formate_embed(self.embed), view = self)

            @discord.ui.button(emoji = "🗑", style = discord.ButtonStyle.danger)
            async def delete(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.response.defer()
                await interaction.message.delete()

            @discord.ui.button(label = "Revenir en arrière", emoji = "↩", style = discord.ButtonStyle.secondary, row = 2, custom_id = "back", disabled = True)
            async def back(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if not self.embeds_backup:
                    await interaction.response.send_message("> Aucune sauvegarde disponible.", ephemeral = True)
                    return

                await interaction.response.defer()

                self.embeds_backup_of_backup.append(self.embed.copy())
                self.embed = self.embeds_backup[-1].copy()
                del self.embeds_backup[-1]

                self = get_an_update_of_backups_buttons(self)
                await interaction.message.edit(embed = formate_embed(self.embed), view = self)

            @discord.ui.button(label = "Restaurer", emoji = "↪", style = discord.ButtonStyle.secondary, row = 2, custom_id = "restaure", disabled = True)
            async def restaure(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return

                if not self.embeds_backup_of_backup:
                    await interaction.response.send_message("> Il n'y a aucun embed a restorer pour le moment.", ephemeral = True)
                    return

                await interaction.response.defer()
                
                self.embeds_backup.append(self.embed.copy())
                self.embed = self.embeds_backup_of_backup[-1].copy()
                del self.embeds_backup_of_backup[-1]

                self = get_an_update_of_backups_buttons(self)
                await interaction.message.edit(embed = formate_embed(self.embed), view = self)

        await ctx.send(embed = embed, view = EmbedCreator())


def setup(bot):
    bot.add_cog(Utilitaire(bot))