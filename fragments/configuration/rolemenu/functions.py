import discord
from typing import List


async def get_main_embed(bot, ctx, data = None) -> discord.Embed:
    """
    Fonction permettant d'obtenir l'embed de départ
    """
    if not data:
        data = {"buttons": [], "selectors": []}

    embed = discord.Embed(
        title = "Configuration de boutons/sélécteurs à rôle",
        description = "*Un sélécteur compte comme 5 boutons. Discord vous limites à maximum 25 boutons par message.*"
        + "\n\n"
        + f"> *Votre nombre de bouton :* ***{len(data['buttons'])}***\n"
        + f"> *Votre nombre de sélécteur :* ***{len(data['selectors'])}***",
        color = await bot.get_theme(ctx.guild.id),
        thumbnail = discord.EmbedMedia(url = ctx.guild.icon.url) if ctx.guild.icon else None
    )
    return embed


def get_role_menu_select_options(data) -> List[discord.SelectOption]:
    """
    Fonction permettant d'obtenir une liste des options du sélécteur permettant de choisir un bouton/sélécteur à configurer
    """
    options = []
    
    for selector in data["selectors"]:
        configured = sum([1 for option_data in selector["options_data"] if option_data["role"]])
        options.append(discord.SelectOption(label = f"Sélécteur - {selector['id']}", emoji = "👥", description = f"Rôle(s) défini : {str(configured) + '/' + str(len(selector['options_data'])) if selector['options_data'] else 'Aucun'}", value = "selector_" + selector["id"]))
    
    for button in data["buttons"]:
        options.append(discord.SelectOption(label = f"Bouton - {button['id']}", emoji = "👤", description = "Rôle défini" if button["role"] else "Rôle non défini", value = "button_" + button['id']))

    if not options:
        return [discord.SelectOption(label = "Aucun bouton/sélécteur", default = True, value = "nope")]
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
    Fonction permettant d'obtenir l'embed de configuration d'un sélécteur du rolemenu
    """
    embed = discord.Embed(
        title = f"Sélécteur - {selector_data['id']}",
        color = await bot.get_theme(ctx.guild.id)
    )

    embed.add_field(name = "Texte du sélécteur", value = selector_data["placeholder"])
    embed.add_field(name = f"Rôle{('s' if selector_data['min_values'] > 1 else '')} minimum", value = str(selector_data['min_values']))
    embed.add_field(name = f"Rôle{('s' if selector_data['max_values'] > 1 else '')} maximum", value = str(selector_data['max_values']))
    embed.add_field(name = f"Nombre d'option{('s' if len(selector_data['options_data']) > 1 else '')}", value = str(len(selector_data['options_data'])))

    return embed


def get_formated_selector_options(options_data) -> List[discord.SelectOption]:
    """
    Fonction permettant d'obtenir une liste des options d'un sélécteur que le configurateur a configuré
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