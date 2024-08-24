import discord
from discord.ext import commands, tasks

class statut_updater(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_update.start()
        self.last_guilds_count = 0

    def cog_unload(self):
        self.status_update.cancel()

    @tasks.loop(seconds = 30)
    async def status_update(self):
        if len(self.bot.guilds) != self.last_guilds_count:
            await self.bot.change_presence(activity = discord.Streaming(name = f"{len(self.bot.guilds)} serveurs", url = "https://www.twitch.tv/discord"))
            self.last_guilds_count = len(self.bot.guilds)

    @status_update.before_loop
    async def before_status_update(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(statut_updater(bot))