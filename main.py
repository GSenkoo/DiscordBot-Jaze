import discord
import os

from dotenv import load_dotenv
from discord.ext import commands
from utils.FilesManager import manage_files
from utils.PermissionsManager import PermissionsManager
from utils.HelpCommand import CustomHelp
from utils.MartialBot import MartialBot


bot = MartialBot(command_prefix = "+", intents = discord.Intents.all(), help_command = CustomHelp())
@bot.check
async def can_use_cmd(ctx):
    permission_manager = PermissionsManager()
    return await permission_manager.can_use_cmd(ctx, bot)

manage_files(bot, "load")

load_dotenv()
bot.run(token = os.getenv("TOKEN"))