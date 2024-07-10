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
from discord.ext import commands
from utils.Database import Database

class MartialBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db = None
        self.colors_save = {}
        self.langages_save = {}
        self.prefixes_save = {}

    
    async def create_db(self):
        database = Database()
        await database.create_pool()
        self.db = database
    
    async def set_theme(self, guild_id : int, theme : int):
        if guild_id in self.colors_save:
            self.colors_save[guild_id] = theme

        await self.db.set_data("guild", "theme", theme, guild_id = guild_id)


    async def get_theme(self, guild_id : int):
        if str(guild_id) in self.colors_save.keys():
            return self.colors_save[str(guild_id)]
    
        theme = await self.db.get_data(table = "guild", column = "theme", guild_id = guild_id)

        self.colors_save[str(guild_id)] = int(theme)
        return int(theme)


    async def get_translations_langage(self, guild_id : int):
        if str(guild_id) in self.langages_save:
            return self.langages_save[str(guild_id)]

        langage = await self.db.get_data("guild", "langage", guild_id = guild_id)
        return langage


    async def get_translation(self, translation_key : str, guild_id : int):
        langage = await self.get_translations_langage(guild_id)

        with open(f"translations/{langage}.json", encoding = "utf-8") as file:
            translation_data = json.load(file)
        
        return translation_data[translation_key]
    

    async def set_prefix(self, guild_id : int, new_prefix : str):
        if str(guild_id) in self.prefixes_save.keys():
            self.prefixes_save[str(guild_id)] = new_prefix

        await self.db.set_data("guild", "prefix", new_prefix, guild_id = guild_id)


    async def get_prefix(self, message: discord.Message) -> list[str] | str:
        if str(message.guild.id) in self.prefixes_save.keys():
            return self.prefixes_save[str(message.guild.id)]
        
        current_prefix = await self.db.get_data("guild", "prefix", guild_id = message.guild.id)

        self.prefixes_save[str(message.guild.id)] = current_prefix
        return current_prefix