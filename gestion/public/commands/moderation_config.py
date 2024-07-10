import discord
import json
from discord import AllowedMentions as AM
from discord.ext import commands
from utils.Paginator import PaginatorCreator


class Parametres_de_moderations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description = "Définir les rôles qui ne seront pas retirés lors des derank", usage = "<add/del/view> [role]")
    @commands.guild_only()
    async def noderank(self, ctx, action : str, role : discord.Role = None):
        if action not in ["add", "del", "view"]:
            await ctx.send(f"> Action invalide, voici un rappel d'utilisation : `{await self.bot.get_prefix(ctx.message)}noderank <add/del/view> [role]`.")
            return
        
        if (action != "view") and (not role):
            await ctx.send("> Si votre action n'est pas \"view\", alors le paramètre `role` devient obligatoire.")
            return

        noderank_roles = await self.bot.db.get_data("guild", "noderank_roles", guild_id = ctx.guild.id)
        if not noderank_roles:
            noderank_roles = "[]"
        noderank_roles = json.loads(noderank_roles)


        if action == "del":
            if role.id not in noderank_roles:
                await ctx.send(f"> Le rôle {role.mention} n'est pas un rôle noderank.", allowed_mentions = AM.none())
                return
            
            noderank_roles.remove(role.id)
        elif action == "add":
            if role.id in noderank_roles:
                await ctx.send(f"> Le rôle {role.mention} est déjà un rôle noderank.", allowed_mentions = AM.none())
                return
            
            noderank_roles.append(role.id)
        else:
            paginator_creator = PaginatorCreator()
            paginator = await paginator_creator.create_paginator(
                title = "Rôles noderank",
                embed_color = await self.bot.get_theme(ctx.guild.id),
                data_list = [f"<@&{noderank_role}>" for noderank_role in noderank_roles],
                no_data_message = "*Aucun rôle noderank*",
                page_counter = False
            )

            if type(paginator) == list:
                await ctx.send(embed = paginator[0])
            else:
                await paginator.send(ctx)
            return
        
        await self.bot.db.set_data("guild", "noderank_roles", json.dumps(noderank_roles), guild_id = ctx.guild.id)
        await ctx.send(f"> Le rôle {role.mention} " + ("sera désorormais" if action == "del" else "ne sera désormais plus") + " retiré lors des derank.", allowed_mentions = AM.none())


    @commands.command(description = "Définir la limite de suppression de message par commande clear")
    @commands.guild_only()
    async def clearlimit(self, ctx, number : int):
        if not 5 <= number <= 10000:
            await ctx.send("> Votre nombre maximal de suppression de message par commande clear doit être entre 5 et 10000.")
            return
        

        clear_limit = await self.bot.db.get_data("guild", "clear_limit", guild_id = ctx.guild.id)
        if clear_limit == number:
            await ctx.send(f"> La limite de suppression de message par commande clear est déjà définis à {clear_limit}.")
            return
        
        await self.bot.db.set_data("guild", "clear_limit", number, guild_id = ctx.guild.id)
        await ctx.send(f"> La limite de suppression de message par commande clear a été définis à **{number}** messages.")
        

def setup(bot):
    bot.add_cog(Parametres_de_moderations(bot))