import json
import discord
import emoji
from discord.ext import commands
from typing import Union
from datetime import timedelta, datetime


class Tools:
    def __init__(self, bot):
        self.bot = bot

    async def add_sanction(
        self,
        sanction_type : str,
        ctx : commands.Context,
        member : Union[discord.Member, discord.User],
        reason : Union[str, None],
        time : str = None
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
        
        assert sanction_type in ["derank", "ban", "kick", "warn", "tempmute", "blrank", "blvoc"]
        assert not (sanction_type == "tempmute" and not time)
    

        user_sanctions = await self.bot.db.get_data("member", "sanctions", guild_id = ctx.guild.id, user_id = member.id)
        if not user_sanctions:
            user_sanctions = "[]"
        user_sanctions = json.loads(user_sanctions)

        message = \
            f"> Vous avez été **{sanction_type}**" \
            + (f" du serveur **{ctx.guild.name}**" if sanction_type in ["ban", "kick"] else f" sur le serveur **{ctx.guild.name}**") \
            + (f" `{time}` " if sanction_type == "tempmute" else " ") \
            + f"par **{ctx.author.display_name}**" \
            + ("." if not reason else f" pour `" + reason.replace("`", "'") + "`.")

        try: await member.send(message)
        except: pass

        sanction_data = {
            "type": sanction_type,
            "moderator": ctx.author.id,
            "timestamp": round(datetime.now().timestamp()),
            "reason": (reason.replace("`", "'") if len(reason) <= 50 else reason[:47].replace("`", "'") + "...") if reason else None
        }

        if sanction_type == "tempmute":
            sanction_data["time"] = time

        user_sanctions.append(sanction_data)

        await self.bot.db.set_data("member", "sanctions", json.dumps(user_sanctions), guild_id = ctx.guild.id, user_id = member.id)


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
    
    async def get_emoji(self, query):
        if emoji.is_emoji(query):
            return query
        
        query = query.split(":")
        if len(query) != 3:
            return None
        
        query = query[2].replace(">", "")
        try: query = self.bot.get_emoji(int(query))
        except: return None
        return query
    
    async def replace_vars(self, text, member = None, guild = None):
        if member:
            text \
                .replace("{MemberName}", member.name) \
                .replace("{MemberDisplayName}", member.display_name) \
                .replace("{MemberMention}", member.mention) \
                .replace("{MemberId}", member.id) \
                .replace("{MemberCreatedAt}", member.created_at.strftime('%d/%m/%Y %H:%M')) \
                .replace("{MemberCreatedAtf}", f"<t:{round(member.created_at.timestamp())}>") \
                .replace("{MemberCreatedAtR}", f"<t:{round(member.created_at.timestamp())}:R>") \
                .replace("{MemberRolesCount}", str(len(member.roles))) \
                .replace("{MemberStatus}", str(member.status).replace('dnd', 'ne pas déranger').replace('offline', 'hors ligne').replace('online', 'en ligne').replace('idle', 'inactif')) \
                .replace("{MemberActivity}", member.activity.name if member.activity else 'Aucune activitée')

        if guild:
            text \
                .replace("{ServerName}", guild.name) \
                .replace("{ServerId}", str(guild.id)) \
                .replace("{ServerCreatedAt}", guild.created_at.strftime('%d/%m/%Y %H:%M')) \
                .replace("{ServerCreatedAtf}", f"<t:{round(guild.created_at.timestamp())}>") \
                .replace("{ServerCreatedAtR}", f"<t:{round(guild.created_at.timestamp())}:R>") \
                .replace("{MemberCount}", str(len(guild.members))) \
                .replace("{ConnectedCount}", str(len([member for member in guild.members if member.status != discord.Status.offline]))) \
                .replace("{OnlineCount}", str(len([member for member in guild.members if member.status == discord.Status.online]))) \
                .replace("{OfflineCount}", str(len([member for member in guild.members if member.status == discord.Status.offline]))) \
                .replace("{DndCount}", str(len([member for member in guild.members if member.status == discord.Status.dnd]))) \
                .replace("{IdleCount}", str(len([member for member in guild.members if member.status == discord.Status.idle]))) \
                .replace("{AdminCount}", str(len([member for member in guild.members if member.guild_permissions.administrator]))) \
                .replace("{BotCount}", str(len([member for member in guild.members if member.bot]))) \
                .replace("{BoostCount}", str(guild.premium_subscription_count)) \
                .replace("{ChannelCount}", str(len(guild.channels))) \
                .replace("{InVoiceCount}", str(len([member for member in guild.members if member.voice])))

        return text