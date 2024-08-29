import discord
import asyncio
import json
import random

from datetime import datetime, timedelta
from discord.ext import commands, tasks


"""
"primary_keys": {"guild_id": "BIGINT NOT NULL", "channel_id": "BIGINT NOT NULL", "message_id": "BIGINT NOT NULL UNIQUE"},
"keys": {
    "reward": "VARCHAR(255) DEFAULT 'Acune récompense'",
    "end_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "channel": "BIGINT DEFAULT 0",
    "emoji": "VARCHAR(10)",
    "interaction_type": "VARCHAR(10) DEFAULT 'reaction'",
    "button_color": "VARCHAR(10) DEFAULT 'blue'",
    "button_text": "VARCHAR(80) DEFAULT 'Participer'",
    "winners_count": "INTEGER DEFAULT 1",
    "participations": "MEDIUMTEXT",
    "required_role": "BIGINT DEFAULT 0",
    "prohibited_role": "BIGINT DEFAULT 0",
    "in_vocal_required": "BOOLEAN DEFAULT 0"
}
"""


class on_interaction_giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaway_loop.start()
        self.giveaway_auto_delete_loop.start()
        self.update_task_enabled_messages = []


        async def check_condition(giveaway : dict, user, guild, is_dm = False):
            member = await guild.fetch_member(user.id)
            user_roles_ids = [role.id for role in member.roles]

            giveaway_link = f"[Giveaway {giveaway['reward']}](https://discord.com/channels/{giveaway['guild_id']}/{giveaway['channel_id']}/{giveaway['message_id']})"

            role = None
            if (giveaway["required_role"]) and (giveaway["required_role"] not in user_roles_ids):
                if is_dm: role = guild.get_role(giveaway["required_role"])
                return f"> Vous ne pouvez pas participer au {giveaway_link} car vous n'avez pas le rôle " + (f"<@&{giveaway['required_role']}>" if not is_dm else f"**@{role.name}**") + "."

            elif giveaway["prohibited_role"] in user_roles_ids:
                if is_dm: role = guild.get_role(giveaway["prohibited_role"])
                return f"> Vous ne pouvez pas participer au {giveaway_link} car vous avez le rôle interdit " + (f"<@&{giveaway['prohibited_role']}>" if not is_dm else f"**@{role.name}**") + "."

            elif giveaway["in_vocal_required"]:
                if not member.voice:
                    return f"> Vous ne pouvez pas participer au {giveaway_link} sans être en vocal dans le serveur."
            
        self.check_condition = check_condition
        self.action = True

# -------------------------- Giveaway participations events

    @commands.Cog.listener()
    async def on_interaction(self, interaction : discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        if interaction.custom_id != "giveaway":
            return
        
        current_giveaway = await self.bot.db.execute(f"SELECT * FROM giveaway WHERE message_id = {interaction.message.id} AND end_at > CURRENT_TIMESTAMP AND ended = false", fetch = True)
        if not current_giveaway:
            await interaction.response.send_message("> Les données de ce giveaway ne sont plus disponibles.", ephemeral = True)
            return
    
        giveaway = dict(zip(await self.bot.db.get_table_columns("giveaway"), current_giveaway[0]))
        participations = json.loads(giveaway["participations"])
        if interaction.user.id in participations:
            participations.remove(interaction.user.id)
            await self.bot.db.set_data("giveaway", "participations", json.dumps(participations), guild_id = interaction.guild.id, channel_id = interaction.channel.id, message_id = interaction.message.id)
            await interaction.response.send_message("> Votre participation a bien été retirée.", ephemeral = True)
        else:
            check = await self.check_condition(giveaway, interaction.user, interaction.guild)
            if check:
                await interaction.response.send_message(check, ephemeral = True)
                return
            
            participations.append(interaction.user.id)
            await self.bot.db.set_data("giveaway", "participations", json.dumps(participations), guild_id = interaction.guild.id, channel_id = interaction.channel.id, message_id = interaction.message.id)
            await interaction.response.send_message("> Votre participation a bien été prise en compte.", ephemeral = True)

        if interaction.message.id not in self.update_task_enabled_messages: # Pour vérifier si une boucle (qui s'exécute toutes les 5 secondes) qui met à jours le message est en action, sinon, en lancer une nouvelle.
            self.update_task_enabled_messages.append(interaction.message.id)
            
            previous_participant = 0
            while (datetime.now().timestamp() - giveaway["end_at"].timestamp() <= 5) and (self.action):
                participations = await self.bot.db.get_data("giveaway", "participations", True, guild_id = interaction.guild.id, channel_id = interaction.channel.id, message_id = interaction.message.id)
                
                ended = await self.bot.db.get_data("giveaway", "ended", guild_id = interaction.guild.id, channel_id = interaction.channel.id, message_id = interaction.message.id)
                if ended:
                    break

                if previous_participant != len(participations):
                    message_embed = interaction.message.embeds[0]
                    message_embed.set_footer(text = f"{len(participations)} participants")
                    try: await interaction.message.edit(embed = message_embed)
                    except: pass
                previous_participant = len(participations)
            
                await asyncio.sleep(5)



    @commands.Cog.listener()
    async def on_reaction_add(self, reaction : discord.Reaction, user : discord.User):
        if not reaction.message.guild:
            return
        
        current_giveaway = await self.bot.db.execute(f"SELECT * FROM giveaway WHERE message_id = {reaction.message.id} AND end_at > CURRENT_TIMESTAMP AND ended = false", fetch = True)
        if not current_giveaway:
            return
    
        giveaway = dict(zip(await self.bot.db.get_table_columns("giveaway"), current_giveaway[0]))
        if (giveaway["interaction_type"] != "reaction") or (reaction.emoji != giveaway["emoji"]):
            return
        
        async def send_dm(message):
            try: await user.send(message)
            except: pass

        check = await self.check_condition(giveaway, user, reaction.message.guild, True)
        if check:
            await reaction.remove(user)
            await send_dm(check)


# -------------------------- Giveaway check end_at tasks

    def cog_unload(self):
        self.giveaway_loop.cancel()
        self.giveaway_auto_delete_loop.cancel()
        self.action = False

    @tasks.loop(seconds = 5)
    async def giveaway_loop(self):
        giveaways_to_end = await self.bot.db.execute("SELECT * FROM giveaway WHERE end_at < CURRENT_TIMESTAMP AND ended = false", fetch = True)
        
        if not giveaways_to_end:
            return
        
        giveaway_table_columns = await self.bot.db.get_table_columns("giveaway")
        giveaways = [dict(zip(giveaway_table_columns, giveaway)) for giveaway in giveaways_to_end]
        
        for giveaway in giveaways:
            message : discord.Message = self.bot.get_message(giveaway["message_id"])
            if not message:
                try:
                    guild : discord.Guild = await self.bot.fetch_guild(giveaway["guild_id"])
                    channel : discord.TextChannel = guild.get_channel(giveaway["channel_id"])

                    if not channel: raise ValueError()

                    message : discord.Message = await channel.fetch_message(giveaway["message_id"])
                except:
                    await self.bot.db.execute("DELETE FROM giveaway WHERE guild_id = %s AND channel_id = %s AND message_id = %s", (giveaway["guild_id"], giveaway["channel_id"], giveaway["message_id"]))
                    continue

            if giveaway["interaction_type"] == "button":
                await message.edit(view = None)
                participants = json.loads(giveaway["participations"])
            else:
                reaction = None
                for reaction in message.reactions:
                    if reaction.emoji == giveaway["emoji"]:
                        reaction = reaction
                if reaction:
                    participants = []
                    async for user in reaction.users():
                        if user.bot: continue
                        participants.append(user.id)

            winners = []
            participants_save = participants.copy()
            if not participants:
                await message.reply("> Giveaway terminé, aucun gagnant. Il n'y a pas eu de participants.")
                await self.bot.db.execute("DELETE FROM giveaway WHERE guild_id = %s AND channel_id = %s AND message_id = %s", (giveaway["guild_id"], giveaway["channel_id"], giveaway["message_id"]))
            else:
                if (giveaway["winners_count"] == 1) or (len(participants) == 1):
                    winners.append("<@" + str(random.choice(participants)) + ">")
                    await message.reply(f"> Giveaway terminé, le gagnant du giveaway **{giveaway['reward']}** est {winners[0]}.")
                else:
                    if giveaway["winners_count"] >= len(participants):
                        winners.append(f"<@{participant}>" for participant in participants)
                    else:
                        for i in range(giveaway["winners_count"]):
                            winner = random.choice(participants)
                            participants.remove(winner)
                            winners.append(f"<@{winner}>")

                    await message.reply(f"> Giveaway terminé, les gagnants du giveaway **{giveaway['reward']}** sont {', '.join(winners[:-1])} et {winners[-1]}.")
            
            message_embed = message.embeds[0]
            message_embed.description = "Gagnant" + ("s" if len(winners) > 1 else "") + " : " + (", ".join([winner for winner in winners]) if winners else "*Aucun gagnant*")
            message_embed.fields[0].value = f"<t:{round(giveaway['end_at'].timestamp())}:R>"
            
            if participants:
                await self.bot.db.set_data("giveaway", "ended", True, guild_id = message.guild.id, channel_id = message.channel.id, message_id = message.id)
                
                # Pour sauvegarder les participants (j'utilise ça pour sauvegarder les données des participants ayant réagi avec intéraction, puisque sinon, on pourra participer même après la fin du giveaway si celui-ci est reroll)
                await self.bot.db.set_data("giveaway", "participations", json.dumps(participants_save), guild_id = message.guild.id, channel_id = message.channel.id, message_id = message.id)
                
            await message.edit(
                embed = message_embed,
                view = None
            )


    @tasks.loop(seconds = 1200)
    async def giveaway_auto_delete_loop(self):
        date = datetime.now() - timedelta(hours = 24)
        await self.bot.db.execute("DELETE FROM giveaway WHERE end_at < %s", (date,))

    @giveaway_auto_delete_loop.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)

    @giveaway_loop.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5) # Pour s'assurer que la base de donnée ai le temps de s'initialiser


def setup(bot):
    bot.add_cog(on_interaction_giveaway(bot))