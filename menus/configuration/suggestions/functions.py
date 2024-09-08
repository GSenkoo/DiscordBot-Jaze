import discord
import json


async def get_suggestion_settings_embed(bot, ctx, data : dict) -> discord.Embed:
    embed = discord.Embed(
        title = "Paramètres de suggestions",
        color = await bot.get_theme(ctx.guild.id),
        description = "*Si aucun salon de confirmation n'est donné, alors les suggestions ne seront pas vérifiés.* "
        + "*Les utilisateurs avec la permission owner et le propriétaire peuvent confirmer les suggestions sans avoir à avoir un rôle modérateur.*"
    )

    embed.add_field(name = "Statut", value = "Activé" if data["enabled"] else "Désactivé")
    embed.add_field(name = "Salon de suggestion", value = f"<#{data['channel']}>" if data['channel'] else "*Aucun salon*")
    embed.add_field(name = "Salon de confirmation", value = f"<#{data['confirm_channel']}>" if data['confirm_channel'] else "*Aucun salon*")
    embed.add_field(name = "Emoji \"pour\"", value = data["for_emoji"])
    embed.add_field(name = "Emoji \"contre\"", value = data["against_emoji"])
    embed.add_field(name = "Rôles modérateurs", value = "<@&" + ">\n<@&".join([str(role_id) for role_id in data['moderator_roles']]) + ">" if data['moderator_roles'] else "*Aucun rôles modérateurs*")

    return embed


async def get_suggestions_data(bot, ctx):
    suggestions_found = await bot.db.execute(f"SELECT * FROM suggestions WHERE guild_id = {ctx.guild.id}", fetch = True)

    if not suggestions_found:
        suggestion_data = {
            "channel": ctx.channel.id, "confirm_channel": None,
            "moderator_roles": [],
            "enabled": False, "for_emoji": "✅", "against_emoji": "❌"
        }
    else:
        suggesiton_columns = await bot.db.get_table_columns("suggestions")
        suggestion_current_data = dict(zip(suggesiton_columns, suggestions_found[0]))
        suggestion_data = {
            "channel": suggestion_current_data["channel"], "confirm_channel": suggestion_current_data["confirm_channel"],
            "moderator_roles": json.loads(suggestion_current_data["moderator_roles"]), "enabled": suggestion_current_data["enabled"],
            "for_emoji": suggestion_current_data["for_emoji"] if suggestion_current_data["for_emoji"] else "✅",
            "against_emoji": suggestion_current_data["against_emoji"] if suggestion_current_data["against_emoji"] else "❌"
        }

    return suggestion_data