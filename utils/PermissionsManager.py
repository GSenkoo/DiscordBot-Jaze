"""
MIT License with Attribution Clause

Copyright (c) 2024 GSenkoo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

**Attribution:**
All copies, modifications, or substantial portions of the Software must include
the original author attribution as follows:
"This software includes work by GSenkoo (github)".

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import json
from discord.ext import commands
from utils.Database import Database


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
        with open("gestion/private/data/default_perms.json") as file:
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
        db = Database()
        await db.connect()

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

        await db.set_data("guild", "perms_hierarchic", json.dumps(model), False, guild_id = guild_id)
        await db.set_data("guild", "perms_custom", json.dumps(model_custom), guild_id = guild_id)


    async def initialize_guild_perms(self, guild_id : int) -> None:
        db = Database()
        await db.connect()
        
        commands_permission = await self.get_default_commands_perm()
        guild_perm_data = await db.get_data("guild", "perms_hierarchic", guild_id = guild_id)
        if not guild_perm_data:
            await self.reset_guild_perms(guild_id)
            return
        guild_perm_data = json.loads(guild_perm_data)
        
        # ---------------- S'assurer que le serveur possède toutes les commandes actuelles dans ses configurations
        for command in await self.get_allcommands():
            if command in guild_perm_data["commands"].keys():
                continue
            guild_perm_data["commands"][command] = commands_permission[command]

        # ---------------- S'assurer qu'il n'y ai pas de commande en trop dans les configurations du serveur
        for command in guild_perm_data["commands"].keys():
            if command in commands_permission.keys():
                continue
            del guild_perm_data["commands"][command]

        await db.set_data("guild", "perms_hierarchic", json.dumps(guild_perm_data), False, guild_id = guild_id)


    async def get_command_perm(self, guild_id : int, command_name : str):
        default_commands_perm = await self.get_default_commands_perm()

        db = Database()
        await db.connect()
        guild_perms_data = json.loads(await db.get_data("guild", "perms_hierarchic", guild_id = guild_id))
        await db.close()

        return guild_perms_data["commands"].get(command_name, default_commands_perm[command_name])

    
    async def get_perm_commands(self, guild_id : int, permission_id : int):
        db = Database()
        await db.connect()
        
        guild_perms_data = json.loads(await db.get_data("guild", "perms_hierarchic", guild_id = guild_id))
        commands = [command for command, perm in guild_perms_data["commands"].items() if perm == str(permission_id)]
        
        return commands


    async def can_use_cmd(self, ctx):
        with open("config.json") as file:
            data = json.load(file)

        if ctx.author.id in data["developers"]:
            return True
        return True
        

