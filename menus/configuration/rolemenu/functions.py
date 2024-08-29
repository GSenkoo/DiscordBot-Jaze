import discord
from utils import Tools
from typing import List


async def get_main_embed(bot, ctx, data = None) -> discord.Embed:
    """
    Fonction permettant d'obtenir l'embed de départ
    """
    if not data:
        data = {"buttons": [], "selectors": []}

    embed = discord.Embed(
        title = "Configuration de boutons/sélecteurs à rôle",
        description = "*Un sélecteur équivaut à 5 boutons, et Discord limite chaque message à 25 boutons. Les rôles requis ou ignorés ne s'appliquent pas aux options d'un sélecteur permettant de choisir plusieurs rôles.*"
        + "\n\n"
        + f"> *Votre nombre de sélecteur :* ***{len(data['selectors'])}***\n"
        + f"> *Votre nombre de bouton :* ***{len(data['buttons'])}***\n",
        color = await bot.get_theme(ctx.guild.id),
        thumbnail = discord.EmbedMedia(url = ctx.guild.icon.url) if ctx.guild.icon else None
    )
    return embed


def get_role_menu_select_options(data) -> List[discord.SelectOption]:
    """
    Fonction permettant d'obtenir une liste des options du sélecteur permettant de choisir un bouton/sélecteur à configurer
    """
    options = []
    
    for selector in data["selectors"]:
        configured = sum([1 for option_data in selector["options_data"] if option_data["role"]])
        options.append(discord.SelectOption(label = f"Sélecteur - {selector['id']}", emoji = "👥", description = f"Rôle(s) défini : {str(configured) + '/' + str(len(selector['options_data'])) if selector['options_data'] else 'Aucun'}", value = "selector_" + selector["id"]))
    
    for button in data["buttons"]:
        options.append(discord.SelectOption(label = f"Bouton - {button['id']}", emoji = "👤", description = "Rôle défini" if button["role"] else "Rôle non défini", value = "button_" + button['id']))

    if not options:
        return [discord.SelectOption(label = "Aucun bouton/sélecteur", default = True, value = "nope")]
    return options


async def get_button_embed(button_data, ctx, bot) -> discord.Embed:
    """
    Fonction permettant d'obtenir l'embed de configuration d'un bouton du rolemenu
    """
    embed = discord.Embed(
        title = f"Bouton - {button_data['id']}",
        color = await bot.get_theme(ctx.guild.id)
    )

    embed.add_field(name = "Texte", value = button_data["label"])
    embed.add_field(name = "Emoji", value = button_data["emoji"] if button_data["emoji"] else "*Aucun emoji*")
    embed.add_field(name = "Couleur", value = button_data["color"].capitalize())
    embed.add_field(name = "Rôle", value = f"<@&{button_data['role']}>" if button_data['role'] else "*Aucun rôle (obligatoire)*")
    embed.add_field(name = "Rôle requis", value = f"<@&{button_data['required_role']}>" if button_data['required_role'] else "*Aucun rôle*")
    embed.add_field(name = "Rôle ignoré", value = f"<@&{button_data['ignored_role']}>" if button_data['ignored_role'] else "*Aucun rôle*")
    
    return embed


async def get_selector_embed(selector_data, ctx, bot) -> discord.Embed:
    """
    Fonction permettant d'obtenir l'embed de configuration d'un sélecteur du rolemenu
    """
    embed = discord.Embed(
        title = f"Sélecteur - {selector_data['id']}",
        color = await bot.get_theme(ctx.guild.id)
    )

    embed.add_field(name = "Texte du sélecteur", value = selector_data["placeholder"])
    embed.add_field(name = f"Choix maximum", value = str(selector_data['max_values']))
    embed.add_field(name = f"Choix minimum", value = str(selector_data['min_values']))    
    embed.add_field(name = f"Nombre d'option{('s' if len(selector_data['options_data']) > 1 else '')}", value = str(len(selector_data['options_data'])))

    return embed


def get_formated_selector_options(options_data) -> List[discord.SelectOption]:
    """
    Fonction permettant d'obtenir une liste des options d'un sélecteur que le configurateur a configuré
    """
    options = []
    for option in options_data:
        options.append(
            discord.SelectOption(
                label = option["label"],
                emoji = option["emoji"],
                description = option["description"],
                value = "selector_option_" + option["label"]
            )
        )
    
    if not options:
        return [discord.SelectOption(label = "Aucune option configurée", value = "nope", default = True)]
    return options


async def get_selector_option_embed(selector_option_data, ctx, bot) -> discord.Embed:
    """
    Fonction permettant d'obtenir l'embed de configuration d'une option d'un sélecteur
    """
    embed = discord.Embed(
        title = f"Option - {selector_option_data['label']}",
        color = await bot.get_theme(ctx.guild.id)
    )

    embed.add_field(name = "Texte", value = selector_option_data["label"])
    embed.add_field(name = "Description", value = selector_option_data["description"] if selector_option_data["description"] else "*Aucune description*")
    embed.add_field(name = "Emoji", value = selector_option_data["emoji"] if selector_option_data["emoji"] else "*Aucun emoji*")
    embed.add_field(name = "Rôle", value = f"<@&{selector_option_data['role']}>" if selector_option_data['role'] else "*Aucun rôle (obligatoire)*")
    embed.add_field(name = "Rôle requis", value = f"<@&{selector_option_data['required_role']}>" if selector_option_data['required_role'] else "*Aucun rôle*")
    embed.add_field(name = "Rôle ignoré", value = f"<@&{selector_option_data['ignored_role']}>" if selector_option_data['ignored_role'] else "*Aucun rôle*")

    return embed


def create_components(data) -> discord.ui.View:
    """Fonction permettant de convertir les données de boutons/sélecteurs en vrai boutons/sélecteurs

    Format du custom_id des roles-buttons :
    - "role_button_1241484256182669402_1265398039066054676_1276176305376722984"
    -              ^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^
    -              Rôle à ajouter      Rôle obligatoire    Rôle interdit

    C'est la même chose pour les options des sélecteurs, mais aulieu de "role_button_" au début, c'est "option_" pour l'option.
    """
    view = discord.ui.View(timeout = None)

    for selector_data in data["selectors"].copy():
        if selector_data["max_values"] > len(selector_data["options_data"]):
            selector_data["max_values"] = len(selector_data["options_data"])

        if selector_data["min_values"] > selector_data["max_values"]:
            selector_data["min_values"] = selector_data["max_values"]

        selector = discord.ui.Select(
            placeholder = selector_data["placeholder"],
            min_values = selector_data["min_values"],
            max_values = selector_data["max_values"],
            custom_id = "selector_roles"
        )

        for option_data in selector_data["options_data"]:
            selector.add_option(
                label = option_data["label"],
                description = option_data["description"],
                emoji = option_data["emoji"],
                value = f"option_{option_data['role']}"
                    + (
                        f"_{option_data['required_role'] if option_data['required_role'] else 0}_{option_data['ignored_role'] if option_data['ignored_role'] else 0}"
                        if selector_data["max_values"] == 1 else "_0_0"
                    )
            )

        view.add_item(selector)

    for button_data in data["buttons"]:
        view.add_item(
            discord.ui.Button(
                label = button_data["label"],
                emoji = button_data["emoji"],
                style = getattr(discord.ButtonStyle, button_data["color"]),
                custom_id = f"role_button"
                    + f"_{button_data['role']}"
                    + f"_{button_data['required_role'] if button_data['required_role'] else 0}"
                    + f"_{button_data['ignored_role'] if button_data['ignored_role'] else 0}"
            )
        )

    return view