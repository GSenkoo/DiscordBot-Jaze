import json
import discord
from discord.ext import commands
from typing import Union
from datetime import timedelta, datetime
from utils.Database import Database


class Tools:
    async def add_sanction(
        self,
        sanction_type : str,
        ctx : commands.Context,
        member : Union[discord.Member, discord.User],
        reason : Union[str, None],
        time : timedelta = None
    ) -> None:
        """
        Cette fonction ajoutera une sanctions à la liste des sanctions de l'utilisateur concerné.
        Un dm pour informer l'utilisateur concerné lui sera aussi envoyé (si possible).

        Paramètres
        ------------------------------------------
        sanction_type `str`
            Le type de sanction (derank, ban, kick, warn ou tempmute)
        ctx `discord.ext.commands.Context`
            Le contexte de la sanction
        member `Union[discord.Member, discord.User]`
            L'utilisateur qui subit la sanction
        reason `Union[str, None]`
            La raison de la sanction
        time `str` default `None`
            Obligatoire uniquement si le type de sanction est un tempmute, vous devrez ici indiquer la durée du tempmute
        """
        if member.bot:
            return
        
        assert sanction_type in ["derank", "ban", "kick", "warn", "tempmute"]
        assert not (sanction_type == "tempmute" and not time)
        
        database = Database()
        await database.connect()

        user_sanctions = await database.get_data("member", "sanctions", guild_id = ctx.guild.id, user_id = member.id)
        if not user_sanctions:
            user_sanctions = "[]"
        user_sanctions = json.loads(user_sanctions)
        
        attrs = ["days", "hours", "minutes", "seconds"]
        converter = {
            "days": "jour(s)",
            "hours": "heure(s)",
            "minutes": "minute(s)",
            "seconds": "seconde(s)"
        }

        for attr in attrs:
            if getattr(time, attr, None):
                time = str(getattr(time, attr)) + " " + converter[attr]
                break

        message = \
            f"> Vous avez été {sanction_type}" \
            + f" du serveur **{ctx.guild.name}**" \
            + (f" `{time}` " if sanction_type == "tempmute" else " ") \
            + f"par **{ctx.author.display_name}**" \
            + ("." if not reason else f" pour `" + reason.replace("`", "'") + "`.")

        try: await member.send(message)
        except: pass

        user_sanctions.append({
            "type": sanction_type,
            "moderator": ctx.author.id,
            "timestamp": round(datetime.now().timestamp()),
            "reason": (reason if len(reason) <= 500 else reason[:497] + "...") if reason else None
        })

        await database.set_data("member", "sanctions", json.dumps(user_sanctions), guild_id = ctx.guild.id, user_id = member.id)
        await database.disconnect()


    async def find_duration(
        self,
        duration : str
    ) -> Union[timedelta, None]:
        """
        Renvoyer un temps au format `datetime.timedelta` selon une temps donné dans une chaîne de caractère.

        Paramètres
        ------------------------------------------
        duration `str`
            La durée en format str

        Exemples de format valide :
        ------------------------------------------
        `1jours`, `3days`, `7h`, `8secondes`, `9minutes`, `1min`
        """
        #
        duration_test = duration.replace("days", "").replace("day", "").replace("jours", "").replace("jour", "").replace("d", "").replace("j", "")
        if duration_test.isdigit() and int(duration_test): #  je rajoute int(duration_test) pour s'assurer que le nombre n'est pas une valeure nulle (0)
            return timedelta(days = int(duration_test))
        
        duration_test = duration.replace("hours", "").replace("hour", "").replace("heures", "").replace("heure", "").replace("h", "")
        if duration_test.isdigit() and int(duration_test):
            return timedelta(hours = int(duration_test))
        
        duration_test = duration.replace("minutes", "").replace("minute", "").replace("min", "").replace("m", "")
        if duration_test.isdigit() and int(duration_test):
            return timedelta(minutes = int(duration_test))
        
        duration_test = duration.replace("secondes", "").replace("seconde", "").replace("seconds", "").replace("second", "").replace("sec", "").replace("s", "")
        if duration_test.isdigit() and int(duration_test):
            return timedelta(seconds = int(duration_test))
        
        return None