import discord
import json
from typing import List


def get_counter_choices(counters_data) -> List[discord.SelectOption]:
    """
    Obtenir le sélecteur du menu permettant de choisir un compteur à modifier
    """
    choices = []
    for counter in counters_data:
        choices.append(discord.SelectOption(label = f"Compteur {'ON' if counter['enabled'] else 'OFF'} - {counter['name']}", value = "counter_" + counter["name"], emoji = "🔢"))
    if choices:
        return choices
    return [discord.SelectOption(label = "Aucun compteur configuré", value = "nope", default = True)]


async def get_counters_main_embed(bot, ctx, counters_data) -> discord.Embed:
    """
    Obtenir l'embed de configuration principal des compteurs
    """
    embed = discord.Embed(
        title = "Configuration des compteurs",
        description = f"*Vous avez actuellement un total de **{len(counters_data)}** compteur{'s' if len(counters_data) > 1 else ''} sur 10.*\nUtilisez le menu déroulant pour les configurer.",
        color = await bot.get_theme(ctx.guild.id)
    )

    return embed


async def get_counter_embed(ctx, bot, counter_data) -> discord.Embed:
    """
    Obtenir l'embed d'un certains compteur
    """
    embed = discord.Embed(
        title = "Configuration de compteurs",
        description = f"*Vous pouvez voir les variables utilisable sur ce compteur via `+variables` (variables de serveur).*",
        color = await bot.get_theme(ctx.guild.id)
    )

    embed.add_field(name = "Statut", value = "Activé" if counter_data["enabled"] else "Désactivé")
    embed.add_field(name = "Texte", value = counter_data["text"] if counter_data["text"] else "*Aucun texte défini*")
    embed.add_field(name = "Salon", value = f"<#{counter_data['channel']}>" if counter_data['channel'] else "*Aucun salon défini*")
    embed.add_field(name = "Fréquence des mises à jours", value = counter_data["update_frequency"].replace("m", " minutes").replace("h", " heure"))

    return embed


async def get_data(bot, ctx) -> List[dict]:
    results = await bot.db.execute(f"SELECT * FROM counter WHERE guild_id = {ctx.guild.id}", fetch = True)
    if not results:
        return []
    
    counter_table_columns = await bot.db.get_table_columns("counter")
    counters_data = []

    for counter_data in results:
        counters_data.append(dict(zip(counter_table_columns, counter_data)))
    return counters_data


async def save_data(bot, ctx, counters_data) -> None:
    await bot.db.execute(f"DELETE FROM counter WHERE guild_id = {ctx.guild.id}")
    for counter_data in counters_data:
        await bot.db.execute("INSERT INTO counter (guild_id, name, enabled, text, channel, update_frequency) VALUES (%s, %s, %s, %s, %s, %s)", (ctx.guild.id, counter_data["name"], counter_data["enabled"], counter_data["text"], counter_data["channel"], counter_data["update_frequency"]))