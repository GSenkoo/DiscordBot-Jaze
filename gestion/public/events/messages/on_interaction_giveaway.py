import discord
import asyncio
import json
import random
from datetime import datetime
from discord.ext import commands, tasks


class on_interaction_giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaway_loop.start()

# -------------------------- Giveaway participations events

    @commands.Cog.listener()
    async def on_interaction(self, interaction : discord.Interaction):
        if interaction.custom_id != "giveaway":
            return
        
        await interaction.response.send_message("> Fonctionnel.", ephemeral = True)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        message = reaction.message

# -------------------------- Giveaway check end_at tasks

    def cog_unload(self):
        self.giveaway_loop.cancel()

    @tasks.loop(seconds = 5)
    async def giveaway_loop(self):
        giveaways_to_end = await self.bot.db.execute("SELECT * FROM giveaway WHERE end_at < CURRENT_TIMESTAMP", fetch = True)
        
        if not giveaways_to_end:
            return
        
        giveaway_table_columns = await self.bot.db.get_table_columns("giveaway")
        giveaways = []
        for giveaway in giveaways_to_end:
            giveaways.append(zip(giveaway_table_columns, giveaway))
        giveaways = [set(data) for data in giveaways]

        for giveaway in giveaways:
            try:
                guild : discord.Guild = await self.bot.fetch_guild(giveaway["guild_id"])
                channel : discord.TextChannel = await self.bot.fetch_channel(giveaway["channel_id"])
                message : discord.Message = await channel.fetch_message(giveaway["message_id"])
            except discord.NotFound:
                await self.bot.db.execute("DELETE FROM TABLE WHERE guild_id = %s AND channel = %s AND message = %s", (giveaway["guild_id"], giveaway["channel_id"], giveaway["message_id"]))
                continue
            except Exception as e:
                print(e)
                continue
            
            if giveaway["interaction_type"] == "button":
                await message.edit(view = None)
                participants = json.loads(giveaway["participations"])
            else:
                reaction = None
                for reaction in message.reactions:
                    if reaction.emoji == giveaway["emoji"]:
                        reaction = reaction
                
                if not reaction:
                    await self.bot.db.execute("DELETE FROM TABLE WHERE guild_id = %s AND channel = %s AND message = %s", (giveaway["guild_id"], giveaway["channel_id"], giveaway["message_id"]))
                    participants = []
                else:
                    participants = await reaction.users().flatten()

            winners = []
            if not participants:
                await message.reply("> Giveaway terminé, aucun gagnant. Il n'y a pas eu de participants.")
            else:
                if (giveaway["winners_count"] == 1) or (giveaway["imposed_winner"]):
                    await message.reply(f"> Giveaway terminé, le gagnant du giveaway est {random.choice(participants).mention if not giveaway["imposed_winner"] else giveaway["imposed_winner"]}.")
                else:
                    if giveaways["winners_counts"] >= len(participants):
                        winners = [f"{participant.mention}" for participant in participants]
                    else:
                        for i in range(giveaway["winners_count"]):
                            winner = random.choice(participants)
                            participants.remove(winner)
                            winners.append(winner.mention)

                    await message.reply(f"> Giveaway terminé, les gagnants du giveaway sont {', '.join(winners[:-2])} et {winners[-1]}.")
            
            message_embed = message.embeds[0]
            message_embed.description = "Gagnant" + ("s" if len(winners) > 1 else "") + " : " + (", ".join(winners) if winners else "*Aucun gagnant*")

            await message.edit(
                embed = message_embed,
                view = None
            )



    @giveaway_loop.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5) # Pour s'assurer que la base de donnée ai le temps de s'initialiser


def setup(bot):
    bot.add_cog(on_interaction_giveaway(bot))