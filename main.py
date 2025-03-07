import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.config import PREFIX
from utils.database import Base, engine  # Import database components
from sqlalchemy import inspect
import sys

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set!")

# Initialize database tables
print("Creating database tables...", file=sys.stderr)
try:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    print("Created tables:", table_names, file=sys.stderr)
    print("Database tables created successfully!", file=sys.stderr)
except Exception as e:
    print(f"Failed to create database tables: {e}", file=sys.stderr)
    raise

# Initialize bot with required intents
intents = discord.Intents.default()
intents.message_content = True  # Required for commands
intents.members = True  # Required for member operations
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Load cogs
async def load_extensions():
    """Load all cog extensions"""
    try:
        print("Loading economy cog...")
        await bot.load_extension("cogs.economy")
        print("Loading admin cog...")
        await bot.load_extension("cogs.admin")
        print("All cogs loaded successfully")
    except Exception as e:
        print(f"Error loading cogs: {e}", file=sys.stderr)
        raise  # Re-raise to handle in on_ready

@bot.event
async def on_ready():
    """Called when bot is ready and connected"""
    print(f'{bot.user} has connected to Discord!')
    try:
        await load_extensions()
        print("Attempting to sync application commands...")
        await bot.tree.sync()
        print("Successfully synced application commands")
        print("Bot is fully ready!")
    except Exception as e:
        print(f"An error occurred during setup: {e}", file=sys.stderr)
        return  # Exit early if setup fails

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands"""
    print(f"Command error occurred: {type(error).__name__} - {str(error)}", file=sys.stderr)

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

if __name__ == "__main__":
    try:
        print("Starting bot...", file=sys.stderr)
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Failed to login: Invalid token", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)