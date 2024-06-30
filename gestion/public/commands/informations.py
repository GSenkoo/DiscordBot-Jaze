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
        translations = await self.bot.get_translation("alladmins", ctx.guild.id)

        administrators = [f"{member.mention} `({member.id})`" for member in ctx.guild.members if (member.guild_permissions.administrator) and (not member.bot)]
        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = f"{translations['Administrateurs']} ({len(administrators)})",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = administrators,
            data_per_page = 10,
        )
        
        if type(paginator) == list:
            await ctx.send(embed = paginator[0])
        else:
            await paginator.send(ctx)


    @commands.command(aliases = ["allbot"], description = "Voir les bots sur le serveur")
    @commands.guild_only()
    async def allbots(self, ctx):
        translations = await self.bot.get_translation("allbots", ctx.guild.id)

        bots = [f"{member.mention} `({member.id})`" for member in ctx.guild.members if member.bot]
        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = f"{translations['Bots']} ({len(bots)})",
            embed_color = await self.bot.get_theme(ctx.guild.id),
            data_list = bots,
            data_per_page = 10,
        )
        
        if type(paginator) == list:
            await ctx.send(embed = paginator[0])
        else:
            await paginator.send(ctx)


    @commands.command(aliases = ["botadmin"], description = "Voir les bots avec la permission administrateur")
    @commands.guild_only()
    async def botadmins(self, ctx):
        translations = await self.bot.get_translation("botadmins", ctx.guild.id)

        bots = [f"{member.mention} `({member.id})`" for member in ctx.guild.members if (member.guild_permissions.administrator) and (member.bot)]
        if not bots:
            await ctx.send(f'>' + translations['Il n\'y a pas de bot avec la permission administrateur sur le serveur'] + '.')
            return
        
        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = f"{translations['Bot Administrateurs']} ({len(bots)})",
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
        translations = await self.bot.get_translation("boosters", ctx.guild.id)

        boosters = [f"{subscriber.mention} ({translations['boost depuis [data_date]'].replace('[data_date]', f'<t:{round(subscriber.premium_since.timestamp())}:R>')})" for subscriber in ctx.guild.premium_subscribers]

        if not boosters:
            await ctx.send(f"> " + {translations["Il n'y a pas de booster sur ce serveur"]})
            return

        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = f"{translations['Boosters']} ({len(boosters)})",
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
    async def rolemembers(self, ctx, role: discord.Role):
        translations = await self.bot.get_translation("rolemembers", ctx.guild.id)

        members = [f"{member.mention} (`{member.id}`)" for member in role.members]

        if not members:
            await ctx.send(f">" +  translations["Il n'y a aucun membre avec le rôle"] + f" {role.mention}", allowed_mentions = None)
            return

        paginator_creator = PaginatorCreator()
        paginator = await paginator_creator.create_paginator(
            title = f"{translations['Membre avec']} @{role.name} ({len(members)})",
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
        translation = await self.bot.get_translation("serverinfo", ctx.guild.id)

        member_online, member_idle, member_dnd = 0, 0, 0
        vanity_url = f"{translation['Non débloqué']}"
        if "VANITY_URL" in ctx.guild.features:
            try: vanity_url = f"**{await ctx.guild.vanity_invite()}**"
            except: vanity_url = f"{translation['Aucun accès']}"

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
            description = ctx.guild.description if ctx.guild.description else f"*{translation['Aucune description']}*"
        ).add_field(
            name = f"{translation['Propriétaire']}",
            value = f"{ctx.guild.owner.mention}"
        ).add_field(
            name = f"{translation['Date de création']}",
            value = f"**<t:{round(ctx.guild.created_at.timestamp())}:R>**",
            inline = False
        )
        
        embed.add_field(
            name = f"{translation['Membres']}",
            value = f"*{translation['En lignes']}* : **{member_online}**\n"
            + f"*{translation['Inactifs']}* : **{member_idle}**\n"
            + f"*{translation['Ne pas déranger']}* : **{member_dnd}**\n"
            + f"*{translation['Hors lignes']}* : **{len(ctx.guild.members) - member_online - member_dnd - member_idle}**\n"
            + f"*{translation['Total']}* : **{len(ctx.guild.members)}**"
        )
        embed.add_field(
            name = "Salons",
            value = f"*{translation['Textuels']}* : **{len(ctx.guild.text_channels)}**\n"
            + f"*{translation['Vocaux']}* : **{len(ctx.guild.voice_channels)}**\n"
            + f"*{translation['Forums']}* : **{len(ctx.guild.forum_channels)}**\n"
            + f"*{translation['Conférences']}* : **{len(ctx.guild.stage_channels)}**\n"
            + f"*{translation['Catégories']}* : **{len(ctx.guild.categories)}**\n"
            + f"*{translation['Total']}* : **{len(ctx.guild.channels)}**"
        )
        embed.add_field(
            name = f"{translation['Rôles']}",
            value = f"*{translation['Rôles admin']}* : **{len([role for role in ctx.guild.roles if role.permissions.administrator])}**\n"
            + f"*{translation['Rôles de bot']}* : **{len([role for role in ctx.guild.roles if role.is_bot_managed()])}**\n"
            + f"*{translation['Rôle booster']}* : " + (ctx.guild.premium_subscriber_role.mention if ctx.guild.premium_subscriber_role else "Aucun") + "\n"
            + f"*{translation['Rôles']}* : **{len(ctx.guild.roles)}**"
        )
        embed.add_field(
            name = "Autres informations",
            value = f"*{translation['Boosts']}* : **{ctx.guild.premium_subscription_count}**\n"
            + f"*{translation['Boosters']}* : **{len(ctx.guild.premium_subscribers)}**\n"
            + f"*{translation['Bots']}* : **{len([m for m in ctx.guild.members if m.bot])}**\n"
            + f"*{translation['Vanity']}* : {vanity_url}",
            inline = True
        )
        embed.set_footer(
            text = f"{translation['ID']} : {ctx.guild.id}"
        )
        
        embed.timestamp = datetime.now()
        if ctx.guild.banner:
            embed.set_image(url = ctx.guild.banner.url)

        await ctx.send(embed = embed)


    @commands.command(usage = "<role>", description = "Voir des informations relatives à un certain rôle")
    @commands.guild_only()
    async def role(self, ctx, role : discord.Role):
        translation = await self.bot.get_translation("role", ctx.guild.id)
        translation_permissions = await self.bot.get_translation("permissions", ctx.guild.id)

        embed = discord.Embed(
            description = f"### {role.mention} (`{role.id}`)",
            color = await self.bot.get_theme(ctx.guild.id)
        )
        
        embed.add_field(name = f"{translation['Date de création']}", value = f"<t:{round(role.created_at.timestamp())}:R>")
        embed.add_field(name = f"{translation['Membre le possédant']}", value = f"{len(role.members)}")
        embed.add_field(name = f"{translation['Position']}", value = f"{role.position}/{len(ctx.guild.roles)}")
        embed.add_field(name = f"{translation['Mentionnable']}", value = f"{translation['Oui']}" if role.mentionable else f"{translation['Non']}")
        embed.add_field(name = f"{translation['Affiché séparément']}", value = f"{translation['Oui']}" if role.hoist else f"{translation['Non']}")
        embed.add_field(name = f"{translation['Couleur']}", value = f"{role.color}")
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
                role_dangerous_permissions.append(translation_permissions[permission])

        embed.add_field(
            name = f"{translation['Permissions dangereuses']}", 
            value = f"{translation['Aucune']}" 
            if not role_dangerous_permissions
            else ", ".join(role_dangerous_permissions[:4]) + (translation['et [data_number] autres'].replace("[data_number]", str(len(role_dangerous_permissions) - 5)) if len(role_dangerous_permissions) > 3 else "")
        )
        embed.timestamp = datetime.now()

        await ctx.send(embed = embed)


    @commands.command(description = "Voir des informations relatives à un salon")
    @commands.guild_only()
    async def channel(self, ctx, channel : discord.TextChannel = None):
        translation = await self.bot.get_translation("channel", ctx.guild.id)
        
        if not channel:
            channel = ctx.channel

        embed = discord.Embed(
            description = f"### {channel.mention} (`{channel.id}`)",
            color = await self.bot.get_theme(ctx.guild.id)
        )
        embed.add_field(name = f"{translation['Sujet']}", value = channel.topic if channel.topic else f"{translation['Aucun']}")
        embed.add_field(name = f"{translation['Date de création']}", value = f"<t:{round(channel.created_at.timestamp())}:R>")
        embed.add_field(name = f"{translation['Position']}", value = f"{channel.position}/{len(ctx.guild.channels)}")
        embed.add_field(name = f"{translation['Catégorie']}", value = f"{channel.category}" if channel.category else f"{translation['Aucune']}")
        embed.add_field(name = f"{translation['Mode lent']}", value = translation["[data_time] secondes"].replace("[data_time]", str(channel.slowmode_delay)) if channel.slowmode_delay else f"{translation['Désactivé']}")
        embed.add_field(name = f"{translation['Nsfw']}", value = translation["Oui"] if channel.is_nsfw else translation["Non"])
        embed.add_field(name = f"{translation['Utilisateurs y ayants accès']}", value = f"{len(channel.members)}")
        embed.timestamp = datetime.now()
        
        await ctx.send(embed = embed)


    @commands.command(description = "Voir des informations realives aux statistiques vocales")
    @commands.guild_only()
    async def vocinfo(self, ctx):
        translation = await self.bot.get_translation("vocinfo", ctx.guild.id)

        embed = discord.Embed(
            title = f"{translation['Statistiques vocales']}",
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

        embed.add_field(name = translation["En vocal"], value = str(users_count))
        embed.add_field(name = translation["Mute"], value = str(users_mute_count))
        embed.add_field(name = translation["En sourdine"], value = str(users_deaf_count))
        embed.add_field(name = translation["En streaming"], value = str(users_streaming_count))
        embed.add_field(name = translation["En vidéo"], value = str(users_video_count))

        await ctx.send(embed = embed)


    @commands.command(description = "Obtenir des informations relatives au bot")
    @commands.guild_only()
    async def botinfo(self, ctx):
        translation = await self.bot.get_translation("botinfo", ctx.guild.id)

        embed = discord.Embed(
            title = self.bot.user.display_name,
            description = translation["Bot discord avancé, optimisé et complet."],
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
        view.add_item(discord.ui.Button(style = discord.ButtonStyle.link, label = translation["Inviter [data_user]"].replace("data_user", self.bot.user.name), url = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot"))
        developers = [await self.bot.fetch_user(developer) for developer in developers]
        embed.add_field(name = translation["Développeur"], value = ", ".join([f'[**{developer.display_name}**](https://discord.com/users/{developer.id})' for developer in developers]))
        embed.add_field(name = translation["Vitesse"], value = f"{round(self.bot.latency * 1000)}ms")
        embed.add_field(name = translation["Version Python"], value = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        embed.add_field(name = translation["Version Pycord"], value = f"{discord.__version__}")
        embed.add_field(name = translation["Serveurs"], value = f"{len(self.bot.guilds)}")
        embed.add_field(name = translation["Utilisateur"], value = f"{len(self.bot.users)}")
        embed.add_field(name = translation["Mémoire utilisée"], value = str(round(memory_usage, 3)) + "GB")

        await ctx.send(embed = embed, view = view)

    @commands.command(description = "Voir des informations relatives à un membre/utilisateur")
    @commands.guild_only()
    async def user(self, ctx, user : discord.User = None):
        translation = await self.bot.get_translation("user", ctx.guild.id)
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

        embed.add_field(name = translation["Création du compte"], value = f"<t:{round(user.created_at.timestamp())}:R>")
        embed.add_field(name = translation["Badges"], value = ", ".join(user_flags) if user_flags else translation["Aucun"])
        embed.add_field(name = translation["Bot"], value = translation["Oui"] if user.bot else translation["Non"])

        member = None
        try: member = await ctx.guild.fetch_member(user.id)
        except: pass

        if member:
            embed.add_field(name = translation["Status"], value = member.status)
            embed.add_field(name = translation["Date d'arrivée"], value = f"<t:{round(member.joined_at.timestamp())}:R>")
            if member.premium_since:
                embed.add_field(name = translation["Booster depuis"], value = f"<t:{round(member.premium_since.timestamp())}:R>")
            embed.add_field(name = translation["Rôle le plus haut"], value = f"{member.top_role.mention}")
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
            translation = await self.bot.get_translation("pic", ctx.guild.id)
            embed2 = discord.Embed(
                title = user.display_name + f" ({translation['Avatar de base']})",
                url = f"https://discord.com/users/{user.id}",
                color = await self.bot.get_theme(ctx.guild.id)
            ).set_image(url = user.display_avatar.url)
            view.add_item(discord.ui.Button(label = translation["Avatar par défaut"], style = discord.ButtonStyle.link, url = user.display_avatar.url))
        
        if not embed2:
            await ctx.send(embed = embed)
            return
        await ctx.send(embeds = [embed, embed2], view = view)


    @commands.command(description = "Voir la bannière de profil d'un utilisateur")
    @commands.guild_only()
    async def banner(self, ctx, user : discord.User = None):
        translation = await self.bot.get_translation("banner", ctx.guild.id)

        if not user:
            user = ctx.author
        if not user.banner:
            await ctx.send(f"> " + (translation["[data_user] n'a pas de bannière"].replace("[data_user]", user.mention) if user != ctx.author else translation["Vous n'avez pas de bannière"]) + ".", allowed_mentions = None)
            return
        
        view = discord.ui.View(timeout = None)
        view.add_item(discord.ui.Button(label = translation["Bannière"], style = discord.ButtonStyle.link, url = user.banner.url))
        embed = discord.Embed(
            title = user.display_name,
            url = f"https://discord.com/users/{user.id}",
            color = await self.bot.get_theme(ctx.guild.id)
        ).set_image(url = user.banner.url)

        await ctx.send(embed = embed, view = view)


    @commands.command(description = "Voir l'icône du serveur ou celui d'un des serveurs du bot")
    @commands.guild_only()
    async def serverpic(self, ctx, server : discord.Guild = None):
        translation = await self.bot.get_translation("serverpic", ctx.guild.id)

        if not server:
            server = ctx.guild
        if not ctx.guild.icon:
            await ctx.send(f"> " + translation["Le serveur [data_server] n'a pas d'icône"].replace("[data_server]", f"**{server.name}**") + ".")
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
        translation = await self.bot.get_translation("serverbanner", ctx.guild.id)
        if not server:
            server = ctx.guild
        if not ctx.guild.banner:
            await ctx.send(f"> " + translation["Le serveur [data_server] n'a pas de bannière"].replace("[data_server]", f"**{server.name}**") + ".")
            return
        
        view = discord.ui.View(timeout = None)
        view.add_item(discord.ui.Button(label = translation["Bannière"], style = discord.ButtonStyle.link, url = server.banner.url))
        embed = discord.Embed(
            title = server.name,
            color = await self.bot.get_theme(ctx.guild.id)
        ).set_image(url = server.banner.url)

        await ctx.send(embed = embed, view = view)


def setup(bot):
    bot.add_cog(Informations(bot))