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

        self.colors_save = {}
        self.langages_save = {}


    async def get_theme(self, guild_id : int):
        if guild_id in self.colors_save.keys():
            return self.colors_save[guild_id]
        
        database = Database()
        try:
            await database.connect()
            theme = await database.get_data(table = "guild", column = "theme", guild_id = guild_id)
        finally: await database.disconnect()
        self.colors_save[guild_id] = int(theme)

        return int(theme)


    async def get_translations_langage(self, guild_id : int):
        if guild_id in self.langages_save:
            return self.langages_save[guild_id]
        
        database = Database()
        try:
            await database.connect()
            langage = await database.get_data("guild", "langage", guild_id = guild_id)
        finally: await database.disconnect()

        return langage


    async def get_translation(self, translation_key : str, guild_id : int):
        langage = await self.get_translations_langages(guild_id)

        with open(f"translations/{langage}.json", encoding = "utf-8") as file:
            translation_data = json.load(file)
        
        return translation_data[translation_key]