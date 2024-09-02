import os
import discord

from dotenv import load_dotenv
from blagues_api import BlaguesAPI, BlagueType

load_dotenv()
blague_type = {
    "GLOBAL": "Normales",
    "DEV": "Développeurs",
    "DARK": "Humour Noir",
    "LIMIT": "Limites",
    "BEAUF": "Beauf",
    "BLONDES": "Blondes"
}

async def get_embed_joke(ctx, bot, joke_type) -> discord.Embed:
    joke_api = BlaguesAPI(os.getenv("BLAGUE_API_KEY"))
    joke_found = await joke_api.random_categorized(getattr(BlagueType, joke_type))

    embed = discord.Embed(
        title = f"Type de Blague : {blague_type[joke_type]}",
        description = "*Ces blagues sont générées par une API indépendante de nos bots, donc en cas de problème, nous ne pouvons pas en être tenus responsables.*",
        color = await bot.get_theme(ctx.guild.id)
    )

    embed.add_field(name = "Blague", value = joke_found.joke)
    embed.add_field(name = "Réponse", value = "||" + joke_found.answer + "||")

    return embed