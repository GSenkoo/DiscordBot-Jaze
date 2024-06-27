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


import discord
import json
from discord.ext import commands
from utils.Paginator import PaginatorCreator
from utils.Database import Database

async def get_theme(guild_id : int):
    database = Database()
    try:
        await database.connect()
        theme = await database.get_data(table = "guild", column = "theme", guild_id = guild_id)
    finally: await database.disconnect()
    return int(theme)


class CustomHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return f"**`{self.context.clean_prefix}{command.name}{' ' if command.signature else ''}{command.signature}`**\n{command.description}"
    
    async def send_bot_help(self, mapping):
        titles, descriptions = [], []
        for cog, commands in mapping.items():
            if not getattr(cog, "qualified_name", None) or getattr(cog, "qualified_name", None) == "Developer":
                continue
            
            commands_signatures = [self.get_command_signature(command) for command in commands]
            if not commands_signatures:
                continue

            titles.append(getattr(cog, "qualified_name"))
            descriptions.append(
                f"*Utilisez des espaces pour séparer vos arguments, mettez les entre guillemets `\"\"` si vos arguments comportent des espaces. "
                + "Les arguments sous forme `<...>` sont obligatoires, tandis que les arguments sous forme `[...]` sont facultatifs.*\n\n"
                + "\n\n".join(commands_signatures)
            )

        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = titles,
            embed_color = await get_theme(self.context.guild.id),
            data_list = descriptions,
            data_per_page = 1,
            pages_looped = True,
            page_counter = False,
            without_button_if_onepage = False,
        )

        await paginator.send(self.context)


    def command_not_found(self, string):
        mapping, propositions = self.get_bot_mapping(), []
        
        def has_aliases_comparison(cmd, query):
            if query in str(cmd):
                return True
            for alias in cmd.aliases:
                if (alias in query) or (query in alias):
                    return True
            return False

        for cog, commands in mapping.items():
            for command in commands:
                if (str(command) in string) or (string in str(command)) or has_aliases_comparison(command, string):
                    propositions.append(self.context.clean_prefix + f"help {command}")

        return f"Aucune commande appelée \"{string if len(string) <= 30 else string[:30] + '...'}\" n'éxiste" + (", voici quelques recommendations : \n`" + "`\n`".join(propositions) + "`" if propositions else ".")
    

    async def send_command_help(self, command):
        embed = discord.Embed(
            title = f"Commande {command}",
            color = await get_theme(self.context.guild.id)
        ).add_field(
            name = "Description",
            value = f"{command.description}",
            inline = False
        ).add_field(
            name = "Utilisation",
            value = f"`{self.context.clean_prefix}{command.name}{' ' if command.signature else ''}{command.signature}`"
        )

        if command.aliases:
            embed.add_field(
                name = "Alias",
                value = f"`{'`, `'.join(command.aliases)}`" if command.aliases else "*Aucun alias*"
            )
        if command.help:
            embed.add_field(
                name = "Aide",
                value = f"{command.help}"
            )


        channel = self.get_destination()
        await channel.send(embed = embed)


    async def send_cog_help(self, cog):
        cog_name = getattr(cog, "qualified_name", None)
        cog_commands = await self.filter_commands(cog.get_commands())

        with open("config.json") as file:
            data = json.load(file)
            developers = data["developers"]

        if (not cog_name) or (not cog_commands) or (cog_name == "Developer" and self.context.author.id not in developers):
            return
        
        cog_commands_signatures = [self.get_command_signature(command) for command in cog_commands]
        embed = discord.Embed(
            title = cog_name,
            description = f"*Utilisez des espaces pour séparer vos arguments, mettez les entre guillemets `\"\"` si vos arguments comportent des espaces. "
                + "Les arguments sous forme `<...>` sont obligatoires, tandis que les arguments sous forme `[...]` sont facultatifs.*\n\n"
                + "\n\n".join(cog_commands_signatures),
            color = await get_theme(self.context.guild.id)
        )

        await self.get_destination().send(embed = embed)