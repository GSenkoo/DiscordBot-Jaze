import discord
import os
import dotenv
from discord.ext import commands
from blagues_api import BlaguesAPI, BlagueType


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
                        
                        await interaction.message.edit(embed = await get_embed_joke())
                        await interaction.response.defer()

                await interaction.message.edit(embed = await get_embed_joke(), view = Regen())
                await interaction.response.defer()
            
        await ctx.send(
            embed = discord.Embed(
                title = "Quel type de blague souhaitez-vous obtenir?",
                color = await self.bot.get_theme(ctx.guild.id)
            ),
            view = ChooseJokeType()
        )


def setup(bot):
    bot.add_cog(Jeux(bot))