import discord
import json
from discord.ext import commands
from utils.Paginator import PaginatorCreator


class CustomHelp(commands.HelpCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_command_signature(self, command):
        return f"**`{self.context.clean_prefix}{command.name}{' ' if command.signature else ''}{command.signature}`**\n{command.description}"
    
    async def send_bot_help(self, mapping):
        titles, descriptions, select = [], [], []
        help_type = await self.context.bot.db.get_data("guild", "help_type", guild_id = self.context.guild.id)

        for cog, commands in mapping.items():
            if not getattr(cog, "qualified_name", None) or getattr(cog, "qualified_name", None) == "Developer":
                continue
            
            commands_signatures = [self.get_command_signature(command) for command in commands]
            if not commands_signatures:
                continue

            titles.append(getattr(cog, "qualified_name").replace("_", " "))
            descriptions.append(
                f"*Utilisez des espaces pour séparer vos arguments, mettez les entre guillemets `\"\"` si vos arguments comportent des espaces. "
                + f"Les arguments sous forme `<...>` sont obligatoires, tandis que les arguments sous forme `[...]` sont facultatifs. Utilisez `{self.context.clean_prefix}help [command/category]` pour vous aider.*\n\n"
                + "\n\n".join(commands_signatures)
            )

        if help_type == "s":
            class HelpView(discord.ui.View):
                def __init__(self, context):
                    super().__init__()
                    self.context = context

                async def on_timeout(self) -> None:
                    try: await self.message.edit(view = None)
                    except: pass

                @discord.ui.select(
                    placeholder = "Choisir une catégorie",
                    options = [discord.SelectOption(label = title, value = str(index)) for index, title in enumerate(titles)],
                    custom_id = "select"
                )
                async def select_callback(self, select, interaction):
                    if interaction.user != self.context.author:
                        await interaction.response.send_message("Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
                        return
                    
                    for option in self.get_item("select").options:
                        option.default = (option.value == select.values[0])
                    
                    await interaction.response.defer()
                    await interaction.message.edit(
                        embed = discord.Embed(
                            title = titles[int(select.values[0])],
                            description = descriptions[int(select.values[0])],
                            color = await self.context.bot.get_theme(self.context.guild.id)
                        ),
                        view = self
                    )

            await self.context.send(
                embed = discord.Embed(
                    title = titles[0],
                    description = descriptions[0],
                    color = await self.context.bot.get_theme(self.context.guild.id)
                ),
                view = HelpView(context = self.context)
            )

        else:
            paginator_creator = PaginatorCreator()
            paginator = await paginator_creator.create_paginator(
                title = titles,
                embed_color = await self.context.bot.get_theme(self.context.guild.id),
                data_list = descriptions,
                data_per_page = 1,
                pages_looped = True,
                without_button_if_onepage = False,
            )

            await paginator.send(self.context)

    def subcommand_not_found(self, command, string):
        return f"> Aucune commande appelée \"{string if len(string) <= 30 else string[:30] + '...'}\" n'éxiste."


    
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
            if not commands:
                continue
            
            cog_name = getattr(cog, "qualified_name", None)

            if cog_name:
                if string == cog_name.replace("_", " "):
                    return
                if (string in cog_name.replace("_", " ") or (cog_name.replace("_", " ") in string)) and cog_name != "Developer":
                    propositions.append(self.context.clean_prefix + f"help {cog_name.replace('_', ' ')}")

            for command in commands:
                if str(command).startswith("on "):
                    continue
                if (str(command) in string) or (string in str(command)) or has_aliases_comparison(command, string):
                    propositions.append(self.context.clean_prefix + f"help {command}")

        return f"> Aucune commande appelée \"{string if len(string) <= 30 else string[:30] + '...'}\" n'éxiste" + (", voici quelques recommendations : \n`" + "`\n`".join(propositions) + "`" if propositions else ".")
    

    async def send_command_help(self, command):
        embed = discord.Embed(
            title = f"Commande {command}",
            color = await self.context.bot.get_theme(self.context.guild.id)
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
        if command.cog_name:
            embed.add_field(
                name = "Catégorie",
                value = f"`{command.cog_name}`"
            )     

        if command.help:
            embed.add_field(
                name = "Aide",
                value = f"{command.help}"
            )

        advanced_perms_enabled = await self.context.bot.db.get_data("guild", "perms_enabled", guild_id = self.context.guild.id)
        if not advanced_perms_enabled:
            with open("gestion/private/data/permissions_translations.json", encoding = "utf-8") as file:
                perms_translation = json.load(file)
            with open("gestion/private/data/commands_guildpermissions.json", encoding = "utf-8") as file:
                commands_guildpermissions = json.load(file)
            
            command_allowed_perms = [perms_translation[perm] for perm in commands_guildpermissions[str(command)]]
            embed.add_field(
                name = "Permissions nécessaire",
                value = "`" + f"`, `".join(command_allowed_perms) + "`" if command_allowed_perms else "*Aucune. Utilisable par tous.*"
            )
        else:
            perms_hierarchic_data = await self.context.bot.db.get_data("guild", "perms_hierarchic", False, True, guild_id = self.context.guild.id)
            perms_custom_data = await self.context.bot.db.get_data("guild", "perms_custom", False, True, guild_id = self.context.guild.id)
            
            embed.add_field(
                name = "Permission hiérarchique",
                value = "`Perm " +  str(perms_hierarchic_data["commands"][str(command)]).replace("0", "Public").replace("10", "Owner").replace("11", "Propriétaire") + "`"
            )

            command_custom_perms_allowed = perms_custom_data["commands"].get(str(command))
            embed.add_field(
                name = "Permissions personnalisées",
                value = "`" + f"`, `".join(command_custom_perms_allowed) + "`" if command_custom_perms_allowed else "*Aucune*"
            )


        channel = self.get_destination()
        await channel.send(embed = embed)


    async def send_cog_help(self, cog):
        cog_name = getattr(cog, "qualified_name", None)
        cog_commands = await self.filter_commands(cog.get_commands())

        with open("config.json", encoding = "utf-8") as file:
            data = json.load(file)
            developers = data["developers"]

        if (not cog_name) or (not cog_commands) or (cog_name == "Developer" and self.context.author.id not in developers):
            return

        cog_commands_signatures = [self.get_command_signature(command) for command in cog_commands]
        embed = discord.Embed(
            title = cog_name,
            description = f"*Utilisez des espaces pour séparer vos arguments, mettez les entre guillemets `\"\"` si vos arguments comportent des espaces. "
                + f"Les arguments sous forme `<...>` sont obligatoires, tandis que les arguments sous forme `[...]` sont facultatifs. Utilisez `{self.context.clean_prefix}help [command/category]` pour vous aider.*\n\n"
                + "\n\n".join(cog_commands_signatures),
            color = await self.context.bot.get_theme(self.context.guild.id)
        )

        await self.get_destination().send(embed = embed)