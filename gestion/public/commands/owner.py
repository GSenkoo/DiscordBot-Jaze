import discord
import json
from discord.ext import commands
from utils.Paginator import PaginatorCreator

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.command(description = "Ajouter un utilisateur dans la whitelist", aliases = ["whitelist"])
    @commands.guild_only()
    async def wl(self, ctx, user : discord.User):

        data_wl = await self.bot.db.get_data("guild", "whitelist", guild_id = ctx.guild.id)
        if not data_wl: data_wl = "[]"
        current_whitelists = json.loads(data_wl)

        if user.id in current_whitelists:
            await ctx.send(f"> **{user.display_name}** est déjà dans la whitelist")
            return
        
        current_whitelists.append(user.id)
        await self.bot.db.set_data("guild", "whitelist",  json.dumps(current_whitelists), True, guild_id = ctx.guild.id)

        await ctx.send(f"> **{user.display_name}** est désormais dans la whitelist.")
    

    @commands.command(description = "Retirer un utilisateur de la white list", aliases = ["unwhitelist"])
    @commands.guild_only()
    async def unwl(self, ctx, user : discord.User):
        data_wl = await self.bot.db.get_data("guild", "whitelist", guild_id = ctx.guild.id)
        if not data_wl: data_wl = "[]"
        current_whitelists = json.loads(data_wl)

        if user.id not in current_whitelists:
            await ctx.send(f"> **{user.display_name}** n'est pas dans la whitelist")
            return

        current_whitelists.remove(user.id)
        await self.bot.db.set_data("guild", "whitelist",  json.dumps(current_whitelists), True, guild_id = ctx.guild.id)

        await ctx.send(f"> **{user.display_name}** n'est désormais plus dans whitelist.")


    @commands.command(description = "Voir les utilisateurs dans la whitelist", aliases = ["whitelists"])
    @commands.guild_only()
    async def wls(self, ctx):
        data_wl = await self.bot.db.get_data("guild", "whitelist", guild_id = ctx.guild.id)
        if not data_wl: data_wl = "[]"
        current_whitelists = json.loads(data_wl)

        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = "White list",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = [f"<@{user}>" for user in current_whitelists],
            pages_looped = True,
            no_data_message = "*Aucun utilisateur dans la whitelist*"
        )

        if type(paginator) == list:
            await ctx.send(embed = paginator[0])
        else:
            await paginator.send(ctx)
        

        
def setup(bot):
    bot.add_cog(Owner(bot))