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
        data_owner = await self.bot.db.get_data("guild", "owners", guild_id = ctx.guild.id)
        if not data_owner: data_owner = "[]"
        current_owners = json.loads(data_owner)

        if user.id in current_owners:
            await ctx.send(f"> **{user.display_name}** a déjà la permission owner")
            return
        
        current_owners.append(user.id)
        await self.bot.db.set_data("guild", "owners",  json.dumps(current_owners), True, guild_id = ctx.guild.id)


        await ctx.send(f"> **{user.display_name}** a désormais la permission owner.")
    

    @commands.command(description = "Retirer la permission owner à un utilisateur")
    @commands.guild_only()
    async def unowner(self, ctx, user : discord.User):
        data_owner = await self.bot.db.get_data("guild", "owners", guild_id = ctx.guild.id)
        if not data_owner: data_owner = "[]"
        current_owners = json.loads(data_owner)

        if user.id not in current_owners:
            await ctx.send(f"> **{user.display_name}** n'a pas les permissions owners")
            return
        
        current_owners.remove(user.id)
        await self.bot.db.set_data("guild", "owners",  json.dumps(current_owners), True, guild_id = ctx.guild.id)

        await ctx.send(f"> **{user.display_name}** n'a désormais plus la permission owner.")


    @commands.command(description = "Voir les utilisateurs possédant la permission owner")
    @commands.guild_only()
    async def owners(self, ctx):
        data_owner = await self.bot.db.get_data("guild", "owners", guild_id = ctx.guild.id)
        if not data_owner: data_owner = "[]"
        current_owners = json.loads(data_owner)
        

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