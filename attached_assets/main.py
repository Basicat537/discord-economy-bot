import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.config import PREFIX

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize bot with minimal required intents
intents = discord.Intents.default()
intents.message_content = True  # Required for commands
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Load cogs
async def load_extensions():
    await bot.load_extension("cogs.economy")
    await bot.load_extension("cogs.admin")

@bot.event
async def on_ready():
    await load_extensions()
    print(f'{bot.user} has connected to Discord!')
    await bot.tree.sync()  # Sync slash commands

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('❌ У вас нет прав для выполнения этой команды.')
    elif isinstance(error, commands.errors.CommandNotFound):
        await ctx.send('❌ Команда не найдена.')
    else:
        await ctx.send(f'❌ Произошла ошибка: {str(error)}')

# Run the bot
bot.run(TOKEN)