import json
import discord
import emoji
import asyncio

from discord.ext import commands
from typing import Union
from datetime import timedelta, datetime

class Tools:
    """
    Classe "outils" où sont stockés des fonctions utiles souvent utilisées
    """
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

    def create_delete_message_task(self, message):
        async def task():
            try: await message.delete()
            except: pass
        loop = asyncio.get_event_loop()
        loop.create_task(task())

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


    async def get_member_vars_dict(self, member):
        return {
            "{MemberName}": member.name,
            "{MemberDisplayName}": member.display_name,
            "{MemberMention}": member.mention,
            "{MemberId}": str(member.id),
            "{MemberCreatedAt}": member.created_at.strftime('%d/%m/%Y %H:%M'),
            "{MemberCreatedAtf}": f"<t:{round(member.created_at.timestamp())}>",
            "{MemberCreatedAtR}": f"<t:{round(member.created_at.timestamp())}:R>",
            "{MemberRolesCount}": str(len(member.roles)) if member.roles else "0",
            "{MemberStatus}": str(member.status).replace('dnd', 'ne pas déranger').replace('offline', 'hors ligne').replace('online', 'en ligne').replace('idle', 'inactif'),
            "{MemberActivity}": member.activity.name if member.activity else 'Aucune activité'
        }


    async def get_guild_vars_dict(self, guild):
        return {
            "{ServerName}": guild.name,
            "{ServerId}": str(guild.id),
            "{ServerCreatedAt}": guild.created_at.strftime('%d/%m/%Y %H:%M'),
            "{ServerCreatedAtf}": f"<t:{round(guild.created_at.timestamp())}>",
            "{ServerCreatedAtR}": f"<t:{round(guild.created_at.timestamp())}:R>",
            "{MemberCount}": str(len(guild.members)),
            "{ConnectedCount}": str(len([member for member in guild.members if member.status != discord.Status.offline])),
            "{OnlineCount}": str(len([member for member in guild.members if member.status == discord.Status.online])),
            "{OfflineCount}": str(len([member for member in guild.members if member.status == discord.Status.offline])),
            "{DndCount}": str(len([member for member in guild.members if member.status == discord.Status.dnd])),
            "{IdleCount}": str(len([member for member in guild.members if member.status == discord.Status.idle])),
            "{AdminCount}": str(len([member for member in guild.members if member.guild_permissions.administrator])),
            "{BotCount}": str(len([member for member in guild.members if member.bot])),
            "{BoostCount}": str(guild.premium_subscription_count),
            "{ChannelCount}": str(len(guild.channels)),
            "{InVoiceCount}": str(len([member for member in guild.members if member.voice]))
        }


    def multiple_replaces(self, text, dict_replaces : dict):
        if not text: return None

        for key, value in dict_replaces.items():
            text = text.replace(key, value)

        return text
    

    def embed_from_dict(self, embed_dict : dict) -> discord.Embed:
        embed = discord.Embed(
            title = embed_dict["title"],
            description = embed_dict["description"],
            color = embed_dict["color"],
            timestamp = embed_dict["timestamp"],
            footer = discord.EmbedFooter(text = embed_dict["footer"]["text"], icon_url = embed_dict["footer"]["icon_url"]) if embed_dict["footer"]["text"] else None,
            author = discord.EmbedAuthor(name = embed_dict["author"]["name"], icon_url = embed_dict["author"]["icon_url"], url = embed_dict["author"]["url"]) if embed_dict["author"]["name"] else None
        )

        if embed_dict["thumbnail"]:
            embed.set_thumbnail(url = embed_dict["thumbnail"])
        if embed_dict["image"]:
            embed.set_image(url = embed_dict["image"])

        for field_data in embed_dict["fields"]:
            embed.add_field(name = field_data["name"], value = field_data["value"], inline = field_data["inline"])

        return embed
    

    async def send_join_message(self, guild, member):       
        joins_sql_data = await self.bot.db.execute(f"SELECT * FROM joins WHERE guild_id = {guild.id}", fetch = True)
        joins_table_columns = await self.bot.db.get_table_columns("joins")
        joins_data = dict(zip(joins_table_columns, joins_sql_data[0]))
        del joins_data["guild_id"]

        member_vars_dict = await self.get_member_vars_dict(member)
        guild_vars_dict = await self.get_guild_vars_dict(guild)
        vars_to_replace = {**member_vars_dict, **guild_vars_dict}

        if joins_data["message_dm_enabled"]:
            view = discord.ui.View(timeout = None)
            view.add_item(discord.ui.Button(label = f"Envoyé depuis : {guild.name}", disabled = True))
            await member.send(self.multiple_replaces(joins_data["message_dm"], vars_to_replace), view = view)

        embed = None
        try: embed_dict = json.loads(joins_data["embed"])
        except: embed_dict = {}
        if len(embed_dict):
            embed_dict["title"] = self.multiple_replaces(embed_dict["title"], vars_to_replace)
            embed_dict["description"] = self.multiple_replaces(embed_dict["description"], vars_to_replace)
            embed_dict["footer"]["text"] = self.multiple_replaces(embed_dict["footer"]["text"], vars_to_replace)
            embed_dict["author"]["name"] = self.multiple_replaces(embed_dict["author"]["name"], vars_to_replace)

            for index in range(len(embed_dict["fields"])):
                embed_dict["fields"][index]["name"] = self.multiple_replaces(embed_dict["fields"][index]["name"], vars_to_replace)
                embed_dict["fields"][index]["value"] = self.multiple_replaces(embed_dict["fields"][index]["value"], vars_to_replace)

            embed = self.embed_from_dict(embed_dict)

        join_channel = guild.get_channel(joins_data["channel"])
        if not join_channel:
            return

                
        message_content = self.multiple_replaces(joins_data["message"], vars_to_replace)
        await join_channel.send(content = message_content, embed = embed)


    async def send_leave_message(self, guild, member):       
        leaves_sql_data = await self.bot.db.execute(f"SELECT * FROM leaves WHERE guild_id = {guild.id}", fetch = True)
        leaves_table_columns = await self.bot.db.get_table_columns("leaves")
        leaves_data = dict(zip(leaves_table_columns, leaves_sql_data[0]))
        
        del leaves_data["guild_id"]

        member_vars_dict = await self.get_member_vars_dict(member)
        guild_vars_dict = await self.get_guild_vars_dict(guild)
        vars_to_replace = {**member_vars_dict, **guild_vars_dict}

        embed = None
        try: embed_dict = json.loads(leaves_data["embed"])
        except: embed_dict = {}
        if len(embed_dict):
            embed_dict["title"] = self.multiple_replaces(embed_dict["title"], vars_to_replace)
            embed_dict["description"] = self.multiple_replaces(embed_dict["description"], vars_to_replace)
            embed_dict["footer"]["text"] = self.multiple_replaces(embed_dict["footer"]["text"], vars_to_replace)
            embed_dict["author"]["name"] = self.multiple_replaces(embed_dict["author"]["name"], vars_to_replace)

            for index in range(len(embed_dict["fields"])):
                embed_dict["fields"][index]["name"] = self.multiple_replaces(embed_dict["fields"][index]["name"], vars_to_replace)
                embed_dict["fields"][index]["value"] = self.multiple_replaces(embed_dict["fields"][index]["value"], vars_to_replace)

            embed = self.embed_from_dict(embed_dict)

        leave_channel = guild.get_channel(leaves_data["channel"])
        if not leave_channel:
            return

        message_content = self.multiple_replaces(leaves_data["message"], vars_to_replace)
        await leave_channel.send(content = message_content, embed = embed)


    def get_message_components(message : discord.Message) -> dict:
        """
        Returned dictionnary format : 
            ```
            {
                "buttons": List[discord.ui.Button],
                "selectors": List[discord.ui.SelectMenu]
            }
            ```
        """
        data = {
            "buttons": [],
            "selectors": []
        }

        for components in message.components:
            if not type(components) == discord.ActionRow:
                return
            
            for children in components.children:
                if type(children) == discord.ui.Button:
                    data["buttons"].append(children)
                if type(children) == discord.ui.Select:
                    data["selectors"].append(children)

        return data