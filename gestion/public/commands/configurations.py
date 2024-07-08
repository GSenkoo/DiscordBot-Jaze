import discord
from discord.ext import commands


class Configurations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.command(description = "Changer le thème du bot", aliases = ["setcolor", "color", "settheme"])
    @commands.guild_only()
    async def theme(self, ctx, color : discord.Color):
        await self.bot.set_theme(ctx.guild.id, color.value)
        await ctx.send(f"> Le thème du bot a correctement été défini à `{color}`")


    @commands.command(description = "Modifier le prefix du bot", aliases = ["setprefix"])
    @commands.guild_only()
    async def prefix(self, ctx, prefix : str):
        if len(prefix) > 5:
            await ctx.send("> Votre prefix ne peut pas faire plus de 5 caractères.")
            return
        
        if "`" in prefix:
            await ctx.send("> Votre prefix ne peut pas contenir le caractère \"`\".")
            return
        
        commands_names = [command.name for command in self.bot.commands]
        if prefix in commands_names:
            await ctx.send("> Votre prefix ne peut pas être le nom d'une commande.")
            return
        
        await self.bot.set_prefix(ctx.guild.id, prefix)
        await ctx.send(f"> Le préfix du bot sur ce serveur est désormais `{prefix}`.")
        
        


def setup(bot):
    bot.add_cog(Configurations(bot))