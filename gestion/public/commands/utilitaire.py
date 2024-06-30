"""
MIT License with Attribution Clause

Copyright (c) 2024 GSenkoo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

**Attribution:**
All copies, modifications, or substantial portions of the Software must include
the original author attribution as follows:
"This software includes work by GSenkoo (github)".

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import discord
import sympy
import sys
import asyncio
import wikipedia
import deepl
import dotenv
import os
import json
import mimetypes
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from discord.ext import commands
from utils.Database import Database

sys.set_int_max_str_digits(999999999) # Pour la commande +calc
dotenv.load_dotenv()
deppl_api_key = os.getenv("DEEPL_KEY") # Pour la commande +translate


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
                title = translation["Recherche : [data_query]"].replace("[data_qery]", search),
                description = summary.replace("====", "**").replace(" ====", "").replace("===", "###").replace(" ###", "").replace("==", "## ").replace(" ##", ""),
                color = await self.bot.get_theme(ctx.guild.id),
                timestamp = datetime.now()
            )
        )


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
                    await ctx.respond("> " + translation["Vous n'êtes pas autorisés à intéragir avec ceci"] + ".", ephemeral = True)
                    return
                
                try: translation = await get_translation_async(self.text, select.values[0])
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
                embed.add_field(name = translation["Texte traduit ([data_langage])"].replace("[data_langage]", select.values[0]), value = translation)

                await interaction.message.edit(embed = embed)
                await interaction.response.defer()

        await ctx.send(embed = embed, view = ChooseLangage(self.bot, ctx, text, translator))


    @commands.command(description = "Voir le dernier message supprimé du salon")
    @commands.guild_only()
    async def snipe(self, ctx):
        translation = await self.bot.get_translation("snipe", ctx.guild.id)
        database = Database()
        await database.connect()

        try:
            author_id = await database.get_data("snipe", "author_id", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
            author_name = await database.get_data("snipe", "author_name", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
            author_avatar = await database.get_data("snipe", "author_avatar", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
            message_content = await database.get_data("snipe", "message_content", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
            message_datetime = await database.get_data("snipe", "message_datetime", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        finally: await database.disconnect()

        if not author_id:
            await ctx.send(f"> " + translation["Aucun récent message supprimé n'a été enregistré"] + ".")
            return
        
        embed = discord.Embed(
            author = discord.EmbedAuthor(name = author_name, icon_url = author_avatar, url = "https://discord.com/users/" + str(author_id)),
            description = (message_content if len(message_content) < 2000 else message_content[:1500]),
            color = await self.bot.get_theme(ctx.guild.id),
            timestamp = message_datetime
        )

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
        

    @commands.command(description = "Créer un embed")
    @commands.guild_only()
    async def embed(self, ctx):
        embed = discord.Embed(description = "ㅤ" )
        bot = self.bot

        def formate_embed(data):
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
                for field, field_data in data["fields"].items():
                    embed.add_field(name = field, value = field_data["value"], inline = field_data["inline"])

            return embed

        def get_total_characters(data):
            total = 0
            if data["title"]: total += len(data["title"])
            if data["description"]: total += len(data["description"])
            for field, field_data in data["fields"].items(): total += len(field) + len(field_data["value"])
            if data["footer"]["text"]: total += len(data["footer"]["text"])
            if data["author"]["name"]: total += len(data["author"]["name"])
            return total

        def is_valid_image_url(url):
            mimetype, encoding = mimetypes.guess_type(url)
            return mimetype and mimetype.startswith('image')

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
                    "author": {
                        "name": None,
                        "icon_url": None,
                        "url": None
                    },
                    "fields": {
                        # field exemple "name": {"value": "My field name", "inline": True}
                    },
                }
                self.embeds_backup = []
                self.embeds_backup_of_backup = []

            async def on_timeout(self):
                return await super().on_timeout()
            
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
                    await interaction.response.send_message("Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                await interaction.response.defer()

                temporary_data = self.embed # données temporaires utiles pour check si le nombre de caractère total > 6000, sans modifier self.embed

                def response_check(message):
                    return (message.author == ctx.author) and (message.channel == ctx.channel)
                
                message = None
                if select.values[0] not in ["footer", "author", "field_add", "field_remove"]:
                    message = await ctx.send(f"Quel sera la nouvelle valeur de votre **{select.values[0]}** ? Envoyez `cancel` pour annuler")

                    # Attendre la réponse de l'utilisateur, après 60 secondes d'attente, l'action est annulée
                    try: response = await bot.wait_for('message', timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute dépassée.", delete_after = 2)
                        return
                    finally:
                        await message.delete()
                

                    # Supprimer le message de l'utilisateur
                    try: await response.delete()
                    except: pass

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

                    self.embed[select.values[0]] = response.content

                # ---------------------------- COULEUR ----------------------------
                if select.values[0] == "color":
                    if not len(response.content.removeprefix("#")) == 6:
                        await ctx.send("> La couleur HEX donnée est invalide.", delete_after = 2)
                        return
                    
                    self.embed["color"] = int(response.content.removeprefix("#"), 16)

                # ---------------------------- FOOTER ----------------------------
                if select.values[0] == "footer":
                    # ----- FOOTER / TEXT
                    message1 = await ctx.send("Quel sera le **texte** de votre **footer** ? Envoyez `cancel` pour annuler.")
                    
                    try: response = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée, 1 minute dépassée.", delete_after = 2)
                        return
                    finally:
                        await message1.delete()
                    await response.delete()

                    # @Check annulation
                    if response.content.lower() == "cancel":
                        await ctx.send("> Action annulée.", delete_after = 2)
                        return
                    
                    # @Check total embed < 6000 caractères
                    if len(response.content) > max_sizes["footer_text"]:
                        await ctx.send(f"> Vous ne pouvez pas dépasser {max_sizes['footer_text']} caractères pour votre **footer**.", delete_after = 2)
                        return
                    
                    temporary_data["footer"]["text"] = response.content
                    if get_total_characters(temporary_data) > 6000:
                        await ctx.send(f"> Le nombre total de charactère dans votre embed ne doit pas dépasser les 6000 caractères.", delete_after = 2)

                    # ----- FOOTER / ICON
                    message2 = await ctx.send("Quel sera l'**icône** du **footer**? Envoyez `skip` pour ne pas en mettre.")
                    try: response : discord.Message = await bot.wait_for("message", timeout = 60, check = response_check)
                    except asyncio.TimeoutError:
                        await ctx.send("> Action annulée.", delete_after = 2)
                        return
                    finally:
                        await message2.delete()
                    await response.delete()

                    if response.content.lower() == "skip":
                        self.embed = temporary_data
                    else:
                        if response.attachments: # TO FIX
                            if not response.attachments[0].content_type == "image":
                                await ctx.send("> La première pièce jointe donnée n'est pas une image.", delete_after = 2)
                                return
                            self.embed["image"] = response.attachments[0].url
                        else: # TO FIX
                            if not is_valid_image_url(response.content):
                                await ctx.send("> Le lien donné n'est pas une image valide.", delete_after = 2)
                                return
                            self.embed["image"] = response.content

                # ---------------------------- TIMESTAMP ----------------------------
                ... # TODO

                await ctx.send(f"Votre **{select.values[0]}** a été mis à jours.", delete_after = 2)


                back = self.get_item("back")
                self.remove_item(back)
                back.disabled = False if self.embeds_backup else True
                self.add_item(back)

                restaure = self.get_item("restaure")
                self.remove_item(restaure)
                restaure.disabled = False if self.embeds_backup_of_backup else True
                self.add_item(restaure)
                
                
                # Mettre à jours l'embed
                await interaction.message.edit(embed = formate_embed(self.embed), view = self)

            @discord.ui.button(label = "Envoyer", emoji = "✅", style = discord.ButtonStyle.secondary)
            async def send(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                ...

            @discord.ui.button(label = "Annuler", emoji = "❌", style = discord.ButtonStyle.secondary)
            async def cancel(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                ...

            @discord.ui.button(emoji = "🗑", style = discord.ButtonStyle.danger)
            async def reset(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return

            @discord.ui.button(label = "Revenir en arrière", emoji = "↩", style = discord.ButtonStyle.secondary, row = 2, custom_id = "back")
            async def back(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return

                ...

            @discord.ui.button(label = "Restaurer", emoji = "↪", style = discord.ButtonStyle.secondary, row = 2, custom_id = "restaure")
            async def restaure(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return

                ...


        await ctx.send(embed = embed, view = EmbedCreator())

def setup(bot):
    bot.add_cog(Utilitaire(bot))