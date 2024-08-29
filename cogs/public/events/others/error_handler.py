import discord
import json
from discord.ext import commands

class error_handler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        def display(text : str):
            return text if len(text) <= 30 else text[:30] + "..."
        
        if ctx.guild and not ctx.channel.permissions_for(ctx.guild.me).send_messages:
            try: await ctx.author.send(f"> Je n'ai pas les permissions nécessaires pour envoyer des messages dans le salon <#{ctx.channel.id}>.")
            except: pass

        with open("cogs/private/data/permissions_translations.json", encoding = "utf-8") as file:
            permissions_translations = json.load(file)
  
        match type(error):
            case commands.CommandNotFound:
                pass
            case commands.DisabledCommand:
                pass
            case commands.NotOwner:
                pass
            case commands.CheckFailure:
                pass # L'utilisateur ne peut pas utiliser la commande
            case commands.CommandOnCooldown:
                await ctx.send(f"> Commande en cooldown, merci de réessayer dans {round(error.retry_after)} secondes.")
            case commands.MissingRequiredArgument:
                await ctx.send(f"> Merci de donner un bon nombre d'arguments (utilisation : `{await self.bot.get_prefix(ctx)}{ctx.command} {ctx.command.usage if ctx.command.usage else ctx.command.signature}`).")
            case commands.BadArgument:
                await ctx.send(f"> Merci de véririfez vos types d'arguments (utilisation : `{await self.bot.get_prefix(ctx)}{ctx.command} {ctx.command.usage if ctx.command.usage else ctx.command.signature}`).")
            case commands.PrivateMessageOnly:
                await ctx.send("> Cette commande ne peut pas être utilisé en dehors de mes messages privés.")
            case commands.TooManyArguments:
                await ctx.send(f"> Merci de donner des arguments corrects (utilisation : `{await self.bot.get_prefix(ctx)}{ctx.command} {ctx.command.usage if ctx.command.usage else ctx.command.signature}`).")
            case commands.MessageNotFound:
                await ctx.send(f"> Le message donné ({display(error.argument)}) est invalide.", allowed_mentions = None)
            case commands.MemberNotFound:
                await ctx.send(f"> Le membre donné ({display(error.argument)}) est invalide.", allowed_mentions = None)
            case commands.GuildNotFound:
                await ctx.send(f"> Le serveur donné ({display(error.argument)}) est invalide, ou alors je n'y ai pas accès.", allowed_mentions = None)
            case commands.UserNotFound:
                await ctx.send(f"> L'utilisateur donné ({display(error.argument)}) est invalide.", allowed_mentions = None)
            case commands.ChannelNotFound:
                await ctx.send(f"> Le salon donné ({display(error.argument)}) est invalide.", allowed_mentions = None)
            case commands.ChannelNotReadable:
                await ctx.send(f"> Je ne peux pas accéder au salon donné ({display(error.argument)}).", allowed_mentions = None)
            case commands.ThreadNotFound:
                await ctx.send(f"> Le thread donné ({display(error.argument)}) est introuvable.", allowed_mentions = None)
            case commands.BadColorArgument:
                await ctx.send(f"> La couleur donné ({display(error.argument)}) est invalide.", allowed_mentions = None)
            case commands.RoleNotFound:
                await ctx.send(f"> Le rôle donné ({display(error.argument)}) est invalide.", allowed_mentions = None)
            case commands.BadInviteArgument:
                await ctx.send(f"> Le lien d'invitation donné ({display(error.argument)}) est invalide.", allowed_mentions = None)
            case commands.EmojiNotFound:
                await ctx.send(f"> L'emoji donné ({display(error.argument)}) est invalide.", allowed_mentions = None)
            case commands.GuildStickerNotFound:
                await ctx.send(f"> Le sticker donné ({display(error.argument)}) est introuvable.", allowed_mentions = None)
            case commands.BadBoolArgument:
                await ctx.send(f"> L'argument booléen (oui/non, vrai/faux, on/off) donné ({display(error.argument)}) est invalide.", allowed_mentions = None)
            case commands.MissingPermissions:
                await ctx.send(f"> Vous n'avez pas les permissions nécessaires (`{'`, `'.join([permissions_translations[perm] for perm in error.missing_permissions])}`) pour faire ceci.")
            case commands.BotMissingPermissions:
                await ctx.send(f"> Je n'ai pas les permissions nécessaires (`{'`, `'.join([permissions_translations[perm] for perm in error.missing_permissions])}`) pour faire ceci.")
            case commands.MissingRole:
                await ctx.send(f"> Vous n'avez pas les rôles nécessaires (<@&{'>, <@&'.join(str(role_id) for role_id in error.missing_role)}>) pour faire ceci.", allowed_mentions = None)
            case commands.BotMissingRole:
                await ctx.send(f"> Je n'ai pas les rôles nécessaires (<@&{'>, <@&'.join(str(role_id) for role_id in error.missing_role)}>) pour faire ceci.", allowed_mentions = None)
            case commands.MissingAnyRole:
                await ctx.send(f"> Vous n'avez pas l'un des rôles nécessaires (<@&{'>, <@&'.join(str(role_id) for role_id in error.missing_role)}>) pour faire ceci.", allowed_mentions = None)
            case commands.BotMissingAnyRole:
                await ctx.send(f"> Je n'ai pas l'un des rôles nécessaires (<@&{'>, <@&'.join(str(role_id) for role_id in error.missing_role)}>) pour faire ceci.", allowed_mentions = None)
            case commands.NSFWChannelRequired:
                await ctx.send(f"> Vous devez être dans un salon NSFW pour faire ceci.")
            case _:
                raise error
            
    
def setup(bot):
    bot.add_cog(error_handler(bot))