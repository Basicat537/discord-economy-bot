import discord
from discord.ext import commands
from discord import app_commands
from utils.config import DEFAULT_BALANCE, ERRORS, CURRENCY, PERMISSION_LEVELS, REQUIRED_ROLES
from utils.permissions import has_command_permission, set_command_permission, get_command_permission

class Admin(commands.Cog):
    """Admin commands implementation"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name='admin_set',
        description='Установить баланс пользователя (для администраторов)'
    )
    @app_commands.describe(
        user='Пользователь',
        amount='Новый баланс'
    )
    @has_command_permission('admin_set')
    async def set_balance(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        amount: int
    ):
        """Set user balance (admin only)"""
        if amount < 0:
            await interaction.response.send_message(
                '❌ Баланс не может быть отрицательным',
                ephemeral=True
            )
            return

        economy_cog = self.bot.get_cog('Economy')
        if not economy_cog:
            await interaction.response.send_message(
                ERRORS['ECONOMY_MODULE_ERROR'],
                ephemeral=True
            )
            return

        old_balance = economy_cog.get_balance(user.id)
        economy_cog.accounts[user.id] = amount

        embed = discord.Embed(title="Изменение баланса", color=discord.Color.blue())
        embed.add_field(name="Пользователь", value=user.name, inline=True)
        embed.add_field(
            name="Старый баланс",
            value=CURRENCY['FORMAT'].format(
                amount=old_balance,
                currency=CURRENCY['NAME']
            ),
            inline=True
        )
        embed.add_field(
            name="Новый баланс",
            value=CURRENCY['FORMAT'].format(
                amount=amount,
                currency=CURRENCY['NAME']
            ),
            inline=True
        )
        embed.set_footer(text=f"Изменено администратором: {interaction.user.name}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name='set_permission',
        description='Установить права доступа для команды'
    )
    @app_commands.describe(
        command='Название команды',
        level='Уровень прав доступа (0-3)',
        roles='Список ролей через запятую (например: ADMIN,MODERATOR)'
    )
    @has_command_permission('set_command_permission')
    async def set_permission(
        self,
        interaction: discord.Interaction,
        command: str,
        level: int,
        roles: str = ""
    ):
        """Set permission requirements for a command"""
        role_list = [r.strip() for r in roles.split(',')] if roles else []

        if not set_command_permission(command, level, role_list):
            await interaction.response.send_message(
                ERRORS['INVALID_PERMISSION_LEVEL'],
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Права доступа обновлены",
            color=discord.Color.green()
        )
        embed.add_field(name="Команда", value=command, inline=False)
        embed.add_field(name="Уровень доступа", value=str(level), inline=True)
        embed.add_field(
            name="Роли с доступом",
            value=', '.join(role_list) if role_list else "Нет",
            inline=True
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name='get_permission',
        description='Показать права доступа для команды'
    )
    @app_commands.describe(command='Название команды')
    @has_command_permission('get_command_permissions')
    async def get_permission(
        self,
        interaction: discord.Interaction,
        command: str
    ):
        """Show permission settings for a command"""
        perm = get_command_permission(command)
        if not perm:
            await interaction.response.send_message(
                ERRORS['COMMAND_NOT_FOUND'],
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Права доступа: {command}",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Уровень доступа",
            value=str(perm['level']),
            inline=True
        )
        embed.add_field(
            name="Роли с доступом",
            value=', '.join(perm['roles']) if perm['roles'] else "Нет",
            inline=True
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name='set_currency',
        description='Изменить настройки валюты (для администраторов)'
    )
    @app_commands.describe(
        name='Название валюты',
        symbol='Символ валюты (эмодзи)'
    )
    @has_command_permission('set_currency')
    async def set_currency(
        self,
        interaction: discord.Interaction,
        name: str,
        symbol: str
    ):
        """Change currency settings"""
        CURRENCY['NAME'] = name
        CURRENCY['SYMBOL'] = symbol

        embed = discord.Embed(
            title="Настройки валюты обновлены",
            color=discord.Color.green()
        )
        embed.add_field(name="Новое название", value=name, inline=True)
        embed.add_field(name="Новый символ", value=symbol, inline=True)
        embed.set_footer(text=f"Изменено администратором: {interaction.user.name}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name='admin_reset',
        description='Сбросить баланс пользователя (для администраторов)'
    )
    @app_commands.describe(user='Пользователь')
    @has_command_permission('admin_reset')
    async def reset_balance(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        """Reset user balance to default (admin only)"""
        economy_cog = self.bot.get_cog('Economy')
        if not economy_cog:
            await interaction.response.send_message(
                ERRORS['ECONOMY_MODULE_ERROR'],
                ephemeral=True
            )
            return

        old_balance = economy_cog.get_balance(user.id)
        economy_cog.accounts[user.id] = DEFAULT_BALANCE

        embed = discord.Embed(title="Сброс баланса", color=discord.Color.orange())
        embed.add_field(name="Пользователь", value=user.name, inline=True)
        embed.add_field(
            name="Старый баланс",
            value=CURRENCY['FORMAT'].format(
                amount=old_balance,
                currency=CURRENCY['NAME']
            ),
            inline=True
        )
        embed.add_field(
            name="Новый баланс",
            value=CURRENCY['FORMAT'].format(
                amount=DEFAULT_BALANCE,
                currency=CURRENCY['NAME']
            ),
            inline=True
        )
        embed.set_footer(text=f"Сброшено администратором: {interaction.user.name}")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))