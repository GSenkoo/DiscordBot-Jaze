import discord
import asyncio
import random
from .functions import get_pfc_embed

rules = {
    "pierre": "ciseaux",
    "papier": "pierre",
    "ciseaux": "papier"
}

emojis = {
    "pierre": "🪨",
    "papier": "📄",
    "ciseaux": "✂️"
}

class ChifumiGame(discord.ui.View):
    def __init__(self, ctx, bot, member):
        super().__init__(timeout = 30)
        self.ctx = ctx
        self.bot = bot
        self.member = member

        self.author_pts = 0
        self.oponent_pts = 0
        self.choosing = ctx.author
        self.move = None
        self.oponent_move = None
        

    async def on_timeout(self):
        try:
            await self.message.edit(
                view = None,
                embed = discord.Embed(
                    title = "Partie pfc",
                    description = f"*{self.choosing.display_name} a été déclaré forfait pour inactivité.*",
                    color = await self.bot.get_theme(self.ctx.guild.id)
                )
            )
        except: pass
    
    @discord.ui.select(
        placeholder = "Choisir une action",
        options = [
            discord.SelectOption(label = move_name.capitalize(), emoji = move_emoji, value = move_name) for move_name, move_emoji in emojis.items()
        ]
    )
    async def make_choice_select(self, select, interaction):
        if interaction.user != self.ctx.author and interaction.user != self.member:
            await interaction.response.send_message("> Vous n'êtes pas autorisés à intéragir avec ceci.", ephemeral = True)
            return
        if self.choosing != interaction.user:
            await interaction.response.send_message("> Merci de patienter, ce n'est pas encore à vous de jouer.", ephemeral = True)
            return                

        if interaction.user == self.ctx.author:
            self.choosing = self.ctx.guild.me if not self.member else self.member
            await interaction.edit(embed = await get_pfc_embed(self.ctx, self.bot, self.member, self.author_pts, self.oponent_pts, self.choosing))
            self.move = select.values[0]

            if not self.member:
                await asyncio.sleep(random.randint(1, 3))
                self.oponent_move = random.choice(["pierre", "papier", "ciseaux"])
            else: return
        else:
            self.oponent_move = select.values[0]


        if rules[self.move] == self.oponent_move: self.author_pts += 1
        elif self.move == self.oponent_move: pass
        else: self.oponent_pts += 1

        self.choosing = self.ctx.author

        if 3 in [self.oponent_pts, self.author_pts]:
            await interaction.edit(embed = await get_pfc_embed(self.ctx, self.bot, self.member, self.author_pts, self.oponent_pts, self.choosing, self.move, self.oponent_move), view = None)
            self.on_timeout = lambda: ()
            return
        
        await interaction.edit(embed = await get_pfc_embed(self.ctx, self.bot, self.member, self.author_pts, self.oponent_pts, self.choosing, self.move, self.oponent_move))
