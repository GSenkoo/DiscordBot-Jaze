import discord
import json
from typing import Union, List
from discord.ext import commands


class GPChecker:
    def __init__(self, ctx, bot):
        self.ctx = ctx
        self.bot = bot

    async def get_owners(self) -> List[int]:
        owners = await self.bot.db.get_data("guild", "owners", guild_id = self.ctx.guild.id)

        if owners: owners = json.loads(owners)
        else: owners = []

        return owners
    

    async def has_higher_hierarchic(self, author : discord.Member, member : discord.Member):
        owners = await self.get_owners()
        if not ((author.id in owners) and ((member.id not in owners) and (member != self.ctx.guild.owner))) or (author == self.ctx.guild.owner):
            if (member.id in owners) or (member == self.ctx.guild.owner):
                return False
            if member.top_role.position >= author.top_role.position:
                return False
        return True

    
    async def we_can_ban(self, user : discord.User, member : Union[discord.Member, None]) -> Union[str, bool]:
        if user == self.ctx.guild.me: return "> Je ne peux pas m'auto-ban."
        if user == self.ctx.author: return "> Vous ne pouvez pas vous auto-bannir du serveur."
        if user == self.ctx.guild.owner: return "> Vous ne pouvez pas bannir le propriétaire du serveur."

        if member:
            if member.top_role.position >= self.ctx.guild.me.top_role.position: return f"> Je ne peux pas bannir {member.mention} car il est suppérieur ou égal à moi hiérarchiquement"
            if not await self.has_higher_hierarchic(self.ctx.author, member): return "> Vous ne pouvez pas bannir un membre qui est suppérieur ou égal à vous hiérarchiquement."
        
        return True

    
    async def we_can_kick(self, member : discord.Member) -> Union[str, bool]:
        if member == self.ctx.guild.me: return "> Je ne peux pas m'auto-kick."
        if member == self.ctx.author: return "> Vous ne pouvez pas vous auto-kick du serveur."
        if member == self.ctx.guild.owner: return "> Vous ne pouvez pas kick le propriétaire du serveur."
        
        if not await self.has_higher_hierarchic(self.ctx.author, member): return "> Vous ne pouvez pas kick un membre qui est suppérieur ou égal à vous hiérarchiquement."
        if member.top_role.position >= self.ctx.guild.me.top_role.position: return f"> Je ne peux pas kick {member.mention} car il est suppérieur ou égal à moi hiérarchiquement"        
        
        return True
    

    async def we_can_tempmute(self, member : discord.Member) -> Union[str, bool]:
        if member.timed_out: return f"> Le membre {member.mention} est déjà tempmute."
        if member == self.ctx.guild.me: return "> Je ne peux pas m'auto-tempmute."
        if member == self.ctx.author: return "> Vous ne pouvez pas vous auto-tempmute."
        if member.guild_permissions.administrator: return "> Vous ne pouvez pas mute un utilisateur administrateur."

        if not await self.has_higher_hierarchic(self.ctx.author, member): return "> Vous ne pouvez pas tempmute un membre qui est suppérieur ou égal à vous hiérarchiquement."
        if member.top_role.position >= self.ctx.guild.me.top_role.position: return "> Je ne peux pas tempmute un utilisateur qui est suppérieur ou égal à moi hiérarchiquement."

        return True
    

    async def we_can_untempmute(self, member : discord.Member) -> Union[str, bool]:
        if member == self.ctx.guild.me: return "> D'après mes propres constats, je ne suis pas tempmute."
        if member == self.ctx.author: return "> D'après discord et ma personne, vous n'êtes pas tempmute."
        if not member.timed_out: return f"> Le membre {member.mention} n'est pas tempmute."

        if not await self.has_higher_hierarchic(self.ctx.author, member): return "> Vous ne pouvez pas untempmute un membre qui est suppérieur ou égal à vous hiérarchiquement."
        if member.top_role.position >= self.ctx.guild.me.top_role.position: return "> Je ne peux pas untempmute un utilisateur qui est suppérieur ou égal à moi hiérarchiquement."

        return True

    
    async def we_can_derank(self, member : discord.Member) -> Union[str, bool]:
        if member == self.ctx.guild.me: return "> Je ne peux pas m'auto-derank."
        if member == self.ctx.author: return "> Vous ne pouvez pas vous auto-derank."
        if member == self.ctx.guild.owner: return "> Le propriétaire du serveur ne peut pas être derank."

        if not await self.has_higher_hierarchic(self.ctx.author, member): return "> Vous ne pouvez pas derank un membre qui est suppérieur ou égal à vous hiérarchiquement."
        if member.top_role.position >= self.ctx.guild.me.top_role.position: return "> Je ne peux pas derank un utilisateur suppérieur ou égal à moi hiérarchiquement."
    
        return True

    
    async def we_can_add_role_to(self, member : discord.Member, role : discord.Role) -> Union[str, bool]:
        if not role.is_assignable(): return f"> Le rôle {role.mention} n'est pas un rôle assignable."
        if role in getattr(member, "roles", []): return "> " + ("Vous avez" if member == self.ctx.author else f"{member.mention} a") + f" déjà le rôle {role.mention}."
        
        if not await self.has_higher_hierarchic(self.ctx.author, member): return "> Vous ne pouvez pas ajouter des rôles à un membre qui est suppérieur ou égal à vous hiérarchiquement."
        if role.position >= self.ctx.guild.me.top_role.position: return "> Je ne peux pas ajouter un rôle qui est suppérieur ou égal hiérarchiquement à mon rôle le plus élevé."

        return True
    

    async def we_can_add_role(self, role : discord.Role) -> Union[str, bool]:
        if not role.is_assignable(): return f"> Le rôle {role.mention} n'est pas un rôle assignable."        
        if role.position >= self.ctx.guild.me.top_role.position: return "> Je ne peux pas ajouter un rôle qui est suppérieur ou égal hiérarchiquement à mon rôle le plus élevé."

        return True


    async def we_can_remove_role(self, member : discord.Member, role : discord.Role) -> Union[str, bool]:
        if role not in getattr(member, "roles", []): return "> " + ("Vous n'avez" if member == self.ctx.author else f"{member.mention} n'a") + f" pas le rôle {role.mention}."
        if not role.is_assignable(): return f"> Le rôle {role.mention} ne peut pas être retiré."

        if not await self.has_higher_hierarchic(self.ctx.author, member): return "> Vous ne pouvez pas retirer un rôle à un membre qui est suppérieur ou égal à vous hiérarchiquement."
        if role.position >= self.ctx.guild.me.top_role.position: return "> Je ne peux pas retirer un rôle qui est suppérieur ou égal hiérarchiquement à mon rôle le plus élevé."

        return True


    async def we_can_warn(self, member : discord.Member) -> Union[str, bool]:
        if member == self.ctx.guild.me: return "> Je ne peux pas m'auto-warn."
        if member.bot: return "> Vous ne pouvez pas warn un bot."
        if member == self.ctx.author: return "> Vous ne pouvez pas vous auto-warn."
        if member == self.ctx.guild.owner: return "> Vous ne pouvez pas warn le propriétaire du serveur."

        if not await self.has_higher_hierarchic(self.ctx.author, member): return "> Vous ne pouvez pas warn un membre qui est suppérieur ou égal à vous hiérarchiquement."

        return True
    
    
    async def we_can_blrank(self, member : discord.Member, action : str) -> Union[str, bool]:
        assert action in ["add", "del"]

        if member == self.ctx.guild.me: return "> Je ne peux pas m'auto blrank."
        if member == self.ctx.author: return "> Vous ne pouvez pas vous auto-blrank."
        if member == self.ctx.guild.owner: return "> Vous ne pouvez pas blrank le propriétaire du serveur."

        blrank_users = await self.bot.db.get_data("guild", "blrank_users", True, guild_id = self.ctx.guild.id)

        if not self.has_higher_hierarchic(self.ctx.author, member): return f"> Vous n'êtes pas assez haut placé hiérarchiquement pour gérer {member.mention}."        

        if (member.id in blrank_users) and (action == "add"): return f"> Le membre {member.mention} a déjà été blrank."
        if (member.id not in blrank_users) and (action == "del"): return f"> Le membre {member.mention} n'a pas été blrank."

        return True
    
    async def we_can_blvoc(self, member : discord.Member, action : str) -> Union[str, bool]:
        assert action in ["add", "del"]

        if member == self.ctx.guild.me: return "> Je ne peux pas m'auto blvoc."
        if member == self.ctx.author: return "> Vous ne pouvez pas vous auto-blvoc."
        if member == self.ctx.guild.owner: return "> Vous ne pouvez pa blvoc le propriétaire du serveur."

        blvoc_users = await self.bot.db.get_data("guild", "blvoc_users", True, guild_id = self.ctx.guild.id)

        if not self.has_higher_hierarchic(self.ctx.author, member): return f"> Vous n'êtes pas assez haut placé hiérarchiquement pour gérer {member.mention}."        

        if (member.id in blvoc_users) and (action == "add"): return f"> Le membre {member.mention} a déjà été blvoc."
        if (member.id not in blvoc_users) and (action == "del"): return f"> Le membre {member.mention} n'a pas été blvoc."

        return True