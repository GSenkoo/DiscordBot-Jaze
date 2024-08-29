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


dotenv.load_dotenv()

class Jeux(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Générer des blagues d'une certaine catégorie")
    @commands.guild_only()
    async def joke(self, ctx):
        blague_type = {
            "GLOBAL": "Normales",
            "DEV": "Développeurs",
            "DARK": "Humour Noir",
            "LIMIT": "Limites",
            "BEAUF": "Beauf",
            "BLONDES": "Blondes"
        }

        bot = self.bot
        class ChooseJokeType(discord.ui.View):
            async def on_timeout(self) -> None:
                if self.to_components() != self.message.components:
                    return
                try: await self.message.edit(view = None)
                except: pass

            @discord.ui.select(
                placeholder = "Choisir un type de blague",
                options = [
                    discord.SelectOption(label = joke_name, value = joke_id) for joke_id, joke_name in blague_type.items()
                ]
            )
            async def select_callback(self, select, interaction):
                if ctx.author != interaction.user:
                    await ctx.send("> Vous n'êtes pas autorisés à intéragir avec ceci.")
                    return
                
                async def get_embed_joke() -> discord.Embed:
                    joke_api = BlaguesAPI(os.getenv("BLAGUE_API_KEY"))
                    joke_found = await joke_api.random_categorized(getattr(BlagueType, select.values[0]))

                    embed = discord.Embed(
                        title = f"Type de Blague : {blague_type[select.values[0]]}",
                        description = "*Ces blagues sont générées par une API indépendante de nos bots, donc en cas de problème, nous ne pouvons pas en être tenus responsables.*",
                        color = await bot.get_theme(ctx.guild.id)
                    )

                    embed.add_field(name = "Blague", value = joke_found.joke)
                    embed.add_field(name = "Réponse", value = "||" + joke_found.answer + "||")

                    return embed
                
                class Regen(discord.ui.View):
                    async def on_timeout(self) -> None:
                        try: await self.message.edit(view = None)
                        except: pass

                    @discord.ui.button(label = "Regénérer", emoji = "🔄")
                    async def regen_callback(self, button, interaction):
                        if ctx.author != interaction.user:
                            await ctx.send("> Vous n'êtes pas autorisés à intéragir avec ceci.")
                            return
                        
                        await interaction.edit(embed = await get_embed_joke())

                await interaction.edit(embed = await get_embed_joke(), view = Regen())
            
        await ctx.send(
            embed = discord.Embed(
                title = "Quel type de blague souhaitez-vous obtenir?",
                color = await self.bot.get_theme(ctx.guild.id)
            ),
            view = ChooseJokeType()
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
        
        rules = {
            "pierre": "ciseaux",
            "papier": "pierre",
            "ciseaux": "papier"
        }

        emojis = {
            "pierre": "🪨",
            "papier": "📄",
            "ciseaux": "✂️"
        }

        async def get_pfc_embed(author_pts, oponent_pts, current_player, move = None, oponent_move = None) -> discord.Embed:
            if (author_pts == 3) or (oponent_pts == 3):
                return discord.Embed(
                    title = "Partie pfc",
                    description = 
                    ("*Bien joué. Vous avez gagné cette partie.*" if author_pts == 3 else "*Dommage. Vous avez perdu cette partie.*")
                    if not member else
                    (f"*Victoire attribuée à {ctx.author.mention}. Bien joué.*" if author_pts == 3 else f"*Victoire attribuée à {member.mention}. Bien joué.*"),
                    color = await self.bot.get_theme(ctx.guild.id)
                )
            
            embed = discord.Embed(
                title = "Partie pfc",
                color = await self.bot.get_theme(ctx.guild.id),
                description = f"*Utilisez le menu déroulant pour choisir une option.*\n"
                + f"*Expiration de la partie <t:{round(datetime.now().timestamp()) + 30}:R>.*\n"
                + f"*{current_player.display_name} est entrain de faire son choix...*",
            )

            if move:
                if rules[move] == oponent_move: text_winner = f"(Gagnant : {ctx.author.mention})"
                elif move == oponent_move: text_winner = f"(Égalitée)"
                else: text_winner = f"(Gagnant : {ctx.guild.me if not member else member.mention})"

                embed.add_field(name = "Choix", value = emojis[move] + " vs " + emojis[oponent_move] + f" {text_winner}", inline = False)

            embed.add_field(name = ctx.author.display_name, value = f"{author_pts} pts")
            embed.add_field(name = ctx.guild.me.display_name if not member else member.display_name, value = f"{oponent_pts} pts")

            return embed

        bot = self.bot
        class PfcGame(discord.ui.View):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                self.author_pts = 0
                self.oponent_pts = 0
                self.choosing = ctx.author
                self.move = None
                self.oponent_move = None

            async def on_timeout(self):
                if not self.message.components:
                    return
                
                try:
                    await self.message.edit(
                        view = None,
                        embed = discord.Embed(
                            title = "Partie pfc",
                            description = f"*{self.choosing.display_name} a été déclaré forfait pour inactivité.*",
                            color = await bot.get_theme(ctx.guild.id)
                        )
                    )
                except: pass
            
            @discord.ui.select(
                placeholder = "Choisir une action",
                options = [
                    discord.SelectOption(label = move_name.capitalize(), emoji = move_emoji, value = move_name) for move_name, move_emoji in emojis.items()
                ]
            )
            async def make_choice_select(self, select, interaction):
                if interaction.user != ctx.author and interaction.user != member:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                if self.choosing != interaction.user:
                    await interaction.response.send_message("> Merci de patienter, ce n'est pas encore à vous de jouer.", ephemeral = True)
                    return                

                if interaction.user == ctx.author:
                    self.choosing = ctx.guild.me if not member else member
                    await interaction.edit(embed = await get_pfc_embed(self.author_pts, self.oponent_pts, self.choosing))
                    self.move = select.values[0]

                    if not member:
                        await asyncio.sleep(random.randint(1, 3))
                        self.oponent_move = random.choice(["pierre", "papier", "ciseaux"])
                    else: return
                else:
                    self.oponent_move = select.values[0]


                if rules[self.move] == self.oponent_move: self.author_pts += 1
                elif self.move == self.oponent_move: pass
                else: self.oponent_pts += 1

                self.choosing = ctx.author

                if 3 in [self.oponent_pts, self.author_pts]:
                    await interaction.edit(embed = await get_pfc_embed(self.author_pts, self.oponent_pts, self.choosing, self.move, self.oponent_move), view = None)
                    return
                
                await interaction.edit(embed = await get_pfc_embed(self.author_pts, self.oponent_pts, self.choosing, self.move, self.oponent_move))

        await ctx.send(embed = await get_pfc_embed(0, 0, ctx.author), view = PfcGame(timeout = 30))


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