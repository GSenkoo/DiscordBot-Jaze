import discord
from discord.ext import commands


class on_message_event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.Cog.listener()
    async def on_message(self, message : discord.Message):
        if not message.guild:
            if message.author != self.bot.user:
                print(message.author.name, message.content)
            return
        
        # -------------- Obtenir le prefix via la mention du bot
        if message.content.startswith(message.guild.me.mention):
            await message.channel.send(f"> Mon prefix sur ce serveur est `{await self.bot.get_prefix(message)}`.")
        
        # -------------- Réactions automatiques
        try: autoreact = await self.bot.db.get_data("guild", "autoreact", False, True, guild_id = message.guild.id)
        except: return
        
        if str(message.channel.id) in autoreact.keys():
            for emoji in autoreact[str(message.channel.id)]:
                try: await message.add_reaction(emoji)
                except: pass


def setup(bot):
    bot.add_cog(on_message_event(bot))