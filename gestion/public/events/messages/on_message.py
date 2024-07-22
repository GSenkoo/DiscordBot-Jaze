import discord
from discord.ext import commands


class on_message_event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            print(message.author.name, message.content)
            return
        if message.content.startswith(message.guild.me.mention):
            await message.channel.send(f"> Mon prefix sur ce serveur est `{await self.bot.get_prefix(message)}`.")


def setup(bot):
    bot.add_cog(on_message_event(bot))