import discord
from discord import app_commands
from .config import REQUIRED_ROLES, PERMISSION_LEVELS, ERRORS, COMMAND_PERMISSIONS

def get_user_permission_level(member: discord.Member) -> int:
    """Calculate user's permission level based on their roles"""
    user_roles = [role.name for role in member.roles]
    user_level = PERMISSION_LEVELS['DEFAULT']

    for role_name, level in PERMISSION_LEVELS.items():
        if REQUIRED_ROLES[role_name] in user_roles:
            user_level = max(user_level, level)

    return user_level

def check_command_permission(command_name: str, member: discord.Member) -> bool:
    """Check if user has permission to use a command"""
    if command_name not in COMMAND_PERMISSIONS:
        return False

    permission = COMMAND_PERMISSIONS[command_name]
    user_level = get_user_permission_level(member)

    # Check permission level
    if user_level >= permission['level']:
        return True

    # Check specific roles
    user_roles = [role.name for role in member.roles]
    for role_name in permission['roles']:
        if REQUIRED_ROLES[role_name] in user_roles:
            return True

    return False

def has_command_permission(command_name: str):
    """Decorator to check command permissions"""
    async def predicate(interaction: discord.Interaction):
        if check_command_permission(command_name, interaction.user):
            return True

        await interaction.response.send_message(
            ERRORS['NO_PERMISSION'],
            ephemeral=True
        )
        return False

    return app_commands.check(predicate)

def set_command_permission(command_name: str, level: int, roles: list[str]) -> bool:
    """Set permission requirements for a command"""
    if command_name not in COMMAND_PERMISSIONS:
        return False

    if level < 0 or level > max(PERMISSION_LEVELS.values()):
        return False

    # Validate roles
    for role in roles:
        if role not in REQUIRED_ROLES:
            return False

    COMMAND_PERMISSIONS[command_name] = {
        'level': level,
        'roles': roles
    }
    return True

def get_command_permission(command_name: str) -> dict:
    """Get permission settings for a command"""
    return COMMAND_PERMISSIONS.get(command_name, {
        'level': 0,
        'roles': []
    })