import discord
import json
from discord.ext import commands
from utils.Paginator import PaginatorCreator

class Proprietaire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.command(description = "Ajouter la permission owner à un utilisateur")
    @commands.guild_only()
    async def owner(self, ctx, user : discord.User):
        current_owners = await self.bot.db.get_data("guild", "owners", True, guild_id = ctx.guild.id)

        if user == ctx.author:
            await ctx.send("> Vous n'avez pas besoin des permissions owners.")
            return

        if user.id in current_owners:
            await ctx.send(f"> **{user.display_name}** a déjà la permission owner.")
            return
        
        current_owners.append(user.id)
        await self.bot.db.set_data("guild", "owners",  json.dumps(current_owners), True, guild_id = ctx.guild.id)


        await ctx.send(f"> **{user.display_name}** a désormais la permission owner.")
    

    @commands.command(description = "Retirer la permission owner à un utilisateur")
    @commands.guild_only()
    async def unowner(self, ctx, user : discord.User):
        current_owners = await self.bot.db.get_data("guild", "owners", True, guild_id = ctx.guild.id)

        if user.id not in current_owners:
            await ctx.send(f"> **{user.display_name}** n'a pas les permissions owners.")
            return
        
        current_owners.remove(user.id)
        await self.bot.db.set_data("guild", "owners",  json.dumps(current_owners), True, guild_id = ctx.guild.id)

        await ctx.send(f"> **{user.display_name}** n'a désormais plus la permission owner.")


    @commands.command(description = "Retirer la permission owner à tous les utilisateurs la possédant", aliases = ["dlow"])
    @commands.guild_only()
    async def delowners(self, ctx):
        current_owners = await self.bot.db.get_data("guild", "owners", True, guild_id = ctx.guild.id)

        if len(current_owners) == 0:
            await ctx.send("> Il n'y aucun utilisateur avec la permission owner.")
            return

        await self.bot.db.set_data("guild", "owners", json.dumps([]), guild_id = ctx.guild.id)
        await ctx.send(f"> La permission owner a été retiré à un total de {len(current_owners)} utilisateurs.")


    @commands.command(description = "Voir les utilisateurs possédant la permission owner")
    @commands.guild_only()
    async def owners(self, ctx):
        current_owners = await self.bot.db.get_data("guild", "owners", True, guild_id = ctx.guild.id)
        

        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = "Owners",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = [f"<@{owner}>" for owner in current_owners],
            pages_looped = True,
            no_data_message = "*Aucun utilisateur owner*"
        )

        if type(paginator) == list:
            await ctx.send(embed = paginator[0])
        else:
            await paginator.send(ctx)
        

        


def setup(bot):
    bot.add_cog(Proprietaire(bot))