import discord
from discord import app_commands
from utils.database import get_db, ServiceLevel
from utils.config import ERRORS

def get_user_permission_level(member: discord.Member) -> int:
    """Calculate user's permission level based on their roles"""
    # Default level for everyone
    default_level = 0

    # Admin gets highest level
    if member.guild_permissions.administrator:
        return 3

    # Check other roles
    if any(role.permissions.manage_guild for role in member.roles):
        return 2

    if any(role.permissions.manage_messages for role in member.roles):
        return 1

    return default_level

def has_command_permission(command_name: str):
    """Decorator to check command permissions"""
    async def predicate(interaction: discord.Interaction):
        # Admin always has access
        if interaction.user.guild_permissions.administrator:
            return True

        # Get user's permission level
        user_level = get_user_permission_level(interaction.user)

        # Commands requiring admin (level 3)
        admin_commands = ['admin_set', 'admin_reset', 'set_currency', 'add_level', 'edit_level', 'remove_level']
        if command_name in admin_commands and user_level < 3:
            await interaction.response.send_message(
                ERRORS['NO_PERMISSION'],
                ephemeral=True
            )
            return False

        # Commands requiring moderator (level 2)
        mod_commands = ['mute', 'unmute', 'kick']
        if command_name in mod_commands and user_level < 2:
            await interaction.response.send_message(
                ERRORS['NO_PERMISSION'],
                ephemeral=True
            )
            return False

        # Commands requiring helper (level 1)
        helper_commands = ['warn', 'unwarn']
        if command_name in helper_commands and user_level < 1:
            await interaction.response.send_message(
                ERRORS['NO_PERMISSION'],
                ephemeral=True
            )
            return False

        return True

    return app_commands.check(predicate)