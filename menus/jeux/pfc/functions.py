import discord
from datetime import datetime

rules = {
    "pierre": "ciseaux",
    "papier": "pierre",
    "ciseaux": "papier"
}

emojis = {
    "pierre": "🪨",
    "papier": "📄",
    "ciseaux": "✂️"
}

async def get_pfc_embed(ctx, bot, member, author_pts, oponent_pts, current_player, move = None, oponent_move = None) -> discord.Embed:
    if (author_pts == 3) or (oponent_pts == 3):
        return discord.Embed(
            title = "Partie pfc",
            description = 
            ("*Bien joué. Vous avez gagné cette partie.*" if author_pts == 3 else "*Dommage. Vous avez perdu cette partie.*")
            if not member else
            (f"*Victoire attribuée à {ctx.author.mention}. Bien joué.*" if author_pts == 3 else f"*Victoire attribuée à {member.mention}. Bien joué.*"),
            color = await bot.get_theme(ctx.guild.id)
        )
    
    embed = discord.Embed(
        title = "Partie pfc",
        color = await bot.get_theme(ctx.guild.id),
        description = f"*Utilisez le menu déroulant pour choisir une option.*\n"
        + f"*Expiration de la partie <t:{round(datetime.now().timestamp()) + 30}:R>.*\n"
        + f"*{current_player.display_name} est entrain de faire son choix...*",
    )

    if move:
        if rules[move] == oponent_move: text_winner = f"(Gagnant : {ctx.author.mention})"
        elif move == oponent_move: text_winner = f"(Égalitée)"
        else: text_winner = f"(Gagnant : {ctx.guild.me if not member else member.mention})"

        embed.add_field(name = "Choix", value = emojis[move] + " vs " + emojis[oponent_move] + f" {text_winner}", inline = False)

    embed.add_field(name = ctx.author.display_name, value = f"{author_pts} pts")
    embed.add_field(name = ctx.guild.me.display_name if not member else member.display_name, value = f"{oponent_pts} pts")

    return embed