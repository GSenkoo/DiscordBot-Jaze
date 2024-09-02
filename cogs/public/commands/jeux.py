import discord
import os
import dotenv
import asyncio
import random
import json

from datetime import datetime
from discord.ext import commands
from blagues_api import BlaguesAPI, BlagueType
from utils.MyViewClass import MyViewClass

from menus.jeux.pfc.ChifumiGame import ChifumiGame
from menus.jeux.pfc.functions import get_pfc_embed
from menus.jeux.joke.JokeGenerator import JokeGenerator

dotenv.load_dotenv()

class Jeux(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Générer des blagues d'une certaine catégorie")
    @commands.guild_only()
    async def joke(self, ctx):
        await ctx.send(
            embed = discord.Embed(
                title = "Quel type de blague souhaitez-vous obtenir?",
                color = await self.bot.get_theme(ctx.guild.id)
            ),
            view = JokeGenerator(ctx, self.bot)
        )


    @commands.command(description = "Lancer une partie de bingo", usage = "<minimum> <maximum> [private/public]")
    @commands.guild_only()
    async def bingo(self, ctx, minimum : int, maximum : int, private  : str = "private"):
        if private not in ["private", "public"]:
            await ctx.send(f"> Votre 3ème argument est invalide, votre bingo doit être soit privé, soit public. Rappel d'utilisation : `{await self.bot.get_prefix(ctx.message)}bingo <minimum> <maximum> [private/public]`.")
            return
        
        if maximum - minimum <= 2:
            await ctx.send("> L'erreur entre le nombre minimum et maximum doit être suppérieur ou égal à 2.")
            return
        
        await ctx.send(f"> Partie de bingo lancé, un nombre entre **{minimum}** et **{maximum}** a été généré, serez vous capble de le trouver?\n\n*Envoyez un nombre dans ce salon pour tenter de le trouver*.")
        
        gived_number = minimum - 1
        generated_number = random.randint(minimum, maximum)

        def check_validity(message):
            if (message.channel != ctx.channel) or (private == "private" and message.author != ctx.author) or (not message.content.isdigit()) or (message.author.bot):
                return False
            return True

        while gived_number != generated_number:
            try: response = await self.bot.wait_for("message", check = check_validity, timeout = 300)
            except asyncio.TimeoutError:
                await ctx.send(f"> La [partie de bingo](https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}) a été arrêté, vous avez abondonnez trop tôt.")
                return
            
            gived_number = int(response.content)
            user = response.author

        if private == "private":
            await ctx.send(f"> Vous avez gagné la [partie de bingo](https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}), bien joué. Le nombre était bel et bien **{gived_number}**.")
        else:
            await ctx.send(f"> La [partie de bingo](https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}) a été gagné par {user.mention}, quel champion. Le nombre était bel et bien **{gived_number}**.")


    @commands.command(description = "Jouer à \"pierre, feuille, ciseaux\" avec un membre ou le bot")
    @commands.guild_only()
    async def pfc(self, ctx, member : discord.Member = None):
        if member == ctx.author:
            await ctx.send("> Vous ne pouvez pas lancer une partie de pfc contre vous-mêmes.")
            return

        await ctx.send(
            embed = await get_pfc_embed(ctx, self.bot, member, 0, 0, ctx.author),
            view = ChifumiGame(ctx, self.bot, member)
        )


    @commands.command(description = "Tester votre vitesse de réaction")
    @commands.guild_only()
    async def speedtest(self, ctx):
        embed  = discord.Embed(
            title = "Test de réaction",
            description = "*Dans une durée totalement aléatoire, l'un des boutons ci-dessous va s'activer. Appuyez sur le bouton dès le moment où vous le verrez.*",
            color = await self.bot.get_theme(ctx.guild.id),
            thumbnail = discord.EmbedMedia(url = ctx.author.avatar.url) if ctx.author.avatar else None
        )

        react_view = MyViewClass()
        for i in range(25):
            react_view.add_item(
                discord.ui.Button(
                    emoji = random.choice(['🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍒', '🍍']),
                    style = random.choice([discord.ButtonStyle.primary, discord.ButtonStyle.danger, discord.ButtonStyle.success]),
                    disabled = True
                )
            )

        message = await ctx.send(embed = embed, view = react_view)
        before = datetime.now().timestamp()
        seconds_to_wait = random.randint(2, 4)
        button_index_to_edit = random.randint(0, 24)

        async def response_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                return
            
            now = datetime.now().timestamp()
            speed_in_ms = round((now - before - seconds_to_wait) * 1000)

            with open("cogs/private/data/speedtest_joke.json", encoding = "utf-8") as file:
                jokes = json.load(file)["jokes"]

            embed.description = f"Votre vitesse de réaction a été de **{speed_in_ms}ms**.\n" \
            + ("En moins de 500ms, c'est un exploit." if speed_in_ms < 500 else "") \
            + ("En moins de 1000ms, c'est pas mal." if 500 <= speed_in_ms < 1000 else "") \
            + (random.choice(jokes) if speed_in_ms >= 1000 else "")
            
            await interaction.edit(embed = embed, view = None)

            
        react_view.children[button_index_to_edit].disabled = False
        react_view.children[button_index_to_edit].callback = response_callback
        await asyncio.sleep(seconds_to_wait)

        await message.edit(view = react_view)


def setup(bot):
    bot.add_cog(Jeux(bot))