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
import os
import sys
import psutil
from datetime import datetime
from typing import Union
from discord.ext import commands
from utils.Paginator import PaginatorCreator
from utils.Database import Database

class Informations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases = ["alladmin"], description = "Voir les membres avec la permission administrateur")
    @commands.guild_only()
    async def alladmins(self, ctx):
        administrators = [f"{member.mention} `({member.id})`" for member in ctx.guild.members if (member.guild_permissions.administrator) and (not member.bot)]
        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = f"Administrateurs ({len(administrators)})",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = administrators,
            data_per_page = 10,
        )
        
        if type(paginator) == list:
            await ctx.send(embed = paginator[0])
        else:
            await paginator.send(ctx)


    @commands.command(aliases = ["botadmin"], description = "Voir les bots avec la permission administrateur")
    @commands.guild_only()
    async def botadmins(self, ctx):
        bots = [f"{member.mention} `({member.id})`" for member in ctx.guild.members if (member.guild_permissions.administrator) and (member.bot)]
        
        if not bots:
            await ctx.send("> Il n'y a pas de booster sur votre serveur.")
            return
        
        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = f"Bot Administrateurs ({len(bots)})",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = bots,
            data_per_page = 10,
        )

        if type(paginator) == list:
            await ctx.send(embed = paginator[0])
        else:
            await paginator.send(ctx)

    
    @commands.command(aliases = ["subscribers", "boosteurs"], description = "Voir les boosters du serveur")
    @commands.guild_only()
    async def boosters(self, ctx):
        boosters = [f"{subscriber.mention} (boost depuis <t:{round(subscriber.premium_since.timestamp())}:R>)" for subscriber in ctx.guild.premium_subscribers]
        
        if not boosters:
            await ctx.send("> Il n'y a pas de booster sur ce serveur")
            return
        
        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = f"Boosters ({len(boosters)})",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = boosters,
            data_per_page = 10,
        )

        if type(paginator) == list:
            await ctx.send(embed = paginator[0])
        else:
            await paginator.send(ctx)


    @commands.command(description = "Voir les membres avec un certains rôle", aliases = ["rlmb", "rolemb"])
    @commands.guild_only()
    async def rolemembers(self, ctx, role : discord.Role):
        members = [f"{member.mention} (`{member.id}`)" for member in role.members]
        
        if not members:
            await ctx.send(f"> Il n'y a aucun membre avec le rôle {role.mention}", allowed_mentions = None)
            return
        
        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = f"Membre avec @{role.name} ({len(members)})",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = members,
            data_per_page = 10,
        )

        if type(paginator) == list:
            await ctx.send(embed = paginator[0])
        else:
            await paginator.send(ctx)


    @commands.command(description = "Voir des informations relatives au serveur")
    @commands.guild_only()
    async def serverinfo(self, ctx):
        member_online, member_idle, member_dnd = 0, 0, 0
        vanity_url = "Non débloqué"
        if "VANITY_URL" in ctx.guild.features:
            try: vanity_url = f"**{await ctx.guild.vanity_invite()}**"
            except: vanity_url = "Aucun accès"

        for member in ctx.guild.members:
            match str(member.status):
                case "online":
                    member_online += 1
                case "idle":
                    member_idle += 1
                case "dnd":
                    member_dnd += 1
        
        embed = discord.Embed(
            title = ctx.guild.name,
            thumbnail = ctx.guild.icon.url if ctx.guild.icon else None,
            color = await self.bot.get_theme(ctx.guild.id),
            description = ctx.guild.description if ctx.guild.description else "*Aucune description*"
        ).add_field(
            name = "Propriétaire",
            value = f"{ctx.guild.owner.mention}"
        ).add_field(
            name = "Date de création",
            value = f"**<t:{round(ctx.guild.created_at.timestamp())}:R>**",
            inline = False
        )
        
        embed.add_field(
            name = "Membres",
            value = f"*En lignes* : **{member_online}**\n"
            + f"*Inactifs* : **{member_idle}**\n"
            + f"*Ne pas déranger* : **{member_dnd}**\n"
            + f"*Hors lignes* : **{len(ctx.guild.members) - member_online - member_dnd - member_idle}**\n"
            + f"*Total* : **{len(ctx.guild.members)}**"
        )
        embed.add_field(
            name = "Salons",
            value = f"*Textuels* : **{len(ctx.guild.text_channels)}**\n"
            + f"*Vocaux* : **{len(ctx.guild.voice_channels)}**\n"
            + f"*Forums* : **{len(ctx.guild.forum_channels)}**\n"
            + f"*Conférences* : **{len(ctx.guild.stage_channels)}**\n"
            + f"*Catégories* : **{len(ctx.guild.categories)}**\n"
            + f"*Total* : **{len(ctx.guild.channels)}**"
        )
        embed.add_field(
            name = "Rôles",
            value = f"*Rôles admin* : **{len([role for role in ctx.guild.roles if role.permissions.administrator])}**\n"
            + f"*Rôles de bot* : **{len([role for role in ctx.guild.roles if role.is_bot_managed()])}**\n"
            + f"*Rôle booster* : " + (ctx.guild.premium_subscriber_role.mention if ctx.guild.premium_subscriber_role else "Aucun") + "\n"
            + f"*Rôles* : **{len(ctx.guild.roles)}**"
        )
        embed.add_field(
            name = "Autres informations",
            value = f"*Boosts* : **{ctx.guild.premium_subscription_count}**\n"
            + f"*Boosters* : **{len(ctx.guild.premium_subscribers)}**\n"
            + f"*Bots* : **{len([m for m in ctx.guild.members if m.bot])}**\n"
            + f"*Vanity* : {vanity_url}",
            inline = True
        )
        embed.set_footer(
            text = f"ID : {ctx.guild.id}"
        )
        
        embed.timestamp = datetime.now()
        if ctx.guild.banner:
            embed.set_image(url = ctx.guild.banner.url)

        await ctx.send(embed = embed)


    @commands.command(usage = "<role>", description = "Voir des informations relatives à un certain rôle")
    @commands.guild_only()
    async def role(self, ctx, role : discord.Role):
        embed = discord.Embed(
            description = f"### {role.mention} (`{role.id}`)",
            color = await self.bot.get_theme(ctx.guild.id)
        )

        embed.add_field(name = "Date de création", value = f"<t:{round(role.created_at.timestamp())}:R>")
        embed.add_field(name = "Membre le possédant", value = f"{len(role.members)}")
        embed.add_field(name = "Position", value = f"{role.position}/{len(ctx.guild.roles)}")
        embed.add_field(name = "Mentionnable", value = "Oui" if role.mentionable else "Non")
        embed.add_field(name = "Affiché séparément", value = "Oui" if role.hoist else "Non")
        embed.add_field(name = "Couleur", value = f"{role.color}")
        dangerous_permissions = [
            "administrator",
            "kick_members",
            "ban_members",
            "manage_channels",
            "manage_guild",
            "view_audit_log",
            "manage_messages",
            "mention_everyone",
            "manage_roles",
            "manage_webhooks",
            "manage_emojis_and_stickers",
            "manage_threads"
        ]
        role_dangerous_permissions = []
        for permission in dangerous_permissions:
            if getattr(role.permissions, permission):
                role_dangerous_permissions.append(permission.replace("_", " ").capitalize())
        embed.add_field(
            name = "Permissions dangereuses", 
            value = f"Aucune" 
            if not role_dangerous_permissions
            else ", ".join(role_dangerous_permissions[:4]) + (f" (et {len(role_dangerous_permissions) - 5} autres)" if len(role_dangerous_permissions) > 3 else "")
        )
        embed.timestamp = datetime.now()

        await ctx.send(embed = embed)


    @commands.command(description = "Voir des informations relatives à un salon")
    @commands.guild_only()
    async def channel(self, ctx, channel : discord.TextChannel = None):
        if not channel:
            channel = ctx.channel

        embed = discord.Embed(
            description = f"### {channel.mention} (`{channel.id}`)",
            color = await self.bot.get_theme(ctx.guild.id)
        )
        embed.add_field(name = "Sujet", value = channel.topic if channel.topic else "Aucun")
        embed.add_field(name = "Date de création", value = f"<t:{round(channel.created_at.timestamp())}:R>")
        embed.add_field(name = "Position", value = f"{channel.position}/{len(ctx.guild.channels)}")
        embed.add_field(name = "Catégorie", value = f"{channel.category}" if channel.category else "Aucune")
        embed.add_field(name = "Mode lent", value = f"{channel.slowmode_delay}s" if channel.slowmode_delay else "Désactivé")
        embed.add_field(name = "Nsfw", value = "Oui" if channel.is_nsfw else "Non")
        embed.add_field(name = "Utilisateurs y ayants accès", value = f"{len(channel.members)}")
        embed.timestamp = datetime.now()
        
        await ctx.send(embed = embed)


    @commands.command(description = "Voir des informations realives aux statistiques vocales")
    @commands.guild_only()
    async def vocinfo(self, ctx):
        embed = discord.Embed(
            title = "Statistiques vocales",
            color = await self.bot.get_theme(ctx.guild.id),
            thumbnail = ctx.guild.icon.url if ctx.guild.icon else None
        )

        users_count = 0
        users_streaming_count = 0
        users_video_count = 0
        users_mute_count = 0
        users_deaf_count = 0

        for voice_channel in ctx.guild.voice_channels:
            for member in voice_channel.members:

                member_voicestate = member.voice

                users_count += 1
                if member_voicestate.self_stream: users_streaming_count += 1
                if member_voicestate.self_video: users_video_count += 1
                if member_voicestate.self_mute or member_voicestate.self_mute: users_mute_count += 1
                if member_voicestate.self_deaf or member_voicestate.deaf: users_deaf_count += 1

        embed.add_field(name = "En vocal", value = str(users_count))
        embed.add_field(name = "Mute", value = str(users_mute_count))
        embed.add_field(name = "En sourdine", value = str(users_deaf_count))
        embed.add_field(name = "En streaming", value = str(users_streaming_count))
        embed.add_field(name = "En vidéo", value = str(users_video_count))

        await ctx.send(embed = embed)


    @commands.command(description = "Obtenir des informations relatives au bot")
    @commands.guild_only()
    async def botinfo(self, ctx):
        embed = discord.Embed(
            title = self.bot.user.display_name,
            description = "Bot discord avancé, optimisé et complet.",
            color = await self.bot.get_theme(ctx.guild.id),
            thumbnail = self.bot.user.avatar.url
        )

        with open("config.json") as file:
            data = json.load(file)
            developers = data["developers"]

        # calculate memory
        pid = os.getpid()
        python_process = psutil.Process(pid)
        memory_usage = python_process.memory_info()[0] / 2.**30


        view = discord.ui.View()
        view.add_item(discord.ui.Button(style = discord.ButtonStyle.link, label = f"Inviter {self.bot.user.name}", url = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot"))
        developers = [await self.bot.fetch_user(developer) for developer in developers]
        embed.add_field(name = "Développeur", value = ", ".join([f'[**{developer.display_name}**](https://discord.com/users/{developer.id})' for developer in developers]))
        embed.add_field(name = "Vitesse", value = f"{round(self.bot.latency * 1000)}ms")
        embed.add_field(name = "Version Python", value = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        embed.add_field(name = "Version Pycord", value = f"{discord.__version__}")
        embed.add_field(name = "Serveurs", value = f"{len(self.bot.guilds)}")
        embed.add_field(name = "Utilisateur", value = f"{len(self.bot.users)}")
        embed.add_field(name = "Mémoire utilisée", value = str(round(memory_usage, 3)) + "GB")

        await ctx.send(embed = embed, view = view)

    @commands.command(description = "Voir des informations relatives à un membre/utilisateur")
    @commands.guild_only()
    async def user(self, ctx, user : discord.User = None):
        if not user:
            user = ctx.author

        embed = discord.Embed(
            description = f"### {user.mention} (`{user.id}`)",
            color = await self.bot.get_theme(ctx.guild.id),
            thumbnail = user.avatar.url
        )
        
        user_flags = []
        for flag in user.public_flags:
            if not flag[1]: continue
            cflag = flag[0].split("_")
            for index, word in enumerate(cflag):
                cflag[index] = word.capitalize()
            user_flags.append("".join(cflag))

        embed.add_field(name = "Création du compte", value = f"<t:{round(user.created_at.timestamp())}:R>")
        embed.add_field(name = "Badges", value = ", ".join(user_flags) if user_flags else "Aucun")
        embed.add_field(name = "Bot", value = "Oui" if user.bot else "Non")

        member = None
        try: member = await ctx.guild.fetch_member(user.id)
        except: pass

        if member:
            embed.add_field(name = "Status", value = member.status)
            embed.add_field(name = "Date d'arrivée", value = f"<t:{round(member.joined_at.timestamp())}:R>")
            if member.premium_since:
                embed.add_field(name = "Booster depuis", value = f"<t:{round(member.premium_since.timestamp())}:R>")
            embed.add_field(name = "Rôle le plus haut", value = f"{member.top_role.mention}")
        if user.banner: embed.set_image(url = user.banner.url)
        await ctx.send(embed = embed)


    @commands.command(description = "Voir la photo de profil d'un utilisateur")
    @commands.guild_only()
    async def pic(self, ctx, user : discord.User = None):
        if not user:
            user = ctx.author

        view = discord.ui.View(timeout = None)
        view.add_item(discord.ui.Button(label = "Avatar", style = discord.ButtonStyle.link, url = user.avatar.url))
        embed = discord.Embed(
            title = user.display_name,
            url = f"https://discord.com/users/{user.id}",
            color = await self.bot.get_theme(ctx.guild.id)
        ).set_image(url = user.avatar.url)

        embed2 = None
        if user.display_avatar.url != user.avatar.url:
            embed2 = discord.Embed(
                title = user.display_name + " (Avatar de base)",
                url = f"https://discord.com/users/{user.id}",
                color = await self.bot.get_theme(ctx.guild.id)
            ).set_image(url = user.display_avatar.url)
            view.add_item(discord.ui.Button(label = "Avatar par défaut", style = discord.ButtonStyle.link, url = user.display_avatar.url))
        
        if not embed2:
            await ctx.send(embed = embed)
            return
        await ctx.send(embeds = [embed, embed2], view = view)


    @commands.command(description = "Voir la bannière de profil d'un utilisateur")
    @commands.guild_only()
    async def banner(self, ctx, user : discord.User = None):
        if not user:
            user = ctx.author
        if not user.banner:
            await ctx.send(f"> " + (user.mention + " n'a" if user != ctx.author else "Vous n'avez") + " pas de bannière.", allowed_mentions = None)
            return
        
        view = discord.ui.View(timeout = None)
        view.add_item(discord.ui.Button(label = "Bannière", style = discord.ButtonStyle.link, url = user.banner.url))
        embed = discord.Embed(
            title = user.display_name,
            url = f"https://discord.com/users/{user.id}",
            color = await self.bot.get_theme(ctx.guild.id)
        ).set_image(url = user.banner.url)

        await ctx.send(embed = embed, view = view)


    @commands.command(description = "Voir l'icône du serveur ou celui d'un des serveurs du bot")
    @commands.guild_only()
    async def serverpic(self, ctx, server : discord.Guild = None):
        if not server:
            server = ctx.guild
        if not ctx.guild.icon:
            await ctx.send(f"> Le serveur{' ' + server.name if server != ctx.guild else ''} n'a pas d'icône.")
            return
        
        view = discord.ui.View(timeout = None)
        view.add_item(discord.ui.Button(label = "Icône", style = discord.ButtonStyle.link, url = server.icon.url))
        embed = discord.Embed(
            title = server.name,
            color = await self.bot.get_theme(ctx.guild.id)
        ).set_image(url = server.icon.url)

        await ctx.send(embed = embed, view = view)


    @commands.command(description = "Voir la bannière du serveur ou celui d'un des serveurs du bot")
    @commands.guild_only()
    async def serverbanner(self, ctx, server : discord.Guild = None):
        if not server:
            server = ctx.guild
        if not ctx.guild.banner:
            await ctx.send(f"> Le serveur{' ' + server.name if server != ctx.guild else ''} n'a pas de bannière.")
            return
        
        view = discord.ui.View(timeout = None)
        view.add_item(discord.ui.Button(label = "Bannière", style = discord.ButtonStyle.link, url = server.banner.url))
        embed = discord.Embed(
            title = server.name,
            color = await self.bot.get_theme(ctx.guild.id)
        ).set_image(url = server.banner.url)

        await ctx.send(embed = embed, view = view)


    @commands.command(description = "Voir le dernier message supprimé du salon")
    @commands.guild_only()
    async def snipe(self, ctx):
        database = Database()
        await database.connect()

        try:
            author_id = await database.get_data("snipe", "author_id", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
            author_name = await database.get_data("snipe", "author_name", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
            author_avatar = await database.get_data("snipe", "author_avatar", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
            message_content = await database.get_data("snipe", "message_content", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
            message_datetime = await database.get_data("snipe", "message_datetime", guild_id = ctx.guild.id, channel_id = ctx.channel.id)
        finally: await database.disconnect()

        if not author_id:
            await ctx.send("> Aucun récent message supprimé n'a été enregistré.")
            return
        
        embed = discord.Embed(
            author = discord.EmbedAuthor(name = author_name, icon_url = author_avatar, url = "https://discord.com/users/" + str(author_id)),
            description = (message_content if len(message_content) < 2000 else message_content[:1500]),
            color = await self.bot.get_theme(ctx.guild.id),
            timestamp = message_datetime
        )

        await ctx.send(embed = embed)


    @commands.command(aliases = ["ping"], description = "Voir la vitesse actuel du bot")
    @commands.guild_only()
    async def speed(self, ctx):
        await ctx.send(
            embed = discord.Embed(
                title = "Vitesse du bot",
                description = "**`" + str(round(self.bot.latency * 1000)) + "ms`**",
                color = await self.bot.get_theme(ctx.guild.id),
            )
        )


def setup(bot):
    bot.add_cog(Informations(bot))