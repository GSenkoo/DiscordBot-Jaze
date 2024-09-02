import discord
import os
import dotenv

from blagues_api import BlaguesAPI, BlagueType
from .functions import get_embed_joke

dotenv.load_dotenv()

blague_type = {
    "GLOBAL": "Normales",
    "DEV": "Développeurs",
    "DARK": "Humour Noir",
    "LIMIT": "Limites",
    "BEAUF": "Beauf",
    "BLONDES": "Blondes"
}

class JokeGenerator(discord.ui.View):
    def __init__(self, ctx, bot):
        super().__init__()
        self.ctx = ctx
        self.bot = bot

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
        if self.ctx.author != interaction.user:
            await self.ctx.send("> Vous n'êtes pas autorisés à intéragir avec ceci.")
            return
        
        self_ = self
        class Regen(discord.ui.View):
            async def on_timeout(self) -> None:
                try: await self.message.edit(view = None)
                except: pass

            @discord.ui.button(label = "Regénérer", emoji = "🔄")
            async def regen_callback(self, button, interaction):
                if self_.ctx.author != interaction.user:
                    await self_.ctx.send("> Vous n'êtes pas autorisés à intéragir avec ceci.")
                    return
                
                await interaction.edit(embed = await get_embed_joke(self_.ctx, self_.bot, select.values[0]))

        await interaction.edit(embed = await get_embed_joke(self_.ctx, self_.bot, select.values[0]), view = Regen())