import discord
import textwrap
from discord.ext import commands
from utils.PermissionsManager import PermissionsManager


class on_guild_join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild : discord.Guild):
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
                Je suis un bot Discord multifonction et complet, conçu pour offrir une large gamme de fonctionnalités avancées. En raison de ma complexité et de mes capacités étendues, je ne suis pas recommandé pour les petits serveurs, car ceux-ci pourraient ne pas tirer pleinement parti de toutes mes fonctionnalités.

                Pour configurer les permissions de mes commandes, vous pouvez utiliser la commande `+perms`. Si vous avez des difficultés au niveau de la gestion des permissions, la commande `+guideperms` est là pour vous guider pas à pas dans la configuration des permissions. Par défaut, seul le propriétaire du serveur a accès à ces commandes (sauf commandes public), garantissant ainsi une gestion sécurisée et contrôlée.
            """)
        )

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label = f"{len(self.bot.guilds)} serveurs", emoji = "🌐", disabled = True))
        view.add_item(discord.ui.Button(label = f"{len(self.bot.users)} utilisateurs", emoji = "👥", disabled = True))


        try: await user.send(embed = embed, view = view)
        except: pass

        if user != guild.owner:
            try: await guild.owner.send(embed = embed, view = view)
            except: pass
    
def setup(bot):
    bot.add_cog(on_guild_join(bot))