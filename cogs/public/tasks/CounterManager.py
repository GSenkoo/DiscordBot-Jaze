import discord
import asyncio
import random
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from utils import Tools


class CounterManager(commands.Cog):
    """
    Le format de la table d'un salon compteur : 
        "counter": {
            "primary_keys": {"guild_id": "BIGINT NOT NULL", "name": "VARCHAR(80) NOT NULL"},
            "keys": {
                "enabled":"BOOLEAN",
                "text": "VARCHAR(100)",
                "channel": "BIGINT",
                "update_frequency": "VARCHAR(3)",
                "last_update": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
        }
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.counter_updater.start()

    def cog_unload(self):
        self.counter_updater.cancel()


    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(2) # Attendre pour être sûr que la base de donnée ait le temps de s'intialiser

        # -------------------------------- Mise à jour des colonnes "last_update" des salons compteurs de manière aléatoire
        # Pour éviter que les salons se mettents tous à jour à un même moment (exemple : au démarrage, s'il y'a trop de salons qui doivent être mis à jour, le bot risque de se faire rate-limit)
        counter_table_columns = await self.bot.db.get_table_columns("counter")
        channels_counter = await self.bot.db.execute(f"SELECT * FROM counter WHERE last_update < CURRENT_TIMESTAMP AND enabled = True", fetch = True)

        for channel_counter in channels_counter:
            channel_counter_data = dict(zip(counter_table_columns, channel_counter))
            random_last_update = datetime.now() + timedelta(seconds = random.randint(-300, 0))
            await self.bot.db.set_data("counter", "last_update", random_last_update.strftime("%Y-%m-%d %H:%M:%S"), guild_id = channel_counter_data["guild_id"], name = channel_counter_data["name"])


    @tasks.loop(seconds = 2.5)
    async def counter_updater(self):
        # -------------------------------- Récupérer les salons qui doivent être mis à jour
        counters_to_update = []
        counter_table_columns = await self.bot.db.get_table_columns("counter")
        for time, time_type in [(5, "m"), (10, "m"), (30, "m"), (1, "h"), (3, "h")]:
            last_update = datetime.now() - timedelta(minutes = time if time_type == "m" else 0, hours = time if time_type == "h" else 0)
            counters_found = await self.bot.db.execute(
                f"SELECT * FROM counter WHERE enabled = true AND last_update < %s AND update_frequency = '{time}{time_type}'",
                data = (last_update.strftime("%Y-%m-%d %H:%M:%S"),),
                fetch = True
            )
            for counter in counters_found:
                counters_to_update.append(dict(zip(counter_table_columns, counter)))


        tools = Tools(self.bot)
        guilds_vars = {} # Pour sauvegarder les valeurs des variables de serveur (au cas où il y'a plusieurs salons compteur sur un même serveur)
        for counter_data in counters_to_update:
            # -------------------------------- Récupération du serveur
            guild = self.bot.get_guild(counter_data["guild_id"])
            if not guild:
                continue

            # -------------------------------- Récupération des valeurs des variables du serveur
            if guild.id not in guilds_vars.keys():
                guild_vars = tools.get_guild_vars_dict(guild)
                guilds_vars[guild.id] = guild_vars
            else:
                guild_vars = guilds_vars[guild.id]

            # -------------------------------- Récupération du salon
            channel = guild.get_channel(counter_data["channel"])
            if not channel:
                try: channel = await guild.fetch_channel(counter_data["channel"])
                except:
                    return
            
            # -------------------------------- Mise à jour du salon
            try:
                text = tools.multiple_replaces(counter_data["text"], guild_vars)
                await channel.edit(name = text if len(text) <= 100 else text[:97] + "...")
                await self.bot.db.set_data("counter", "last_update", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), guild_id = counter_data["guild_id"], name = counter_data["name"])
            except:
                pass


    @counter_updater.before_loop
    async def before_counter_updater(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)


def setup(bot):
    bot.add_cog(CounterManager(bot))