import discord
import json
import asyncio
import os
import sys
from discord.ext import commands
from utils.FilesManager import manage_files


class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description = "Mettre à jour les commandes, évènements et tâches en arrière plan du bot", aliases = ["up", "uc"])
    @commands.guild_only()
    async def update(self, ctx):
        with open("config.json", encoding = "utf-8") as file:
            config_data = json.load(file)
        
        if ctx.author.id not in config_data["developers"]:
            return
        
        a, b, duration = manage_files(self.bot, "unload")
        a, b, duration2 = manage_files(self.bot, "load")

        await ctx.send(f"> {len(self.bot.commands)} commandes mis à jour en {round((duration + duration2) * 100)}ms.")
   
    @commands.command(description = "Arrêter le bot")
    @commands.guild_only()
    async def stop(self, ctx):
        with open("config.json", encoding = "utf-8") as file:
            config_data = json.load(file)
        
        if ctx.author.id not in config_data["developers"]:
            return
        
        await ctx.send("> `[Database] Déconnection de la base de donnée en cours...`")

        print("[Database] Déconnection de la base de donnée en cours...")
        await self.bot.db.close_pool()
        print("[Database] Déconnection de la base de donnée effectuée avec succès.")

        await ctx.send("> `[Database] Déconnection de la base de donnée effectuée, bot déconnecté.`")
        await self.bot.close()

    @commands.command(description = "Redémarrer le bot")
    @commands.guild_only()
    async def restart(self, ctx):
        with open("config.json", encoding = "utf-8") as file:
            config_data = json.load(file)
        
        if ctx.author.id not in config_data["developers"]:
            return
        
        await ctx.send("> `[Database] Déconnection de la base de donnée en cours...`")

        print("[Database] Déconnection de la base de donnée en cours...")
        await self.bot.db.close_pool()
        print("[Database] Déconnection de la base de donnée effectuée avec succès, redémarrage lancé.")

        await ctx.send("> `[Database] Déconnection de la base de donnée effectuée, redémarrage lancé.`")
        os.system("python main.py")        


def setup(bot):
    bot.add_cog(Developer(bot))