import discord
import textwrap
import asyncio
from discord.ext import commands
from utils.PermissionsManager import PermissionsManager


class on_guild_join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild : discord.Guild):
        perms_enabled = await self.bot.db.get_data("guild", "perms_enabled", guild_id = guild.id) # si le bot a déjà été précédement ajouté au serveur et que le serveur avait activé le système de permission
        if perms_enabled:
            permission_manager = PermissionsManager(self.bot)
            await permission_manager.initialize_guild_perms(guild.id)

        user = None
        async for bot_added_log in guild.audit_logs(action = discord.AuditLogAction.bot_add):
            if bot_added_log.target == self.bot.user:
                user = bot_added_log.user
                break
        
        embed = discord.Embed(
            thumbnail = guild.me.avatar.url if guild.me.avatar else None,
            title = f"Merci de m'avoir ajouté sur {guild.name}",
            color = 0xFFFFFF,
            description = textwrap.dedent("""
                Je suis un bot discord **polyvalent** et **totalement français**.
                Par défaut, mon **prefix** sur votre serveur est `+`.
                                          
                Si vous souhaitez **utiliser mes fonctionnalitées** sur votre serveur, il est vivement conseillé de me mettre hiérachiquement **au dessus de tous les autres rôles**.
                                          
                En cas de problème sur le bot, vous pouvez contacter **senkoo.g4l**.
            """)
        )

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label = f"{len(self.bot.guilds)} serveurs", emoji = "🌐", disabled = True))
        view.add_item(discord.ui.Button(label = f"{len(self.bot.users)} utilisateurs", emoji = "👥", disabled = True))

        await asyncio.sleep(1.5) # Pour s'assurer que le bot ai le temps d'avoir rejoins le serveur (car le bot ne peut pas mp un membre qui n'a pas de serveur en commun avec lui)

        try: await user.send(embed = embed, view = view)
        except: pass

        if user != guild.owner:
            try: await guild.owner.send(embed = embed, view = view)
            except: pass
    
def setup(bot):
    bot.add_cog(on_guild_join(bot))