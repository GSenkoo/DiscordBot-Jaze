import discord
import textwrap
import json
from datetime import datetime
from discord.ext import commands
from utils.PermissionsManager import PermissionsManager
from utils.Paginator import PaginatorCreator
from utils.Database import Database


class MyViewClass(discord.ui.View):
    async def on_timeout(self):
        if self.to_components != self.message.components:
            return
        if self.message:
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

class Gestion_des_Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(description = "Lire le guide de configuration des permissions.", aliases = ["gp"])
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
                if select.values == "perms_hp2":
                    await interaction.message.edit(
                        embed = discord.Embed(
                            color = await bot.get_theme(ctx.guild.id),
                            description = textwrap.dedent()
                        )
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

    
    @commands.command(description = "Voir et configurer les autorisations des permissions hiérarchiques")
    @commands.guild_only()
    async def perms(self, ctx):
        bot = self.bot

        async def get_main_embed():
            db = Database()
            await db.connect()
            permissions_data = json.loads(await db.get_data("guild", "perms_hierarchic", guild_id = ctx.guild.id))
            await db.disconnect()

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
                    db = Database()
                    await db.connect()
                    permissions_data = json.loads(await db.get_data("guild", "perms_hierarchic", guild_id = ctx.guild.id))
                    await db.disconnect()

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
                            discord.SelectOption(label = "Gérer les permissions", emoji = "🗝", value = "manage_guildpermissions")
                        ],
                        custom_id = "edit_perm"
                    )
                    async def select_callback(self, select, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return

                        db = Database()
                        await db.connect()
                        permissions_data = json.loads(await db.get_data("guild", "perms_hierarchic", guild_id = interaction.guild.id))
                        permission_data = permissions_data["authorizations"][original_permission]
                        await db.disconnect()

                        previous_view = self
                        if select.values[0] == "add_roles":
                            if len(permission_data["roles"]) >= 15:
                                await interaction.response.send_message("> Vous ne pouvez pas ajouter plus de 15 rôles autorisés.", ephemeral = True)
                                return
                            
                            await interaction.response.defer()
                            
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
                                    
                                    db = Database()
                                    await db.connect()

                                    permissions_data = json.loads(await db.get_data("guild", "perms_hierarchic", guild_id = interaction.guild.id))
                                    permission_data = permissions_data["authorizations"][original_permission]

                                    for role in select.values:
                                        if (role.id in permission_data["roles"]) or (len(permission_data["roles"]) >= 15):
                                            continue
                                        for perm, perm_data in permissions_data["authorizations"].items(): # Faire en sorte à ce que le rôle ne soit nul par ailleurs.
                                            if role.id in perm_data["roles"]:
                                                permissions_data["authorizations"][perm]["roles"].remove(role.id)
                                        permission_data["roles"].append(role.id)

                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                    await interaction.response.defer()
                                    await interaction.message.edit(embed = await get_permission_embed(), view = previous_view)

                                    await db.disconnect()


                                @discord.ui.button(label = "Choisissez des rôles à ajouter", row = 1, style = discord.ButtonStyle.primary, disabled = True)
                                async def callback(self, button, interaction):
                                    pass

                            await interaction.message.edit(view = AddRole())

                        if select.values[0] == "remove_roles":
                            if not permission_data["roles"]:
                                await interaction.response.send_message(f"> Il n'y pour le moment aucun rôle à retirer pour la **{'Perm' + original_permission}**.", ephemeral = True)
                                return
                            
                            await interaction.response.defer()
                            
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
                                    
                                    db = Database()
                                    await db.connect()

                                    permissions_data = json.loads(await db.get_data("guild", "perms_hierarchic", guild_id = interaction.guild.id))
                                    permission_data = permissions_data["authorizations"][original_permission]

                                    for role_id in select.values:
                                        if int(role_id) not in permission_data["roles"]:
                                            continue
                                        permission_data["roles"].remove(int(role_id))
                                    
                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id =  interaction.guild.id)
                                    await interaction.response.defer()
                                    await interaction.message.edit(embed = await get_permission_embed(), view = previous_view)
                                    await db.disconnect()

                                @discord.ui.button(label = "Choisissez des rôles à supprimer", disabled = True, style = discord.ButtonStyle.primary)
                                async def callback(self, button, interaction):
                                    pass

                            await interaction.message.edit(view = RemoveRole())

                        if select.values[0] == "add_users":
                            if len(permission_data["users"]) >= 15:
                                await interaction.response.send_message("> Vous ne pouvez pas ajouter plus de 15 utilisateurs.", ephemeral = True)
                                return
                            
                            await interaction.response.defer()
                            
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
                                    
                                    db = Database()
                                    await db.connect()

                                    permissions_data = json.loads(await db.get_data("guild", "perms_hierarchic", guild_id = interaction.guild.id))
                                    permission_data = permissions_data["authorizations"][original_permission]

                                    for user in select.values:
                                        if (user.id in permission_data["users"]) or (len(permission_data["users"]) >= 15):
                                            continue
                                        for perm, perm_data in permissions_data["authorizations"].items(): # Faire en sorte à ce que l'utilisateur ne soit nul par ailleurs.
                                            if user.id in perm_data["users"]:
                                                permissions_data["authorizations"][perm]["users"].remove(user.id)
                                        permission_data["users"].append(user.id)

                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id =  interaction.guild.id)
                                    await interaction.response.defer()
                                    await interaction.message.edit(embed = await get_permission_embed(), view = previous_view)
                                    await db.disconnect()


                                @discord.ui.button(label = "Choisissez des utilisateurs à ajouter", disabled = True, style = discord.ButtonStyle.primary)
                                async def callback(self, button, interaction):
                                    pass

                            await interaction.message.edit(view = AddUsers())

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
                                    
                                    db = Database()
                                    await db.connect()
                                    permissions_data = json.loads(await db.get_data("guild", "perms_hierarchic", guild_id = interaction.guild.id))
                                    permission_data = permissions_data["authorizations"][original_permission]
                                    
                                    for user_id in select.values:
                                        if int(user_id) not in permission_data["users"]:
                                            continue
                                        permission_data["users"].remove(int(user_id))

                                    permissions_data["authorizations"][original_permission] = permission_data
                                    await db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                    await db.disconnect()

                                    await interaction.response.defer()
                                    await interaction.message.edit(embed = await get_permission_embed(), view = previous_view)


                                @discord.ui.button(label = "Choisissez des utilisateurs à retirer", disabled = True, style = discord.ButtonStyle.primary)
                                async def callback(self, button, interaction):
                                    pass
                            
                            await interaction.response.defer()
                            await interaction.message.edit(view = RemoveUsers())

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
                                    
                                    db = Database()
                                    await db.connect()
                                    permissions_data = json.loads(await db.get_data("guild", "perms_hierarchic", guild_id = interaction.guild.id))
                                    
                                    for guildperm in select.values:
                                        for perm, perm_data in permissions_data["authorizations"].items():
                                            if guildperm not in perm_data["guildpermissions"]:
                                                continue
                                            permissions_data["authorizations"][perm]["guildpermissions"].remove(guildperm)
                                    permissions_data["authorizations"][original_permission]["guildpermissions"] = select.values

                                    await db.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                    await db.disconnect()

                                    await interaction.response.defer()
                                    await interaction.message.edit(embed = await get_permission_embed(), view = previous_view)


                                @discord.ui.button(label = "Choisssez les permissions qui seront autorisés", style = discord.ButtonStyle.primary, disabled = True)
                                async def callback(self, button, interaction):
                                    pass
                                
                            await interaction.message.edit(view = ManageGuildPermissions())
                            await interaction.response.defer()

                    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                    async def comeback_button_callback(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        await interaction.response.defer()
                        await interaction.message.edit(view = choose_permission_view, embed = await get_main_embed())

                await interaction.response.defer()
                for option in select.options:
                    option.default = option.value == select.values[0]

                await interaction.message.edit(embed = await get_permission_embed(), view = EditPerm())


        await ctx.send(embed = await get_main_embed(), view = ConfigPerms())


    @commands.command(description = "Modifier les commandes par permission.")
    @commands.guild_only()
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
        with open("gestion/private/data/default_perms.json") as file:
            data = json.load(file)
            buyer_commands = data["11"]

        
        # ------------------ Obtenir l'embed qui est affiché au début de la configuration
        async def get_switch_main_embed():
            database = Database()
            await database.connect()

            permissions_data = json.loads(await database.get_data("guild", "perms_hierarchic", guild_id = ctx.guild.id))
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

            await database.disconnect()
            return embed


        # ------------------ Obtenir l'embed de permission pour une certaine permission
        async def get_permission_embed(perm : int):
            database = Database()
            await database.connect()

            permissions_data = json.loads(await database.get_data("guild", "perms_hierarchic", guild_id = ctx.guild.id))
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

            await database.disconnect()
            return embed

        
        # ------------------ Classe discord.ui.View composé d'un select menu permettant de choisir une permission à modifier
        class ChoosePermission(MyViewClass):
            @discord.ui.select(
                placeholder = "Choisir une permission",
                options = [
                    discord.SelectOption(
                        label = custom_names.get(str(i), "Perm" + str(i)),
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
                        
                        await interaction.response.defer()
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
                                            
                                            database = Database()
                                            await database.connect()
                                            permissions_data = json.loads(await database.get_data("guild", "perms_hierarchic", guild_id = interaction.guild.id))
                                            if original_permission == "0":
                                                commands_not_added = []
                                                
                                                with open("gestion/private/data/default_perms.json") as file:
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
                                                else: await interaction.response.defer()
                                                await database.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                                await interaction.message.edit(view = edit_permission_view, embed = await get_permission_embed(int(original_permission)))
                                                await database.disconnect()
                                                return
                                            
                                            for command_name in select.values:
                                                permissions_data["commands"][command_name] = original_permission

                                            await database.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                            await interaction.response.defer()
                                            await interaction.message.edit(view = edit_permission_view, embed = await get_permission_embed(int(original_permission)))

                                            await database.disconnect()
                                            

                                        @discord.ui.button(label = "Choisissez les commandes à transférer", style = discord.ButtonStyle.primary, disabled = True)
                                        async def callback(self, button, interaction):
                                            pass
                                    
                                    await interaction.response.defer()
                                    await interaction.message.edit(view = ChooseCommand())

                                @discord.ui.button(label = "Choisissez une catégorie de commande", style = discord.ButtonStyle.primary, disabled = True)
                                async def callback(self, button, interaction):
                                    pass

                            await interaction.message.edit(view = ChooseCategory(timeout = 300))

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
                                    
                                    database = Database()
                                    await database.connect()
                                    
                                    permissions_data = json.loads(await database.get_data("guild", "perms_hierarchic", guild_id = interaction.guild.id))
                                    for command_name, command_current_permission in permissions_data["commands"].items():
                                        if command_current_permission != select.values[0]:
                                            continue
                                        permissions_data["commands"][command_name] = original_permission

                                    await database.set_data("guild", "perms_hierarchic", json.dumps(permissions_data), guild_id = interaction.guild.id)
                                    await interaction.response.defer()
                                    await interaction.message.edit(embed = get_permission_embed(int(original_permission)), view = edit_permission_view)
                                    await database.disconnect()

                                @discord.ui.button(label = "Choisissez une permission à importer", style = discord.ButtonStyle.primary, disabled = True)
                                async def callback(self, button, interaction):
                                    pass
                            
                            await interaction.message.edit(view = ChoosePermission())


                    @discord.ui.button(label = "Revenir en arrière", emoji = "↩")
                    async def comback_switch_main_button(self, button, interaction):
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                            return
                        
                        await interaction.response.defer()
                        await interaction.message.edit(embed = await get_switch_main_embed(), view = choose_permission_view)


                await interaction.response.defer()
                await interaction.message.edit(embed = await get_permission_embed(int(select.values[0])), view = EditPermissionCommands(timeout = 300))
                

        await ctx.send(embed = await get_switch_main_embed(), view = ChoosePermission(timeout = 300))




    @commands.command(description = "Voir vos commandes par permissions hiérarchiques")
    @commands.guild_only()
    async def helpall(self, ctx):
        perms_manager = PermissionsManager()
        paginator_creator = PaginatorCreator()

        prefix = await self.bot.get_prefix(ctx.message)
        descriptions = []
        for index in range(12):
            commands = await perms_manager.get_perm_commands(ctx.guild.id, index)
            if commands:
                descriptions.append(
                    f"*Utilisez des espaces pour séparer vos arguments, mettez les entre guillemets `\"\"` si vos arguments comportent des espaces. "
                    + "Les arguments sous forme `<...>` sont obligatoires, tandis que les arguments sous forme `[...]` sont facultatifs.*\n\n"
                    + "**__" + custom_names.get(str(index), f"Perm{index}") + "__**" + "\n"
                    + "**`" + "`**\n**`".join([f"{prefix}{command}" for command in commands]) + "`**"
                )

        paginator = await paginator_creator.create_paginator(
            title = "Commandes par permission",
            data_list = descriptions,
            data_per_page = 1,
            embed_color = await self.bot.get_theme(ctx.guild.id),
            pages_looped = True
        )

        await paginator.send(ctx)
        

    @commands.command(description = "Voir vos permissions personnalisées")
    @commands.guild_only()
    async def customperms(self, ctx):
        ...

    
    

    


def setup(bot):
    bot.add_cog(Gestion_des_Permissions(bot))