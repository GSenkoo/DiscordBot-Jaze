import discord
from discord.ext import commands
from utils.Database import Database
from utils.PermissionsManager import PermissionsManager


class on_ready(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"[OnReady] The bot {self.bot.user.name}#{self.bot.user.discriminator} has connected")
        print(f"[Database] Configuration de la base de donnée en cours...")

        await self.bot.create_db()
        await self.bot.db.intialize(intialize_tables = ["snipe", "snipe_edit"])
        print("[Database] Configuration de la base de donnée terminée.")


        print("[PermissionManager] Initialisation des permissions des serveurs en cours...")
        permission_manager = PermissionsManager(self.bot)

        for guild in self.bot.guilds:
            perms_enabled = await self.bot.db.get_data("guild", "perms_enabled", guild_id = guild.id)
            if perms_enabled:
                await permission_manager.initialize_guild_perms(guild.id)
                print(f"[PermissionManager] Le serveur {guild.name} a été intialisé avec succès.")
        print("[PermissionManager] Initialisation des serveurs terminés.")


def setup(bot):
    bot.add_cog(on_ready(bot))