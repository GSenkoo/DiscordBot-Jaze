import discord
from discord.ext import commands
from utils.Database import Database


class on_ready(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"[OnReady] The bot {self.bot.user.name}#{self.bot.user.discriminator} has connected")
        print(f"[Database] Configuration de la base de donnée en cours...")
        db = Database()
        await db.intialize(intialize_tables = ["snipe"])
        print("[Database] Configuration de la base de donnée terminée.")

def setup(bot):
    bot.add_cog(on_ready(bot))