import json
from discord.ext import commands


"""
perms_hierarchic format : 
{
    "authorizations": {
        "perm_number1": {
            "roles": [role_id1, role_id2, ... (max : 15)],
            "users": [user_id1, user_id2, ... (max : 15)],
            "guildpermissions": ["ban_members", "mangae_channels", ... (max : 15)]
        },
        "perm_number2": {
            ...
        },
        ...
    }
    "commands": ["command1", "command2", ... (illimités, mais chaques commandes ne sont jamais présente dans une autre permission hiérarchique)],
}

perms_custom format :
{
    "authorizations": {
        "perm_custom_name1": {
            "roles": [role_id1, role_id2, ... (max : 15)],
            "users": [user_id1, user_id2, ... (max : 15)],
            "guildpermissions": ["ban_members", "mangae_channels", ... (max : 15)]
        },
        "perm_custom_name2": {
            ...
        },
        ...
    }
    "commands": {
        "command1": ["permission_name1", "permission_name2"],
        "command2": [...],
        ... (max : 20)
    }

"""


class PermissionsManager:
    def __init__(self, bot):
        self.bot = bot

    async def _inverse_dict_cmds(self, dictionnary : dict) -> dict:
        inversed_dict = {}
        for key, value in dictionnary.items():
            for nk in value:
                inversed_dict[nk] = key
        return inversed_dict


    async def get_default_perms(self) -> dict:
        """
        ```
        {
            "permissions_id1": ["command_name1", "command_name2", ...],
            "permission_id2": ["command_name3", "command_name4", ...],
            ...
        }
        ```
        """
        with open("gestion/private/data/default_perms.json", encoding = "utf-8") as file:
            return json.load(file)


    async def get_default_commands_perm(self) -> dict:
        """
        ```
        {
            "command_name1": "permission_id1",
            "command_name2": "permission_id2",
            ...
        }
        ```
        """
        return await self._inverse_dict_cmds(await self.get_default_perms())


    async def get_allcommands(self) -> list:
        """
        Renvoyer la liste de toutes les commandes actuelles
        ------------------
        ```
        ["command_name1", "command_name2", "command_name3", ...]
        ```
        """
        default_perm_data = await self.get_default_commands_perm()
        return list(default_perm_data.keys())
    

    async def reset_guild_perms(self, guild_id : int) -> None:
        model = {
            "authorizations": {
                str(index) : {
                    "roles": [],
                    "users": [],
                    "guildpermissions": []
                } for index in range(1, 10)
            },
            "commands": await self.get_default_commands_perm()
        }

        model_custom = {
            "authorizations": {},
            "commands": {}
        }

        await self.bot.db.set_data("guild", "perms_hierarchic", json.dumps(model), guild_id = guild_id)
        await self.bot.db.set_data("guild", "perms_custom", json.dumps(model_custom), guild_id = guild_id)


    async def initialize_guild_perms(self, guild_id : int) -> None:
        commands_permission = await self.get_default_commands_perm()
        guild_perm_data = await self.bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = guild_id)
        if not guild_perm_data:
            await self.reset_guild_perms(guild_id)
            return
        guild_perm_data = guild_perm_data
        
        # ---------------- S'assurer que le serveur possède toutes les commandes actuelles dans ses configurations
        for command in await self.get_allcommands():
            if command in guild_perm_data["commands"].keys():
                continue
            guild_perm_data["commands"][command] = commands_permission[command]

        # ---------------- S'assurer qu'il n'y ai pas de commande en trop dans les configurations du serveur
        for command in list(guild_perm_data["commands"].keys()):
            if command in commands_permission.keys():
                continue
            del guild_perm_data["commands"][command]

        await self.bot.db.set_data("guild", "perms_hierarchic", json.dumps(guild_perm_data), guild_id = guild_id)


    async def get_command_perm(self, guild_id : int, command_name : str):
        default_commands_perm = await self.get_default_commands_perm()

        guild_perms_data = await self.bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = guild_id)
        return guild_perms_data["commands"].get(command_name, default_commands_perm[command_name])

    
    async def get_perm_commands(self, guild_id : int, permission_id : int):
        guild_perms_data = await self.bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = guild_id)
        commands = [command for command, perm in guild_perms_data["commands"].items() if perm == str(permission_id)]
        
        return commands

# ------------------------------------------- CHECK -------------------------------------------

    async def can_use_cmd(self, ctx):
        owners = await self.bot.db.get_data("guild", "owners", True, guild_id = ctx.guild.id)

        # Pour les commandes réservé aux développeurs
        developer_cog = self.bot.get_cog("Developer")

        with open("config.json", encoding = "utf-8") as file:
            config_data = json.load(file)
        if ctx.author.id in config_data["developers"]:
            return True
        if ctx.command.name in [command.name for command in developer_cog.get_commands()]:
            return False

        perms_enabled = await self.bot.db.get_data("guild", "perms_enabled", guild_id = ctx.guild.id)
        if not perms_enabled:
            with open("gestion/private/data/commands_guildpermissions.json") as file:
                commands_guildpermissions = json.load(file)

            command_required_permissions = commands_guildpermissions[ctx.command.name]

            if (ctx.author == ctx.guild.owner):
                return True
            if (ctx.author.id in await self.bot.db.get_data("guild", "owners", True, guild_id = ctx.guild.id)) and ("buyer" not in command_permissions):
                return True

            for permission in command_required_permissions:
                if permission in ["owner", "buyer"]:
                    return False
                if not getattr(ctx.author.guild_permissions, permission):
                    return False
            return True


        perms_hierarchic_data = await self.bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = ctx.guild.id)
        try:
            current_command_perm = perms_hierarchic_data["commands"][ctx.command.name]
        except: return # ça veut dire que la clée/commande n'éxiste pas


        # Tous le monde a accès aux commandes publique
        if current_command_perm == "0":
            return True
        

        # Pour le propriétaire du serveur, tout est autorisé.
        if ctx.author == ctx.guild.owner:
            return True
        if (ctx.author.id in owners) and (current_command_perm != "11"):
            return True
        
        # --------------- Check hierarchic perms
        def check_permission(permission_authorization):
            if permission_authorization["roles"]:
                for role in ctx.author.roles:
                    if role.id not in permission_authorization["roles"]:
                        continue
                    return True
            if permission_authorization["users"]:
                if ctx.author.id in permission_authorization["users"]:
                    return True
            if permission_authorization["guildpermissions"]:
                for perm_id in permission_authorization["guildpermissions"]:
                    if not getattr(ctx.author.guild_permissions, perm_id):
                        continue
                    return True
            return False


        for i in range(9, int(current_command_perm)-1, -1):
            if check_permission(perms_hierarchic_data["authorizations"][str(i)]):
                return True
            
        
        # --------------- Check custom perms
        perms_custom_data = await self.bot.db.get_data("guild", "perms_custom", False, True, guild_id = ctx.guild.id)
        command_permissions = perms_custom_data["commands"].get(ctx.command.name, [])

        for permission in command_permissions:
            if check_permission(perms_custom_data["authorizations"][permission]):
                return True

        return False

# ------------------------------------------- CUSTOM PERMS PART -------------------------------------------

    async def create_custom_permission(self, permission_name, ctx):
        perms_custom_data = await self.bot.db.get_data("guild", "perms_custom", False, True, guild_id = ctx.guild.id)

        assert permission_name not in perms_custom_data["authorizations"].keys()

        perms_custom_data["authorizations"][permission_name] = {"roles": [], "users": [], "guildpermissions": []}
        await self.bot.db.set_data("guild", "perms_custom", json.dumps(perms_custom_data), guild_id = ctx.guild.id)


    async def delete_custom_permission(self, permission_name, ctx):
        perms_custom_data = await self.bot.db.get_data("guild", "perms_custom", False, True, guild_id = ctx.guild.id)

        assert permission_name in perms_custom_data["authorizations"].keys()

        # -------------- Supprimer les autorisations de la permission
        del perms_custom_data["authorizations"][permission_name]

        # -------------- Retirer les commandes de la permission
        for name, current_permissions in perms_custom_data["commands"].items():
            if permission_name in current_permissions:
                perms_custom_data["commands"][name].remove(permission_name)

        await self.bot.db.set_data("guild", "perms_custom", json.dumps(perms_custom_data), guild_id = ctx.guild.id)


    async def get_custom_perm_commands(self, permission_name, ctx):
        perms_custom_data = await self.bot.db.get_data("guild", "perms_custom", False, True, guild_id = ctx.guild.id)

        assert permission_name in perms_custom_data["authorizations"].keys()
        
        commands = []
        for command, permissions in perms_custom_data["commands"].items():
            if permission_name in permissions:
                commands.append(command)

        return commands