from discord.ext import commands
import json
import os

def check_admin():
    """Decorator to check if user has admin permissions"""
    async def predicate(ctx):
        if not ctx.guild:
            return False
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

def check_minecraft_linked():
    """Decorator to check if user has linked Minecraft account"""
    async def predicate(ctx):
        storage_path = 'data/minecraft.json'
        if not os.path.exists(storage_path):
            return False
            
        with open(storage_path, 'r') as f:
            data = json.load(f)
            return str(ctx.author.id) in data.get('linked_accounts', {})
    return commands.check(predicate)
