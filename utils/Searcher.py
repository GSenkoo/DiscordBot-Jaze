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
from typing import Union

class Searcher():
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

    async def search_user(self, query : str) -> Union[discord.Member, None]:
        """
        Arguments
        --------------------------------------------
        query `str` :
            Le nom/L'id/La mention de l'utilisateur concerné.

        Return
        --------------------------------------------
        `Union[discord.Member, None]`

        Exemple d'utilisation
        --------------------------------------------
        ```
        import discord
        from discord.ext import commands
        from utils.Searcher import Searcher

        bot = commands.Bot(command_prefix = "+", intents = discord.Intents.all())

        @bot.command
        async def search_ppl(ctx, query):
            my_searcher = Searcher(bot, ctx)
            member = await my_searcher.search_user(query)
            if member:
                await ctx.send(f"Utilisateur trouvé : {member.name}")
            else:
                await ctx.send("Utilisateur invalide.")
        ```
        """
        user = None

        if query.replace("<", "").replace("@", "").replace(">", "").isdigit():
            try:
                user = await self.bot.fetch_user(int(query.replace("<", "").replace("@", "").replace(">", "")))
                return user
            except: pass
        
        if not user:
            def check(usr, qry):
                if usr.name == qry:
                    return usr
                elif usr.name + "#" + usr.discriminator == qry:
                    return usr
                return None
            
            for member in self.ctx.guild.members:
                if check(member, query):
                    return member
        return None
    

    async def search_role(self, query : str, guild : discord.Guild = None) -> Union[discord.Role, None]:
        """
        Arguments
        --------------------------------------------
        query `str` :
            L'id/Le nom/La mention du rôle que vous voulez trouver.
        guild `discord.Guild`, default `None` :
            L'instance d'un serveur spécifique, si celui du contexte donné ne correspond pas.

        Return
        --------------------------------------------
        `Union[discord.Role, None]`

        Example
        --------------------------------------------
        ```
        import discord
        from discord.ext import commands
        from utils.Searcher import Searcher

        bot = commands.Bot(command_prefix = "+", intents = discord.Intents.all())

        @bot.command
        async def search_role(ctx, query):
            my_searcher = Searcher(bot, ctx)
            role = await my_searcher.search_role(query)
            if role:
                await ctx.send(f"Rôle trouvé : {role.name}")
            else:
                await ctx.send("Rôle invalide.")
        ```
        """
        if not guild: guild = self.ctx.guild
        
        for role in self.ctx.guild.fetch_roles():
            if role.name == query:
                return role
            if query.replace("<@&", "").replace("<@", "").replace(">", "").isdigit():
                if role.id == int(query.replace("<@&", "").replace("<@", "").replace(">", "")):
                    return role
        
        return None