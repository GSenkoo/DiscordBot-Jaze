import discord
import json
import asyncio
import os
import sys
from discord.ext import commands
from utils.FilesManager import manage_files
from utils.Paginator import PaginatorCreator


class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description = "Mettre à jour les commandes, évènements et tâches en arrière plan du bot", aliases = ["up", "uc"])
    async def update(self, ctx):
        a, b, duration = manage_files(self.bot, "unload")
        a, b, duration2 = manage_files(self.bot, "load")

        await ctx.send(f"> {len(self.bot.commands)} commandes mis à jour en {round((duration + duration2) * 100)}ms.")


    @commands.command(description = "Arrêter le bot")
    async def stop(self, ctx):
        await ctx.send("> `[Database] Déconnection de la base de donnée en cours...`")

        print("[Database] Déconnection de la base de donnée en cours...")
        await self.bot.db.close_pool()
        print("[Database] Déconnection de la base de donnée effectuée avec succès.")

        await ctx.send("> `[Database] Déconnection de la base de donnée effectuée, bot déconnecté.`")
        await self.bot.close()
   

    @commands.command(description = "Voir les serveurs sur lequel le bot est")
    async def serverlist(self, ctx):
        paginator_creator = PaginatorCreator()
        guilds_data = [f"{guild.name} (`{guild.id}`) - {len(guild.members)} membres" for guild in self.bot.guilds]

        paginator = await paginator_creator.create_paginator(
            title = "Liste des serveurs",
            embed_color = 0xFFFFFF,
            data_list = guilds_data,
            data_per_page = 20
        )

        if type(paginator) == list: await ctx.send(embed = paginator[0])
        else: await paginator.send(ctx)


    @commands.command(description = "Obtenir une invitation vers un serveur spécifique.")
    async def serverinvite(self, ctx, guild : discord.Guild):
        try:
            invitation = await guild.text_channels[0].create_invite(reason = "Demande du développeur")
        except Exception as e:
            await ctx.send(f"> Je ne peux pas créer un lien d'invitation pour le serveur **{guild.name}** ({e}).")
            return

        invite_link_view = discord.ui.View(timeout = None)
        invite_link_view.add_item(discord.ui.Button(label = "Rejoindre", url = invitation.url, style = discord.ButtonStyle.link))

        await ctx.send(
            embed = discord.Embed(
                author = discord.EmbedAuthor(name = guild.name, icon_url = ctx.guild.icon.url if ctx.guild.icon else None),
                description = "Pour accéder au serveur, redirigez vous vers le lien du bouton ci-dessous.",
                color = 0xFFFFFF
            ),
            view = invite_link_view
        )


def setup(bot):
    bot.add_cog(Developer(bot))