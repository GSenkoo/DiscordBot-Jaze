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
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from discord.ext import commands

sys.set_int_max_str_digits(999999999) # Pour la commande +calc

class Utilitaire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Chercher le salon vocal dans lequel se situe un utilisateur")
    @commands.guild_only()
    async def find(self, ctx, member : discord.Member):
        if not member.voice:
            await ctx.send(f"> " +  ("Vous n'êtes" if ctx.author == member else f"{member.mention} n'est") + " pas dans un salon vocal", allowed_mentions = None)
            return
        
        await ctx.send(f"> " + ("Vous êtes" if ctx.author == member else f"{member.mention} est") + f" actuellement dans le salon {member.voice.channel.mention}")


    @commands.command(usage = "<calcul>", description = "Faire un calcul", aliases = ["calculate"])
    @commands.guild_only()
    async def calc(self, ctx, *calcul):
        calcul = "".join(calcul)
        calcul = calcul.replace("\"", "").replace("x", "*").replace(",", ".").replace("÷", "/").replace("^^", "**")
        try:
            result = sympy.sympify(calcul)
        except:
            await ctx.send("> Syntaxe de calcul invalide.")
            return
        
        try:
            embed = discord.Embed(
                title = "Résultat",
                description = f"```yml\n" + (str(result) if len(str(result)) < 500 else str(result)[:500] + "...") + "\n```",
                color = 0xFFFFFF
            )
        except:
            await ctx.send("> Résultat trop grand.")
            return

        await ctx.send(embed = embed)


    @commands.command(usage = "<search>", description = "Faire une recherche wikipedia", aliases = ["wikipedia", "wkp"])
    @commands.guild_only()
    async def wiki(self, ctx, *search):
        search = " ".join(search)

        if len(search) > 100:
            await ctx.send("Votre recherche est trop longue (plus de 100 caractères).")
            return
        
        def get_summary(topic, sentences):
            wikipedia.set_lang("fr")
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
            await ctx.send(f"> Aucun résultat pour {search}")
            return

        if not summary:
            await ctx.send(f"> Aucun résultats pour " +  search.replace("`", "'"), allowed_mentions = None)
            return

        await ctx.send(
            embed = discord.Embed(
                title = "Recherche : " + search,
                description = summary.replace("====", "**").replace(" ====", "").replace("===", "###").replace(" ###", "").replace("==", "## ").replace(" ##", ""),
                color = await self.bot.get_theme(ctx.guild.id),
                timestamp = datetime.now()
            )
        )


    @commands.command(usage = "<text>", description = "Traduir un texte dans un langage que vous choisirez sur un menu", aliases = ["tsl"])
    @commands.guild_only()
    @commands.cooldown(rate = 5, per = 60)
    async def translate(self, ctx, *text):
        ... # Utiliser l'API DeepL

def setup(bot):
    bot.add_cog(Utilitaire(bot))