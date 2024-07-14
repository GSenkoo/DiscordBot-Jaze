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

        Exemple
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
        
        for role in await self.ctx.guild.fetch_roles():
            if role.name == query:
                return role
            if query.replace("<@&", "").replace("<@", "").replace(">", "").isdigit():
                if role.id == int(query.replace("<@&", "").replace("<@", "").replace(">", "")):
                    return role
        
        return None
    

    async def search_channel(self, query : str, guild : discord.Guild = None) -> Union[discord.TextChannel, None]: # all types of channel
        """
        Arguments
        --------------------------------------------
        query `str` :
            L'id/Le nom/La mention du salon que vous voulez trouver.
        guild `discord.Guild`, default `None` :
            L'instance d'un serveur spécifique, si celui du contexte donné ne correspond pas.

        Return
        --------------------------------------------
        `Union[discord.Channel, None]`

        Exemple
        --------------------------------------------
        ```
        import discord
        from discord.ext import commands
        from utils.Searcher import Searcher

        bot = commands.Bot(command_prefix = "+", intents = discord.Intents.all())

        @bot.command
        async def search_channel(ctx, query):
            my_searcher = Searcher(bot, ctx)
            channel = await my_searcher.search_channel(query)
            if channel:
                await ctx.send(f"Salon trouvé : {channel.mention}")
            else:
                await ctx.send("Salon invalide.")
        ```
        """
        if not guild: guild = self.ctx.guild
        
        query_rmention = query.replace("<#", "").replace(">", "")
        channel = None
        if query_rmention.isdigit():
            try: channel = await guild.fetch_channel(int(query_rmention))
            except: pass

        if channel:
            return channel
        
        for channel in guild.roles:
            if channel.name == query:
                return channel
            if query_rmention.isdigit():
                if channel.id == int(query.replace("<@&", "").replace("<@", "").replace(">", "")):
                    return channel
        
        return None