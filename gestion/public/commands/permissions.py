import discord
import textwrap
from datetime import datetime
from discord.ext import commands


class Gestion_des_Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Lire le guide de configuration des permissions.", aliases = ["gp"])
    @commands.guild_only()
    async def guideperms(self, ctx):
        bot = self.bot

        class PermGuideMenu(discord.ui.View):
            async def on_timeout(self):
                try: await self.message.edit(view = None)
                except: pass

            @discord.ui.select(
                placeholder = "Choisir un guide",
                options = [
                    discord.SelectOption(label = "1. Permissions hiérarchiques et personnalisées", value = "perms_hp"),
                    discord.SelectOption(label = "2. Comprendre vos configurations", value = "understand_config"),
                    discord.SelectOption(label = "3. Gérer les commandes de vos permissions", value = "config_commands"),
                    discord.SelectOption(label = "4. Gérer les autorisations de vos permissions", value = "manage_perms_of_perms"),
                    discord.SelectOption(label = "5. Les limites de configurations", value = "config_limit")
                ]
            )
            async def select_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.response.defer()

                for option in select.options:
                    option.default = option.value == select.values[0]

                if select.values[0] == "perms_hp":
                    await interaction.message.edit(
                        embed = discord.Embed(
                            color = await bot.get_theme(ctx.guild.id),
                            description = textwrap.dedent("""
                                ## Différences théoriques
                                La différence principale entre les permissions hiérarchiques et les permissions personnalisées est que les permissions hiérarchiques sont triées par hiérarchie (comme son nom l'indique). Cela signifie que chaque permission a accès à toutes les commandes des permissions inférieures (en plus des siennes).

                                En plus de cette différence, vous devrez également noter que les permissions hiérarchiques sont notées par des nombres de 1 à 9 représentant leur niveau dans la hiérarchie des permissions hiérarchiques.

                                ## Différences pratiques
                                La distinction entre ces deux types de permissions peut encore sembler assez floue. Voici donc un exemple concret :

                                *"Thomas souhaite faire en sorte que les @modérateurs de son serveur aient accès à une certaine commande `+warn`. Il a déjà configuré ses paramètres de telle sorte que les modérateurs aient accès à la permission 2.*
                                *Mais Thomas veut aussi que tous les rôles avec une permission hiérarchique supérieure aient accès à cette commande. Comment faire ?"*

                                > Dans un premier temps, il serait stupide de créer des permissions personnalisées pour chaque rôle, cela prendrait un temps fou et la gestion serait plus difficile.
                                > Pour résoudre ce problème, Thomas n'aura qu'à configurer ses permissions de telle sorte que les rôles supérieurs à @modérateurs aient accès à une permission supérieure à la permission 2, et c'est fini.
                            """)
                        ),
                        view = self
                    )

        current_date = datetime.now()
        await ctx.send(
            embed = discord.Embed(
                title = "Guide de configuration de vos permissions",
                description = textwrap.dedent(f"""
                {'Bonjour' if current_date.hour > 6 and current_date.hour < 20 else 'Bonsoir'} **{ctx.author.display_name}**, ce guide vous permettra de configurer facilement vos permissions. En suivant celui-ci du début à la fin, vous serez au final capable de :
                
                1. *Voir la différence permissions hiérarchiques et personnalisées.*
                2. *Comprendre la vérification des permissions par le bot.*
                3. *Créer ou modifier vos permissions avec aisance.*

                Vous pouvez également vous fier à votre intuition si vous êtes déjà familier avec ce type de configuration. En cas de problème de compréhension, vous pouvez toujours contacter et demander de l'aide à notre support.
                """),
                color = await self.bot.get_theme(ctx.guild.id)
            ),
            view = PermGuideMenu()
        )

    
    @commands.command(description = "Voir les permissions hiérarchiques")
    @commands.guild_only()
    async def perms(self, ctx):
        ...


    @commands.command(description = "Voir vos permissions personnalisées")
    @commands.guild_only()
    async def customperms(self, ctx):
        ...

    
    

    


def setup(bot):
    bot.add_cog(Gestion_des_Permissions(bot))