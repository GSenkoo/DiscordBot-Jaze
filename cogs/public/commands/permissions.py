import discord
import textwrap
import json
import asyncio

from discord import AllowedMentions as AM
from datetime import datetime
from discord.ext import commands
from utils.PermissionsManager import PermissionsManager
from utils.Paginator import PaginatorCreator


class MyViewClass(discord.ui.View):
    async def on_timeout(self):
        try: await self.message.edit(view = None)
        except: pass


# ------------------ Les permissions qui peuvent être utilisés pour les "permissions autorisées"
guildpermissions = [
    "administrator",
    "kick_members",
    "ban_members",
    "manage_channels",
    "manage_guild",
    "view_audit_log",
    "manage_messages",
    "mention_everyone",
    "manage_roles",
    "manage_webhooks",
    "manage_emojis_and_stickers",
    "manage_threads",
    "moderate_members"
]


# ------------------ Les noms des permissions 0, 10 et 11
custom_names = {
    "0": "Public",
    "10": "Owner",
    "11": "Propriéataire"
}

async def delete_message(message):
    try: await message.delete()
    except: pass

async def check_perms_enabled(ctx):
    permissions_enabled = await ctx.bot.db.get_data("guild", "perms_enabled", guild_id = ctx.guild.id)
    if not permissions_enabled:
        await ctx.send(f"> Pour activer le système de permission avancé utilisez `{await ctx.bot.get_prefix(ctx.message)}advancedperms <on/off>`.")
    return permissions_enabled


class Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.command(description = "Activer/Désactiver le système de permission avancé, en étant désactivé le bot se basera sur les permissions discord", usage = "<on/off>", aliases = ["advancedperm"])
    @commands.guild_only()
    async def advancedperms(self, ctx, action):
        action = action.lower()
        if action not in ["on", "off"]:
            await ctx.send(f"> Votre action est invalide, rappel d'utilisation de la commande : `{await self.bot.get_prefix(ctx.message)}advancedperms <on/off>`.")
            return
        
        perms_enabled = await self.bot.db.get_data("guild", "perms_enabled", guild_id = ctx.guild.id)
        if (perms_enabled and action == "on") or (not perms_enabled and action == "off"):
            await ctx.send(f"> Le système de permission est déjà {'activé' if action == 'on' else 'désactivé'}.")
            return
        
        perms_enabled = not perms_enabled
        await self.bot.db.set_data("guild", "perms_enabled", perms_enabled, guild_id = ctx.guild.id)
        await ctx.send(f"> Le système de permission avancé a bien été {'activé' if action == 'on' else 'désactivé'}." + (f"\n> Conseil : Pour en apprendre un peu plus sur ce système, utilisez `{await self.bot.get_prefix(ctx.message)}guideperms`." if action == "on" else ""))

        if perms_enabled:
            permission_manager = PermissionsManager(self.bot)
            await permission_manager.initialize_guild_perms(ctx.guild.id)


    @commands.command(description = "Lire le guide de configuration des permissions", aliases = ["gp", "guideperm"])
    @commands.guild_only()
    async def guideperms(self, ctx):
        bot = self.bot

        class PermGuideMenu(MyViewClass):
            async def on_timeout(self):
                try: await self.message.edit(view = None)
                except: pass

            @discord.ui.select(
                placeholder = "Choisir un guide",
                options = [
                    discord.SelectOption(label = "1. Permissions hiérarchiques et personnalisées [1]", value = "perms_hp"),
                    discord.SelectOption(label = "1. Permissions hiérarchiques et personnalisées [2]", value = "perms_hp2"),
                    discord.SelectOption(label = "2. Configurations", value = "config"),
                    discord.SelectOption(label = "3. Informations supplémentaires", value = "understand_config"),

                ],
                custom_id = "select"
            )
            async def select_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return

                for option in self.get_item("select").options:
                    option.default = (option.value == select.values[0])

                bot_prefix = await bot.get_prefix(ctx.message)

                if select.values[0] == "perms_hp":
                    await interaction.edit(
                        embed = discord.Embed(
                            color = await bot.get_theme(ctx.guild.id),
                            description = textwrap.dedent("""
                                ## 1. Différences théoriques
                                La différence principale entre les permissions hiérarchiques et les permissions personnalisées est que les permissions hiérarchiques sont triées par hiérarchie (comme son nom l'indique). Cela signifie que chaque permission a accès à toutes les commandes des permissions inférieures (en plus des siennes). Tandis que pour les permissions personnalisées, les permissions sont indépendantes, c'est à dire que les utilisateurs pouvant utiliser les commandes d'une certaine permission personnalisée n'auront accès qu'aux commandes de cette permission et aucune autre (sauf si vous leurs donner l'accès à d'autres permissions).

                                En plus de ces différences, vous devrez également noter que les permissions hiérarchiques sont notées par des nombres de 1 à 9 représentant leur niveau dans la hiérarchie des permissions hiérarchiques, plus le nombre est grand, plus il est haut hiérarchiquement.
                            """)
                        ),
                        view = self
                    )

                elif select.values[0] == "perms_hp2":
                    await interaction.edit(
                        embed = discord.Embed(
                            color = await bot.get_theme(ctx.guild.id),
                            description = textwrap.dedent("""
                                # 2. Différences pratiques

                                Pour mieux comprendre les différences entre les permissions hiérarchiques et les permissions personnalisées, prenons un exemple concret :

                                Imaginons que Thomas gère un serveur et souhaite que les @modérateurs aient accès aux commandes de modération complètes, qui sont par défaut associées à la permission hiérarchique de niveau 2. Thomas a déjà configuré les permissions pour que les modérateurs aient accès à cette permission.

                                Cependant, il veut aussi que tous les autres rôles ayant une permission hiérarchique supérieure à celle des @modérateurs puissent également utiliser les commandes de modération. Comment peut-il s'y prendre ?

                                Dans ce cas, utiliser des permissions personnalisées pour chaque rôle serait contre-productif. Cela prendrait non seulement beaucoup de temps à configurer, mais compliquerait aussi la gestion des permissions, surtout avec la limite de 25 commandes par permission personnalisée.

                                La solution pour Thomas est simple : il lui suffit d'attribuer aux rôles supérieurs une permission hiérarchique avec un niveau plus élevé que celui des modérateurs. Par exemple, il peut assigner une permission de niveau 3 ou plus. Grâce à la hiérarchie, ces rôles auront automatiquement accès non seulement à leurs propres commandes, mais aussi à celles des modérateurs (niveau 2), ainsi qu'à toutes les commandes des niveaux inférieurs. Cette approche permet à Thomas de gérer les permissions de manière efficace sans avoir à créer manuellement des permissions pour chaque rôle.
                            """)
                        ),
                        view = self
                    )

                elif select.values[0] == "config":
                    await interaction.edit(
                        embed = discord.Embed(
                            color = await bot.get_theme(ctx.guild.id),
                            description = textwrap.dedent("""
                                ## Configurations par défauts
                                Dans un premier temps, parlons des configurations par défaut.

                                Les permissions hiérarchiques sont par défaut configurées de cette manière :
                                - La **permission public** (tout le monde y a accès) pour les commandes d'informations non sensibles, les petits jeux et quelques petites commandes utilitaires (ex : `+pic`, `+pfc`, `+help`).
                                - La **permission 1** pour les commandes de modération faible (ex : `+warn`, `+clear`).
                                - La **permission 2** pour les commandes de modération complète (ex : `+ban`, `+sanctions`, `+tempmute`).
                                - La **permission 3** pour une gestion assez complète des paramètres et des commandes du bot (ex : `+joins`, `+clearlimit`, `+bringall`).
                                - La **permission owner** pour les commandes haut placées et un avantage hiérarchique par rapport aux autres membres (ex : `+perms`, `+blrank`, `+wl`).
                                - La **permission propriétaire** pour le propriétaire du serveur disposant de commandes réservées au propriétaire, ces commandes sont non transférables (ex : `+owner`, `+delowners`).

                                Pour ce qui est des permissions personnalisées, il n'y a pas de configuration par défaut.
                                C'est à vous de créer vos propres permissions personnalisées selon vos besoins. Les permissions personnalisées sont des permissions indépendantes des autres, c'est-à-dire qu'elles ont leurs propres autorisations (rôles, utilisateurs et permissions de serveur) mais aussi leurs propres commandes.
                                Si un utilisateur dispose d'une permission personnalisée, cet utilisateur aura bien accès aux commandes de cette permission, mais à aucune autre si vous ne lui donnez pas l'accès.

                                ## Comment configurer ?
                                Ça dépend de ce que vous voulez configurer. Si vous voulez configurer vos permissions hiérarchiques, alors utilisez la commande `+perms` pour configurer les autorisations de vos permissions hiérarchiques, `+switch` pour déplacer des commandes de permission hiérarchique à permission hiérarchique et `+helpall` pour voir vos commandes par permission hiérarchique.
                                Si vous voulez configurer vos permissions personnalisées, alors utilisez la commande `+customperms` pour configurer les autorisations et les commandes de vos permissions personnalisées et `+customhelp` pour voir vos commandes par permission personnalisée.
                            """)
                        ),
                        view = self
                    )
                
                elif select.values[0] == "understand_config":
                    await interaction.edit(
                        embed = discord.Embed(
                            color = await bot.get_theme(ctx.guild.id),
                            description = textwrap.dedent(f"""
                                ## Configurations des permissions hiérarchiques
                                1. Pour voir et configurer les autorisations : `{bot_prefix}perms`
                                2. Pour configurer les commandes par permissions : `{bot_prefix}switch`
                                3. Pour voir vos commandes par permission : `{bot_prefix}helpall`

                                - **Les permissions suivantes ont quelques particularitée et ne peuvent pas recevoir d'autorisation spécifique**
                                 - Public (Tous le monde y a accès) 
                                 - Owner (Réservé à ceux possédant la permission owner)
                                 - Propriétaire (Réservé au propriétaire du serveur)

                                - **Les permissions hiérarchiques possèdent chacune des limites de configurations des autorisations**
                                 - 15 rôles maximum (rôles donnants la permission)
                                 - 15 utilisateurs spécifiques maximum (utilisateurs ayant la permission)
                                 - 15 permissions de serveur maximum (vous pouvez définir des permission de serveur, comme par exemple : administrateur)

                                ## Configurations des permissions personnalisées
                                1. Pour créer des permissions, ensuite voir et configurer l'ensemble des autorisations et des commandes : `{bot_prefix}customperms`
                                2. Pour voir vos commandes par permission personnalisée : `{bot_prefix}customhelp`

                                - **Les permissions personnalisées possèdent chacune des limites de configurations des autorisations**
                                 - 25 commandes maximum
                                 - 15 rôles maximum
                                 - 15 utilisateurs spécifiques maximum
                                 - 15 permissions de serveur maximum
                            """)
                        ),
                        view = self
                    )

                else:
                    await interaction.response.send_message("> Cette partie n'a pas encore été rédigée.", ephemeral = True)

        current_date = datetime.now()
        await ctx.send(
            embed = discord.Embed(
                title = "Guide de configuration de vos permissions",
                description = textwrap.dedent(f"""
                {'Bonjour' if current_date.hour > 6 and current_date.hour < 20 else 'Bonsoir'} **{ctx.author.display_name}**, ce guide vous permettra de configurer facilement vos permissions. En suivant celui-ci du début à la fin, vous serez au final capable de :
                
                1. *Voir la différence entre permissions hiérarchiques et personnalisées.*
                2. *Comprendre la vérification des permissions par le bot.*
                3. *Créer ou modifier vos permissions avec aisance.*

                Vous pouvez également vous fier à votre intuition si vous êtes déjà familier avec ce type de configuration. En cas de problème de compréhension, vous pouvez toujours contacter et demander de l'aide à notre support.
                """),
                color = await self.bot.get_theme(ctx.guild.id)
            ),
            view = PermGuideMenu()
        )


    @commands.command(description = "Voir et configurer les autorisations des permissions hiérarchiques", aliases = ["permissions", "perm"])
    @commands.guild_only()
    @commands.check(check_perms_enabled)
    async def perms(self, ctx):
        bot = self.bot

        async def get_main_embed():
            permissions_data = await self.bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = ctx.guild.id)

            perms = {str(k):0 for k in range(12)}
            for name, perm in permissions_data["commands"].items():
                perms[perm] += 1
            perms = [" - **" + custom_names.get(perm, f"Perm{perm}") + "**" + f" ({cmds_count})" for perm, cmds_count in perms.items() if cmds_count != 0]
            embed = discord.Embed(
                title = "Permissions hiérarchiques",
                color = await self.bot.get_theme(ctx.guild.id),
                description = textwrap.dedent(f"""
                    *Vous pouvez voir et modifier vos permsisions via le menu ci-dessous*
                    *Pour voir les commandes par permissions, utilisez la commande `{await self.bot.get_prefix(ctx.message)}helpall`.*

                    - **__Permissions possédants des commandes__**
                """) + '\n'.join(perms)
            )

            return embed

        class ConfigPerms(MyViewClass):
            @discord.ui.select(
                placeholder = "Choisir une permission",
                options = [
                    discord.SelectOption(label = f"Perm{i}", emoji = "🗝", value = str(i)) for i in range(12) if not custom_names.get(str(i), None)
                ]
            )
            async def select_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                choose_permission_view = self
                original_permission = select.values[0]

                async def get_permission_embed():
                    permissions_data = await bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = ctx.guild.id)

                    guildpermissions_translations = await bot.get_translation("permissions", interaction.guild.id)
                    perm_authorzation_data = permissions_data["authorizations"][select.values[0]]
                    perm_commands = [command for command, permission in permissions_data["commands"].items() if permission == select.values[0]]

                    embed = discord.Embed(
                        title = custom_names.get(select.values[0], f"Permission n°{select.values[0]}"),
                        color = await bot.get_theme(ctx.guild.id),
                        description = textwrap.dedent(f"""
                            *Chaque rôle, utilisateur ou permission de serveur doit appartenir à une seule permission hiérarchique. Ainsi, si vous ajoutez un élément déjà présent dans une autre permission hiérarchique, il sera automatiquement retiré de cette dernière.*
                            
                            ### Informations sur la permission
                            *Commandes* : **{len(perm_commands)}**
                            *Rôles* : **{len(perm_authorzation_data['roles'])}/15**
                            *Utilisateur spécifiques* : **{len(perm_authorzation_data['users'])}/15**
                            *Permissions de serveur* : **{len(perm_authorzation_data['guildpermissions'])}/15**
                        """),

                    ).add_field(
                        name = "Rôles autorisés",
                        value = "\n".join([f"<@&{role_id}>" for role_id in perm_authorzation_data["roles"]]) if perm_authorzation_data["roles"] else "*Aucun rôle*"
                    ).add_field(
                        name ="Utilisateurs autorisés",
                        value = "\n".join([f"<@{user_id}>" for user_id in perm_authorzation_data["users"]]) if perm_authorzation_data["users"] else "*Aucun utilisateur*"
                    ).add_field(
                        name = "Permissions autorisés",
                        value = "\n".join([guildpermissions_translations[p] for p in perm_authorzation_data["guildpermissions"]]) if perm_authorzation_data["guildpermissions"] else "*Aucune permission autorisé*"
                    )

                    return embed
                
                class EditPerm(MyViewClass):
                    @discord.ui.select(
                        placeholder = "Modifier le la permission",
                        options = [
                            discord.SelectOption(label = "Ajouter des rôles", emoji = "🎭", value = "add_roles"),
                            discord.SelectOption(label = "Retirer des rôles", emoji = "🎭", value = "remove_roles"),
                            discord.SelectOption(label = "Ajouter des utilisateurs", emoji = "👥", value = "add_users"),
                            discord.SelectOption(label = "Retirer des utilisateurs", emoji = "👥", value = "remove_users"),
                            discord.SelectOption(label = "Gérer les permissions de serveur", emoji = "🗝", value = "manage_guildpermissions"),
                            discord.SelectOption(label = "Supprimer les permissions de serveur", emoji = "🗝", value = "del_guildpermissions")
                        ],
                        custom_id = "edit_perm"
                    )
                    async def select_callback(self, select, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
 
                        permissions_data = await bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = interaction.guild.id)
                        permission_data = permissions_data["authorizations"][original_permission]

                        previous_view = self
                        if select.values[0] == "add_roles":
                            if len(permission_data["roles"]) >= 15:
                                await interaction.response.send_message("> Vous ne pouvez pas ajouter plus de 15 rôles autorisés.", ephemeral = True)
                                return

                            class AddRole(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisir des rôles",
                                    select_type = discord.ComponentType.role_select,
                                    max_values = 15 - len(permission_data["roles"])
                                )
                                async def add_role_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return
                                    
                                    permissions_data = await bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = interaction.guild.id)
                                    permission_data = permissions_data["authorizations"][original_permission]

                                    for role in select.values:
                                        if (role.id in permission_data["roles"]) or (len(permission_data["roles"]) >= 15):
                                            continue
                                        for perm, perm_data in permissions_data["authorizations"].items(): # Faire en sorte à ce que le rôle ne soit nul par ailleurs.
                                            if role.id in perm_data["roles"]:
                                                permissions_data["authorizations"][perm]["roles"].remove(role.id)
                                        permission_data["roles"].append(role.id)

                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await bot.db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                    await interaction.edit(embed = await get_permission_embed(), view = previous_view)

                                @discord.ui.button(label = "Choisissez des rôles", style = discord.ButtonStyle.primary, disabled = True)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_permission_embed(), view = previous_view)

                            await interaction.edit(view = AddRole())

                        if select.values[0] == "remove_roles":
                            if not permission_data["roles"]:
                                await interaction.response.send_message(f"> Il n'y pour le moment aucun rôle à retirer pour la **{'Perm' + original_permission}**.", ephemeral = True)
                                return
                            
                            roles_data = {}
                            guild_roles = await interaction.guild.fetch_roles()
                            guild_roles_ids = [role.id for role in guild_roles]
                            
                            for role_id in permission_data["roles"]:
                                if role_id not in guild_roles_ids:
                                    roles_data[str(role_id)] = "@RôleIntrouvable"
                                    continue
                                roles_data[str(role_id)] = "@" + guild_roles[guild_roles_ids.index(role_id)].name

                            class RemoveRole(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisir des rôles",
                                    max_values = len(roles_data),
                                    options = [
                                        discord.SelectOption(label = role_name, value = role_id, description = f"Identifiant : {role_id}") for role_id, role_name in roles_data.items()
                                    ]
                                )
                                async def remove_role_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    permissions_data = await bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = interaction.guild.id)
                                    permission_data = permissions_data["authorizations"][original_permission]

                                    for role_id in select.values:
                                        if int(role_id) not in permission_data["roles"]:
                                            continue
                                        permission_data["roles"].remove(int(role_id))
                                    
                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await bot.db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id =  interaction.guild.id)
                                    await interaction.edit(embed = await get_permission_embed(), view = previous_view)

                                @discord.ui.button(label = "Choisissez des rôles", disabled = True, style = discord.ButtonStyle.primary)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_permission_embed(), view = previous_view)

                            await interaction.edit(view = RemoveRole())

                        if select.values[0] == "add_users":
                            if len(permission_data["users"]) >= 15:
                                await interaction.response.send_message("> Vous ne pouvez pas ajouter plus de 15 utilisateurs.", ephemeral = True)
                                return
                                                        
                            class AddUsers(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisir un utilisateur",
                                    select_type = discord.ComponentType.user_select,
                                    max_values = 15 - len(permission_data["users"])
                                )
                                async def add_users_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    permissions_data = await bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = interaction.guild.id)
                                    permission_data = permissions_data["authorizations"][original_permission]

                                    for user in select.values:
                                        if (user.id in permission_data["users"]) or (len(permission_data["users"]) >= 15):
                                            continue
                                        for perm, perm_data in permissions_data["authorizations"].items(): # Faire en sorte à ce que l'utilisateur ne soit nul par ailleurs.
                                            if user.id in perm_data["users"]:
                                                permissions_data["authorizations"][perm]["users"].remove(user.id)
                                        permission_data["users"].append(user.id)

                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await bot.db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id =  interaction.guild.id)
                                    await interaction.edit(embed = await get_permission_embed(), view = previous_view)

                                @discord.ui.button(label = "Choisissez des utilisateurs", disabled = True, style = discord.ButtonStyle.primary)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_permission_embed(), view = previous_view)

                            await interaction.edit(view = AddUsers())

                        if select.values[0] == "remove_users":
                            if not permission_data["users"]:
                                await interaction.response.send_message("> Il n'y aucun utilisateur à retirer.", ephemeral = True)
                                return
                            
                            usr = {}
                            for user_id in permission_data["users"]:
                                try:
                                    user = await bot.fetch_user(user_id)
                                    usr[str(user_id)] = user.display_name
                                except:
                                    usr[str(user_id)] = "UtilisateurIntrouvable"

                            class RemoveUsers(MyViewClass):
                                @discord.ui.select(
                                    max_values = len(usr),
                                    placeholder = "Choisir des utilisateurs",
                                    options = [
                                        discord.SelectOption(label = user_name, value = user_id, description = "Identifiant : " + user_id) for user_id, user_name in usr.items()
                                    ]
                                )
                                async def remove_user_select(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return
                                    
                                    permissions_data = await bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = interaction.guild.id)
                                    permission_data = permissions_data["authorizations"][original_permission]
                                    
                                    for user_id in select.values:
                                        if int(user_id) not in permission_data["users"]:
                                            continue
                                        permission_data["users"].remove(int(user_id))

                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await bot.db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                    await interaction.edit(embed = await get_permission_embed(), view = previous_view)

                                @discord.ui.button(label = "Choisissez des utilisateurs", disabled = True, style = discord.ButtonStyle.primary)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_permission_embed(), view = previous_view)
                            
                            await interaction.edit(view = RemoveUsers())

                        if select.values[0] == "manage_guildpermissions":
                            guildpermissions_translations = await bot.get_translation("permissions", interaction.guild.id)
                            
                            class ManageGuildPermissions(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisissez des permissions",
                                    max_values = len(guildpermissions),
                                    options = [
                                        discord.SelectOption(label = guildpermissions_translations[p], value = p) for p in guildpermissions
                                    ]
                                )
                                async def manage_perm_select_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return
                                    
                                    permissions_data = await bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = interaction.guild.id)
                                    
                                    for guildperm in select.values:
                                        for perm, perm_data in permissions_data["authorizations"].items():
                                            if guildperm not in perm_data["guildpermissions"]:
                                                continue
                                            permissions_data["authorizations"][perm]["guildpermissions"].remove(guildperm)
                                    permissions_data["authorizations"][original_permission]["guildpermissions"] = select.values

                                    await bot.db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)

                                    await interaction.edit(embed = await get_permission_embed(), view = previous_view)

                                @discord.ui.button(label = "Choisssez des permissions", style = discord.ButtonStyle.primary, disabled = True)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_permission_embed(), view = previous_view)

                            await interaction.edit(view = ManageGuildPermissions())

                        if select.values[0] == "del_guildpermissions":
                            if not permission_data["guildpermissions"]:
                                await interaction.response.send_message("> Il n'y a pas de permission de serveur à supprimer.", ephemeral = True)
                                return
                            
                            permission_data["guildpermissions"] = []
                            permissions_data["authorizations"][original_permission] = permission_data

                            await bot.db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                            await interaction.edit(embed = await get_permission_embed())

                    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                    async def comeback_button_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        await interaction.edit(view = choose_permission_view, embed = await get_main_embed())

                for option in select.options:
                    option.default = option.value == select.values[0]

                await interaction.edit(embed = await get_permission_embed(), view = EditPerm())

        await ctx.send(embed = await get_main_embed(), view = ConfigPerms())


    @commands.command(description = "Modifier les commandes par permission hiérarchique", aliases = ["change"])
    @commands.guild_only()
    @commands.check(check_perms_enabled)
    async def switch(self, ctx):
        bot = self.bot # Pour pouvoir accéder à l'instance du bot dans les callback des bouttons/select menus
        prefix = ctx.clean_prefix

        # ------------------ Commandes par cogs ({"cog": ["commands", "commands", "commands"]})
        cogs_to_commands = {}
        for cog in bot.cogs:
            cog_instance = bot.get_cog(cog)
            if (not cog_instance.get_commands()) or (getattr(cog_instance, "qualified_name") == "Developer"):
                continue
            cogs_to_commands[getattr(cog_instance, "qualified_name")] = [command.name for command in cog_instance.get_commands()]

        # ------------------ Charger les commandes réservés aux propriéataire (qui ne peuvent pas donc être déplacés)
        with open("cogs/private/data/default_perms.json", encoding = "utf-8") as file:
            data = json.load(file)
            buyer_commands = data["11"]

        # ------------------ Obtenir l'embed qui est affiché au début de la configuration
        async def get_switch_main_embed():
            permissions_data = await self.bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = ctx.guild.id)
            permissions_to_commands = {}
            permissions_commands_text = ""

            for command_name, command_current_permission in permissions_data["commands"].items():
                permissions_to_commands[command_current_permission] = permissions_to_commands.get(command_current_permission, 0) + 1

            for permission_id, permission_commands_count in permissions_to_commands.items():
                permissions_commands_text += "\n"
                permissions_commands_text += f" - **{custom_names.get(permission_id, 'Perm' + permission_id)}** ({permission_commands_count})"

            embed = discord.Embed(
                title = "Choisissez une permission à gérer",
                description = 
                "*Chaque commande doit appartenir à une seule permission hiérarchique. Ainsi, lorsque vous déplacez une commande d'une permission à une autre, elle sera automatiquement retirée de sa permission précédente.*"
                + "\n\n- **__Permissions possédants des commandes__**"
                + permissions_commands_text,
                color = await bot.get_theme(ctx.guild.id)
            )

            return embed

        # ------------------ Obtenir l'embed de permission pour une certaine permission
        async def get_permission_embed(perm : int):
            permissions_data = await self.bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = ctx.guild.id)
            permission_commands = []

            for command_name, permission_number in permissions_data["commands"].items():
                if int(permission_number) == perm:
                    permission_commands.append(command_name)
            permission_commands = [
                f"**`{prefix}{command_name}`**" + (" (*non transférable*)" if command_name in buyer_commands else "")
                for command_name in permission_commands
            ]
            permission_commands = "\n".join(permission_commands)
            
            embed = discord.Embed(
                title = custom_names.get(str(perm), "Permission n°" + str(perm)),
                description = 
                "*Chaque commande doit appartenir à une seule permission hiérarchique. Ainsi, lorsque vous déplacez une commande d'une permission à une autre, elle sera automatiquement retirée de sa permission précédente.*"
                + "\n\n"
                + "**__Commandes__**\n"
                + permission_commands if permission_commands else "*Aucune commande*",
                color = await bot.get_theme(ctx.guild.id)
            )

            return embed
        
        # ------------------ Classe discord.ui.View composé d'un select menu permettant de choisir une permission à modifier
        class ChoosePermission(MyViewClass):
            @discord.ui.select(
                placeholder = "Choisir une permission",
                options = [
                    discord.SelectOption(
                        label = custom_names.get(str(i), "Perm" + str(i)),
                        emoji  = "🗝",
                        value = str(i)
                    ) for i in range(12)
                ]
            )
            async def choose_permission_select_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                choose_permission_view = self # Sauvegarder la classe pour la restaurer plus tards si besoin
                original_permission = select.values[0]

                # ------------------ Classe discord.ui.View composé d'un select menu permettant de modifier les commandes d'une permission et d'un boutton permettant de revenir en arrière
                class EditPermissionCommands(MyViewClass):
                    @discord.ui.select(
                        placeholder = "Modifier la permission",
                        options = [
                            discord.SelectOption(label = "Importer des commandes", value = "import_commands", emoji = "📥"),
                            discord.SelectOption(label = "Importer une permission",  value = "import_perm", emoji = "📬")
                        ]
                    )
                    async def edit_permission_commands_callback(self, select, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        edit_permission_view = self # Sauvegarde du menu de configuration de la permission pour la restaurer plus tards quand l'utilisatreur aura complété son action
                        
                        # ------------------ Importer des commandes ------------------
                        if select.values[0] == "import_commands":
                
                            # Choisir une catégorie
                            class ChooseCategory(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisir une catégorie",
                                    options = [
                                        discord.SelectOption(label = cog_name.replace("_", " "), value = cog_name)
                                        for cog_name, cog_commands in cogs_to_commands.items() if cog_name != "Proprietaire"
                                    ]
                                )
                                async def choose_category_select(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return
                                    
                                    choose_category_view = self
                                    # Choisir une commande
                                    class ChooseCommand(MyViewClass):
                                        @discord.ui.select(
                                            placeholder = "Choisir une commande",
                                            max_values = len(cogs_to_commands[select.values[0]]),
                                            options = [
                                                discord.SelectOption(label = f"{prefix}{command}", value = command)
                                                for command in cogs_to_commands[select.values[0]]
                                            ]
                                        )
                                        async def choose_command_select_callback(self, select, interaction):
                                            if interaction.user != ctx.author:
                                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                                return
                                            
                                            permissions_data = await bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = interaction.guild.id)
                                            if original_permission == "0":
                                                commands_not_added = []
                                                
                                                with open("cogs/private/data/default_perms.json", encoding = "utf-8") as file:
                                                    data = json.load(file)

                                                # Pour des raisons de sécuritée, on empêche l'ajout des commandes par défaut n'étant pas public vers la permission public.
                                                for command_name in select.values:
                                                    if command_name not in data["0"]: commands_not_added.append(command_name)
                                                    else: permissions_data["commands"][command_name] = "0"

                                                if commands_not_added:
                                                    await interaction.response.send_message(
                                                        "Votre permission a été mise à jours, mais pour des raisons de sécurités, les commandes suivantes n'ont pas été transférées vers la permission Public :"
                                                        + "\n"
                                                        + "\n".join([f"`{prefix}{command}`" for command in commands_not_added]),
                                                        ephemeral = True
                                                    )
                                                await bot.db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                                await interaction.edit(view = edit_permission_view, embed = await get_permission_embed(int(original_permission)))
                                                return
                                            
                                            for command_name in select.values:
                                                permissions_data["commands"][command_name] = original_permission

                                            await bot.db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                            await interaction.edit(view = edit_permission_view, embed = await get_permission_embed(int(original_permission)))
                                            

                                        @discord.ui.button(label = "Choisissez des commandes", style = discord.ButtonStyle.primary, disabled = True)
                                        async def callback(self, button, interaction):
                                            pass

                                        @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                        async def comeback_callback(self, button, interaction):
                                            if interaction.user != ctx.author:
                                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                                return

                                            await interaction.edit(embed = await get_permission_embed(int(original_permission)), view = choose_category_view)
                                    
                                    await interaction.edit(view = ChooseCommand())

                                @discord.ui.button(label = "Choisissez une catégorie", style = discord.ButtonStyle.primary, disabled = True)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_permission_embed(int(original_permission)), view = edit_permission_view)
                            
                            await interaction.edit(view = ChooseCategory(timeout = 600))

                        # ------------------ Importer toutes les commandes d'une permission ------------------
                        if select.values[0] == "import_perm":
                            if original_permission == "0":
                                await interaction.response.send_message("> Vous ne pouvez pas importer de permissions vers la permission publique.", ephemeral = True)
                                return
                            
                            class ChoosePermission(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisir une permission",
                                    options = [
                                        discord.SelectOption(label = custom_names.get(str(i), "Perm" + str(i)), value = str(i))
                                        for i in range(11) if str(i) != original_permission
                                    ]
                                )
                                async def choose_permission_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return
                                    
                                    permissions_data = await bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = interaction.guild.id)
                                    for command_name, command_current_permission in permissions_data["commands"].items():
                                        if command_current_permission != select.values[0]:
                                            continue
                                        permissions_data["commands"][command_name] = original_permission

                                    await bot.db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                    await interaction.edit(embed = get_permission_embed(int(original_permission)), view = edit_permission_view)

                                @discord.ui.button(label = "Choisissez une permission", style = discord.ButtonStyle.primary, disabled = True)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return
                                    
                                    await interaction.edit(embed = await get_permission_embed(int(original_permission)), view = edit_permission_view)
                            
                            await interaction.edit(view = ChoosePermission())

                    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                    async def comback_switch_main_button(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        await interaction.edit(embed = await get_switch_main_embed(), view = choose_permission_view)

                await interaction.edit(embed = await get_permission_embed(int(select.values[0])), view = EditPermissionCommands(timeout = 600))          

        await ctx.send(embed = await get_switch_main_embed(), view = ChoosePermission(timeout = 600))


    @commands.command(description = "Voir vos commandes par permissions hiérarchiques")
    @commands.guild_only()
    @commands.check(check_perms_enabled)
    async def helpall(self, ctx):
        perms_manager = PermissionsManager(self.bot)
        paginator_creator = PaginatorCreator()

        prefix = await self.bot.get_prefix(ctx.message)
        descriptions = []

        for index in range(12):
            commands = await perms_manager.get_perm_commands(ctx.guild.id, index)
            if commands:
                descriptions.append(
                    f"*Utilisez des espaces pour séparer vos arguments, mettez les entre guillemets `\"\"` si vos arguments comportent des espaces. "
                    + "Les arguments sous forme `<...>` sont obligatoires, tandis que les arguments sous forme `[...]` sont facultatifs.*\n\n"
                    + "**__" + custom_names.get(str(index), f"Perm{index}") + "__**"
                    + "\n"
                    + "**`"
                    + "`**\n**`".join([f"{prefix}{command}" for command in commands])
                    + "`**"
                )

        paginator = await paginator_creator.create_paginator(
            title = "Commandes par permission",
            data_list = descriptions,
            data_per_page = 1,
            embed_color = await self.bot.get_theme(ctx.guild.id),
            pages_looped = True,
            page_counter = False
        )

        await paginator.send(ctx)
        

    @commands.command(description = "Voir et configurer vos permissions personnalisées", aliases = ["customperm"])
    @commands.guild_only()
    @commands.check(check_perms_enabled)
    async def customperms(self, ctx):
        cogs_to_commands = {}
        for cog in self.bot.cogs:
            cog_instance = self.bot.get_cog(cog)
            if (not cog_instance.get_commands()) or (getattr(cog_instance, "qualified_name") in ["Proprietaire", "Developer"]):
                continue
            cogs_to_commands[getattr(cog_instance, "qualified_name")] = [command.name for command in cog_instance.get_commands()]
    
        async def get_main_embed_customperms():
            perms_custom = await self.bot.db.get_data("guild", "perms_custom", False, True, guild_id = ctx.guild.id)
            perms_custom_name = list(perms_custom["authorizations"].keys())
            embed = discord.Embed(
                title = "Choisissez une permission à modifier",
                description = "*Contrairement aux commandes hiérarchiques, les permissions personnalisées reçoivent des commandes de manière indépendante les unes des autres. Les rôles disposant de certaines permissions personnalisées n'auront accès qu'à ces permissions spécifiques.*"
                + "\n\n"
                + f"- **__Vos permissions personnalisées__ ({len(perms_custom_name)}/25)**"
                + "\n"
                + (" - **" + "**\n - **".join(perms_custom_name) + "**" if perms_custom_name else "*Aucune permission personnalisée*"),
                color = await self.bot.get_theme(ctx.guild.id)
            )

            return embed

        async def get_main_select_options_customperms():
            perms_custom = await self.bot.db.get_data("guild", "perms_custom", False, True, guild_id = ctx.guild.id)
            perms_custom_name = list(perms_custom["authorizations"].keys())

            options = [
                discord.SelectOption(label = name, value = name, emoji = "🔧") for name in perms_custom_name
            ]

            if not options:
                options.append(discord.SelectOption(label = "Aucune permission personnalisée", value = "nope", default = True))

            return options
        
        async def get_custom_permission_embed(permission_name : str):
            permission_manager = PermissionsManager(bot)
            perms_custom = await self.bot.db.get_data("guild", "perms_custom", False, True, guild_id = ctx.guild.id)
            permission_authorizations = perms_custom["authorizations"].get(permission_name, None)
            guildpermissions_translations = await bot.get_translation("permissions", ctx.guild.id)

            assert permission_authorizations
            
            permission_authorizations["roles"] = [str(role_id) for role_id in permission_authorizations["roles"]]
            permission_authorizations["users"] = [str(role_id) for role_id in permission_authorizations["users"]]
            permission_authorizations["guildpermissions"] = [guildpermissions_translations[p] for p in permission_authorizations["guildpermissions"]]

            permission_commands = await permission_manager.get_custom_perm_commands(permission_name, ctx)

            bot_prefix = await bot.get_prefix(ctx.message)
            embed = discord.Embed(
                title = "Permission " + permission_name,
                description = "*Contrairement aux commandes hiérarchiques, les permissions personnalisées reçoivent des commandes de manière indépendante les unes des autres. Les rôles disposant de certaines permissions personnalisées n'auront accès qu'à ces permissions spécifiques.*"
                + "\n"
                + "### Informations sur la permission\n"
                + f"*Commandes :* **{len(permission_commands)}/25**\n"
                + f"*Rôles :* **{len(permission_authorizations['roles'])}/15**\n"
                + f"*Utilisateurs spécifiques :* **{len(permission_authorizations['users'])}/15**\n"
                + f"*Permissions de serveur :* **{len(permission_authorizations['guildpermissions'])}/15**"
                + "\n"
                + "### Comandes associées"
                + "\n"
                + (f"**`{bot_prefix}" + f"`**\n**`{bot_prefix}".join(permission_commands) + "`**" if permission_commands else "*Aucune commande définis*"),
                color = await self.bot.get_theme(ctx.guild.id)
            )

            embed.add_field(name = "Rôles autorisés", value = "<@&" + ">\n<@&".join(permission_authorizations['roles']) + ">" if permission_authorizations['roles'] else "*Aucun rôle autorisé*")
            embed.add_field(name = "Utilisateurs autorisés", value = "<@" + ">\n<@".join(permission_authorizations['users']) + ">" if permission_authorizations['users'] else "*Aucun utilisateur autorisé*")
            embed.add_field(name = "Permissions autorisés", value = "\n".join(permission_authorizations['guildpermissions']) if permission_authorizations['guildpermissions'] else "*Aucune permission autorisée*")
        
            return embed

        options = await get_main_select_options_customperms()
        bot = self.bot # Sauvegarder l'instance du bot pour l'utiliser dans la classe (pour l'accès à la db)
        class ManageCustomPerms(MyViewClass):
            @discord.ui.select(
                placeholder = "Choisissez une permissions",
                options = options,
                custom_id = "choose_custom_perms"
            )
            async def select_callback(self, select, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                if select.values[0] == "nope":
                    await interaction.response.defer()
                    return
                
                perms_custom = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)
                if not perms_custom["authorizations"].get(select.values[0], None):
                    await interaction.response.send_message(f"> La permission personnalisée **{select.values[0]}** n'éxiste plus.", ephemeral = True)
                    return

                manage_custom_perm_view = self
                original_permission = select.values[0]

                class EditCustomPerm(MyViewClass):
                    @discord.ui.select(
                        placeholder = "Modifier le la permission",
                        options = [
                            discord.SelectOption(label = "Ajouter des rôles", emoji = "🎭", value = "add_roles"),
                            discord.SelectOption(label = "Retirer des rôles", emoji = "🎭", value = "remove_roles"),
                            discord.SelectOption(label = "Ajouter des utilisateurs", emoji = "👥", value = "add_users"),
                            discord.SelectOption(label = "Retirer des utilisateurs", emoji = "👥", value = "remove_users"),
                            discord.SelectOption(label = "Gérer les permissions de serveur", emoji = "🗝", value = "manage_guildpermissions"),
                            discord.SelectOption(label = "Supprimer les permissions de serveur", emoji = "🗝", value = "del_guildpermissions"),
                            discord.SelectOption(label = "Ajouter des commandes", emoji = "📥", value = "add_commands"),
                            discord.SelectOption(label = "Retirer des commandes", emoji = "📤", value = "remove_commands")
                        ],
                        custom_id = "edit_perm"
                    )
                    async def select_callback(self, select, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return

                        permissions_data = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)

                        if original_permission not in permissions_data["authorizations"].keys():
                            await interaction.response.send_message(f"> La permission personnalisée **{original_permission}** n'éxiste plus.", ephemeral = True)
                            return

                        permission_data = permissions_data["authorizations"][original_permission]

                        previous_view = self
                        if select.values[0] == "add_roles":
                            if len(permission_data["roles"]) >= 15:
                                await interaction.response.send_message("> Vous ne pouvez pas ajouter plus de 15 rôles autorisés.", ephemeral = True)
                                return
                            
                            class AddRole(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisir des rôles",
                                    select_type = discord.ComponentType.role_select,
                                    max_values = 15 - len(permission_data["roles"])
                                )
                                async def add_role_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return
                                    
                                    permissions_data = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)
                                    permission_data = permissions_data["authorizations"][original_permission]

                                    for role in select.values:
                                        if (role.id in permission_data["roles"]) or (len(permission_data["roles"]) >= 15):
                                            continue
                                        permission_data["roles"].append(role.id)

                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await bot.db.set_data("guild", "perms_custom", json.dumps(permissions_data), guild_id = interaction.guild.id)

                                    await interaction.edit(embed = await get_custom_permission_embed(original_permission), view = previous_view)

                                @discord.ui.button(label = "Choisissez des rôles", style = discord.ButtonStyle.primary, disabled = True)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_custom_permission_embed(original_permission), view = previous_view)

                            await interaction.edit(view = AddRole())

                        if select.values[0] == "remove_roles":
                            if not permission_data["roles"]:
                                await interaction.response.send_message(f"> Il n'y pour le moment aucun rôle à retirer pour la permission {original_permission}", ephemeral = True)
                                return
                                                        
                            roles_data = {}
                            guild_roles = await interaction.guild.fetch_roles()
                            guild_roles_ids = [role.id for role in guild_roles]
                            
                            for role_id in permission_data["roles"]:
                                if role_id not in guild_roles_ids:
                                    roles_data[str(role_id)] = "@RôleIntrouvable"
                                    continue
                                roles_data[str(role_id)] = "@" + guild_roles[guild_roles_ids.index(role_id)].name

                            class RemoveRole(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisir des rôles",
                                    max_values = len(roles_data),
                                    options = [
                                        discord.SelectOption(label = role_name, value = role_id, description = f"Identifiant : {role_id}") for role_id, role_name in roles_data.items()
                                    ]
                                )
                                async def remove_role_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    permissions_data = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)
                                    permission_data = permissions_data["authorizations"][original_permission]

                                    for role_id in select.values:
                                        if int(role_id) not in permission_data["roles"]:
                                            continue
                                        permission_data["roles"].remove(int(role_id))
                                    
                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await bot.db.set_data("guild", "perms_custom", json.dumps(permissions_data), guild_id =  interaction.guild.id)

                                    await interaction.edit(embed = await get_custom_permission_embed(original_permission), view = previous_view)

                                @discord.ui.button(label = "Choisissez des rôles", disabled = True, style = discord.ButtonStyle.primary)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_custom_permission_embed(), view = previous_view)

                            await interaction.edit(view = RemoveRole())

                        if select.values[0] == "add_users":
                            if len(permission_data["users"]) >= 15:
                                await interaction.response.send_message("> Vous ne pouvez pas ajouter plus de 15 utilisateurs.", ephemeral = True)
                                return
                            
                            class AddUsers(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisir un utilisateur",
                                    select_type = discord.ComponentType.user_select,
                                    max_values = 15 - len(permission_data["users"])
                                )
                                async def add_users_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    permissions_data = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)
                                    permission_data = permissions_data["authorizations"][original_permission]

                                    for user in select.values:
                                        if (user.id in permission_data["users"]) or (len(permission_data["users"]) >= 15):
                                            continue
                                        permission_data["users"].append(user.id)

                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await bot.db.set_data("guild", "perms_custom", json.dumps(permissions_data), guild_id =  interaction.guild.id)

                                    await interaction.edit(embed = await get_custom_permission_embed(original_permission), view = previous_view)

                                @discord.ui.button(label = "Choisissez des utilisateurs", disabled = True, style = discord.ButtonStyle.primary)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_custom_permission_embed(), view = previous_view)

                            await interaction.edit(view = AddUsers())

                        if select.values[0] == "remove_users":
                            if not permission_data["users"]:
                                await interaction.response.send_message("> Il n'y aucun utilisateur à retirer.", ephemeral = True)
                                return
                            
                            usr = {}
                            for user_id in permission_data["users"]:
                                try:
                                    user = await bot.fetch_user(user_id)
                                    usr[str(user_id)] = user.display_name
                                except:
                                    usr[str(user_id)] = "UtilisateurIntrouvable"

                            class RemoveUsers(MyViewClass):
                                @discord.ui.select(
                                    max_values = len(usr),
                                    placeholder = "Choisir des utilisateurs",
                                    options = [
                                        discord.SelectOption(label = user_name, value = user_id, description = "Identifiant : " + user_id) for user_id, user_name in usr.items()
                                    ]
                                )
                                async def remove_user_select(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return
                                    
                                    permissions_data = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)
                                    permission_data = permissions_data["authorizations"][original_permission]
                                    
                                    for user_id in select.values:
                                        if int(user_id) not in permission_data["users"]:
                                            continue
                                        permission_data["users"].remove(int(user_id))

                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await bot.db.set_data("guild", "perms_custom", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                    
                                    await interaction.edit(embed = await get_custom_permission_embed(original_permission), view = previous_view)

                                @discord.ui.button(label = "Choisissez des utilisateurs", disabled = True, style = discord.ButtonStyle.primary)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_custom_permission_embed(original_permission), view = previous_view)
                            
                            await interaction.edit(view = RemoveUsers())

                        if select.values[0] == "manage_guildpermissions":
                            guildpermissions_translations = await bot.get_translation("permissions", interaction.guild.id)
                            
                            class ManageGuildPermissions(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisissez des permissions",
                                    max_values = len(guildpermissions),
                                    options = [
                                        discord.SelectOption(label = guildpermissions_translations[p], value = p) for p in guildpermissions
                                    ]
                                )
                                async def manage_perm_select_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return
                                    
                                    permissions_data = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)
                                    permissions_data["authorizations"][original_permission]["guildpermissions"] = select.values

                                    await bot.db.set_data("guild", "perms_custom", json.dumps(permissions_data), guild_id = interaction.guild.id)

                                    await interaction.edit(embed = await get_custom_permission_embed(original_permission), view = previous_view)

                                @discord.ui.button(label = "Choisssez des permissions", style = discord.ButtonStyle.primary, disabled = True)
                                async def callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                                        return

                                    await interaction.edit(embed = await get_custom_permission_embed(original_permission), view = previous_view)
                                
                            await interaction.edit(view = ManageGuildPermissions())

                        if select.values[0] == "del_guildpermissions":
                            if not permission_data["guildpermissions"]:
                                await interaction.response.send_message("> Il n'y a pas de permission de serveur à supprimer.", ephemeral = True)
                                return
                            
                            permissions_data["authorizations"][original_permission]["guildpermissions"] = []

                            await bot.db.set_data("guild", "perms_custom", json.dumps(permissions_data), guild_id = interaction.guild.id)
                            await interaction.edit(embed = await get_custom_permission_embed(original_permission))

                        if select.values[0] == "add_commands":
                            class ChooseCategory(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisir une catégorie",
                                    options = [
                                        discord.SelectOption(label = category.replace("_", " "), value = category) for category in list(cogs_to_commands.keys())
                                    ]
                                )
                                async def choose_category_select_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci")
                                        return
                                    
                                    previous_view_ = self
                                    class ChooseCommand(MyViewClass):
                                        @discord.ui.select(
                                            placeholder = "Choisir une commande",
                                            options = [
                                                discord.SelectOption(label = command, value = command) for command in cogs_to_commands[select.values[0]]
                                            ],
                                            max_values = len(cogs_to_commands[select.values[0]])
                                        )
                                        async def choose_command_select_callback(self, select, interaction):
                                            if interaction.user != ctx.author:
                                                await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci")
                                                return
                                            
                                            permissions_data = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)

                                            for command in select.values:
                                                if (command in list(permissions_data["commands"].keys())) or (len(permissions_data["commands"]) >= 25):
                                                    continue

                                                command_permissions = permissions_data["commands"].get(command, []).copy()
                                                command_permissions.append(original_permission)
                                                permissions_data["commands"][command] = command_permissions

                                            await bot.db.set_data("guild", "perms_custom", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                            await interaction.edit(embed = await get_custom_permission_embed(original_permission), view = previous_view)
                                            
                                        @discord.ui.button(label = "Choisissez une commande", style = discord.ButtonStyle.primary, disabled = True)
                                        async def indication_callback(self, button, interaction):
                                            pass

                                        @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                        async def comback_command_button_callback(self, button, interaction):
                                            if interaction.user != ctx.author:
                                                await interaction.response.send_message(" Vous n'êtes pas autorisés à intéragir avec ceci.")
                                                return
                                            
                                            await interaction.edit(view = previous_view_)

                                    await interaction.edit(view = ChooseCommand())

                                @discord.ui.button(label = "Choisissez une catégorie de commande", style = discord.ButtonStyle.primary, disabled = True)
                                async def choose_command_callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def comeback_callback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci")
                                        return
                                    
                                    await interaction.edit(view = previous_view)

                            await interaction.edit(view = ChooseCategory())

                        if select.values[0] == "remove_commands":
                            permission_manager = PermissionsManager(bot)
                            permission_commands = await permission_manager.get_custom_perm_commands(original_permission, ctx)
                            bot_prefix = await bot.get_prefix(ctx.message)

                            class ChooseCommand(MyViewClass):
                                @discord.ui.select(
                                    placeholder = "Choisir une commande",
                                    max_values = len(permission_commands),
                                    options = [
                                        discord.SelectOption(label = bot_prefix + name, value = name) for name in permission_commands
                                    ]
                                )
                                async def choose_command_select_callback(self, select, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.")
                                        return
                                    
                                    permissions_data = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)
                                    for command in select.values:
                                        command_permissions = permissions_data["commands"].get(command, []).copy()
                                        if original_permission not in command_permissions:
                                            continue
                                        command_permissions.remove(original_permission)
                                        permissions_data["commands"][command] = command_permissions
                                    
                                    await bot.db.set_data("guild", "perms_custom", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                    await interaction.edit(view = previous_view, embed = await get_custom_permission_embed(original_permission))

                                @discord.ui.button(label = "Choisissez une commande", style = discord.ButtonStyle.primary, disabled = True)
                                async def choose_command_indication_callback(self, button, interaction):
                                    pass

                                @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                                async def choose_command_comback(self, button, interaction):
                                    if interaction.user != ctx.author:
                                        await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.")
                                        return
                                    
                                    await interaction.edit(view = previous_view, embed = await get_custom_permission_embed(original_permission))

                            await interaction.edit(view = ChooseCommand())

                    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                    async def comeback_button_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        await interaction.edit(view = manage_custom_perm_view, embed = await get_main_embed_customperms())

                await interaction.edit(embed = await get_custom_permission_embed(original_permission), view = EditCustomPerm())
                
            @discord.ui.button(label = "Ajouter", emoji = "➕", style = discord.ButtonStyle.primary)
            async def add_custom_perm_button_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                await interaction.response.defer()

                def check_message(message):
                    return (message.channel == ctx.channel) and (message.author == ctx.author) and (message.content)

                message = await ctx.send("Quel sera le **nom** de votre permission personnalisée? Envoyez `cancel` pour annuler.")
                try: response = await bot.wait_for("message", check = check_message, timeout = 60)
                except asyncio.TimeoutError:
                    await ctx.send("> Action annulé, 1 minute écoulée.", delete_after = 2)
                    return
                finally: await delete_message(message)
                await delete_message(response)

                if response.content.lower() == "cancel":
                    await ctx.send("> Action annulé.", delete_after = 2)
                    return
                
                # ------------- Checking NAME...
                if len(response.content) > 30:
                    await ctx.send("> Le nom de votre permission personnalisée ne doit pas dépasser 30 caractères.", delete_after = 2)
                    return
                
                # ------------- Checking NAME...
                if ("perm" in response.content.lower()) \
                    or ("owner" in response.content.lower()) \
                    or ("buyer" in response.content.lower()) \
                    or ("public" in response.content.lower()) \
                    or (response.content.isdigit()):
                    await ctx.send(
                        "> Nommage invalide. Merci de respecter ces **règles de nommage** : \n"
                        + "- Votre nom ne doit pas contenir : `perm`, `owner`, `buyer` et `public`\n"
                        + "- Votre nom de noit pas être un nombre",
                        delete_after = 10
                    )
                    return
                # ------------- Checking NAME...
                perms_custom = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)
                if response.content in list(perms_custom["authorizations"].keys()):
                    await ctx.send("> Cette permission personnalisée existe déjà. Merci de choisir un autre nom.", delete_after = 2)
                    return
                
                # ------------- NAME IS OKAY
                permission_manager = PermissionsManager(bot)
                await permission_manager.create_custom_permission(response.content, ctx)
                await ctx.send(f"> Permission **{response.content}** créé avec succès.", delete_after = 2, allowed_mentions = AM.none())

                choose_custom_perm_select = self.get_item("choose_custom_perms")
                choose_custom_perm_select.options = await get_main_select_options_customperms()

                await interaction.message.edit(embed = await get_main_embed_customperms(), view = self)
                
            @discord.ui.button(label = "Retirer", emoji = "➖", style = discord.ButtonStyle.danger)
            async def remove_custom_perm_button_callback(self, button, interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                    return
                
                perms_custom = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)
                if not perms_custom["authorizations"]:
                    await interaction.response.send_message("> Il n'y a aucune permision personnalisée à supprimer.", ephemeral = True)
                    return
                
                perms_custom_names = list(perms_custom["authorizations"].keys())
                previous_view = self

                class ChoosePermToDel(MyViewClass):
                    @discord.ui.select(
                        placeholder = "Choisir une permission",
                        options = [
                            discord.SelectOption(label = name, value = name, emoji = "🔧") for name in perms_custom_names
                        ]
                    )
                    async def choose_perm_to_del_callback(self, select, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        perms_custom = await bot.db.get_data("guild", "perms_custom", False, True, guild_id = interaction.guild.id)
                        if select.values[0] not in perms_custom["authorizations"].keys():
                            await interaction.response.send_message(f"> La permission **{select.values[0]}** n'éxiste plus.", ephemeral = True)
                            return
                        
                        permissions_manager = PermissionsManager(bot)
                        await permissions_manager.delete_custom_permission(select.values[0], ctx)

                        choose_custom_perm_select = previous_view.get_item("choose_custom_perms")
                        choose_custom_perm_select.options = await get_main_select_options_customperms()
    
                        await interaction.edit(embed = await get_main_embed_customperms(), view = previous_view)

                    @discord.ui.button(label = "Choisissez une permission", style = discord.ButtonStyle.primary, disabled = True)
                    async def choose_perm_to_del(self, select, interaction):
                        pass

                    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                    async def back_button_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        choose_custom_perm_select = previous_view.get_item("choose_custom_perms")
                        choose_custom_perm_select.options = await get_main_select_options_customperms()
                        
                        await interaction.edit(
                            view  = previous_view,
                            embed = await get_main_embed_customperms()
                        )

                embed = await get_main_embed_customperms()
                embed.description += "\n\n"
                embed.description += "*Merci de patienter jusqu'à ce que le bouton \"Revenir en arrière\" soit actif avant de choisir une option dans le menu déroulant pour éviter tout problème.*"
                
                await interaction.edit(view = ChoosePermToDel(), embed = embed)

        await ctx.send(embed = await get_main_embed_customperms(), view = ManageCustomPerms(timeout = 600))


    @commands.command(description = "Voir vos commandes par permissions personnalisées")
    @commands.guild_only()
    @commands.check(check_perms_enabled)
    async def customhelp(self, ctx):
        paginator_creator = PaginatorCreator()
        permission_manager = PermissionsManager(self.bot)
        permissions_data = await self.bot.db.get_data("guild", "perms_custom", False, True, guild_id = ctx.guild.id)
        permissions_names = list(permissions_data["authorizations"].keys())

        if not permissions_names:
            await ctx.send("> Il n'y aucune permission personnalisée créée pour le moment.")
            return
        
        paginator_data = []
        bot_prefix = await self.bot.get_prefix(ctx.message)

        for permission_name in permissions_names:
            page_content = ""
            page_content += f"*Utilisez des espaces pour séparer vos arguments, mettez les entre guillemets `\"\"` si vos arguments comportent des espaces. Les arguments sous forme `<...>` sont obligatoires, tandis que les arguments sous forme `[...]` sont facultatifs.*\n\n"
            page_content += f"**__{permission_name}__**\n"

            permission_commands = await permission_manager.get_custom_perm_commands(permission_name, ctx)

            page_content +=  f"**`{bot_prefix}" + f"`**\n**`{bot_prefix}".join(permission_commands) + "`**" if permission_commands else "*Aucune commande associée*"
            paginator_data.append(page_content)

        paginator = await paginator_creator.create_paginator(
            title = "Commandes par permissions personnalisées",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = paginator_data,
            data_per_page = 1,
            pages_looped = True,
            page_counter = False
        )

        if type(paginator) == list: await ctx.send(embed = paginator[0])
        else: await paginator.send(ctx)

    
    @commands.command(description = "Rétablir les permissions par défauts et supprimer toutes les permissions (sauf owner)", aliases = ["resetperm"])
    @commands.check(check_perms_enabled)
    @commands.guild_only()
    async def resetperms(self, ctx):
        permission_manager = PermissionsManager(self.bot)
        await permission_manager.reset_guild_perms(ctx.guild.id)

        await ctx.send("> Vos permissions ont bien étés réinitialisés.")


def setup(bot):
    bot.add_cog(Permissions(bot))