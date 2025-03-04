import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.config import PREFIX

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set!")

# Initialize bot with required intents
intents = discord.Intents.default()
intents.message_content = True  # Required for commands
intents.members = True  # Required for member operations
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Load cogs
async def load_extensions():
    """Load all cog extensions"""
    await bot.load_extension("cogs.economy")
    await bot.load_extension("cogs.admin")
    # Removed Minecraft cog loading

@bot.event
async def on_ready():
    """Called when bot is ready and connected"""
    await load_extensions()
    print(f'{bot.user} has connected to Discord!')
    try:
        await bot.tree.sync()  # Sync slash commands
        print("Successfully synced application commands")
    except discord.errors.HTTPException as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands"""
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('❌ У вас нет прав для выполнения этой команды.')
    elif isinstance(error, commands.errors.CommandNotFound):
        await ctx.send('❌ Команда не найдена.')
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.send('❌ У вас недостаточно прав для выполнения этой команды.')
    elif isinstance(error, commands.errors.UserNotFound):
        await ctx.send('❌ Пользователь не найден.')
    else:
        await ctx.send(f'❌ Произошла ошибка: {str(error)}')
        print(f"Error occurred: {error}")

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Failed to login: Invalid token")
    except Exception as e:
        print(f"An error occurred: {e}")