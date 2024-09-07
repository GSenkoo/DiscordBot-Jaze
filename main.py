import discord
import os

from dotenv import load_dotenv
from discord.ext import commands

from utils import manage_files
from utils import PermissionsManager
from utils import CustomHelp
from utils import Jaze


bot = Jaze(command_prefix = "+", intents = discord.Intents.all(), help_command = CustomHelp())

@bot.check
async def can_use_cmd(ctx):
    permission_manager = PermissionsManager(ctx.bot)
    return await permission_manager.can_use_cmd(ctx)

manage_files(bot, "load")
load_dotenv()
bot.run(token = os.getenv("TOKEN"))