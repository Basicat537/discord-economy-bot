import discord
from discord.ext import commands
from discord import app_commands
from utils.config import DEFAULT_BALANCE, ERRORS, CURRENCY, SERVICE_LEVELS, PERMISSION_LEVELS, REQUIRED_ROLES
from utils.permissions import has_command_permission, set_command_permission, get_command_permission

class Admin(commands.Cog):
    """Admin commands implementation"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name='add_level',
        description='Добавить новый уровень обслуживания'
    )
    @app_commands.describe(
        name='Название уровня',
        emoji='Эмодзи уровня',
        required_balance='Требуемый баланс',
        color='Цвет (hex код, например: FF0000)',
        benefits='Список привилегий через запятую'
    )
    @has_command_permission('add_level')
    async def add_level(
        self,
        interaction: discord.Interaction,
        name: str,
        emoji: str,
        required_balance: int,
        color: str,
        benefits: str
    ):
        """Add new service level"""
        # Convert color from hex to int
        try:
            color_int = int(color.replace('#', ''), 16)
        except ValueError:
            await interaction.response.send_message(
                '❌ Неверный формат цвета! Используйте hex код (например: FF0000)',
                ephemeral=True
            )
            return

        # Generate new ID
        new_id = max([level['id'] for level in SERVICE_LEVELS['levels']], default=0) + 1

        # Create new level
        new_level = {
            'id': new_id,
            'name': name,
            'emoji': emoji,
            'required_balance': required_balance,
            'color': color_int,
            'benefits': [b.strip() for b in benefits.split(',')]
        }

        # Add to levels list
        SERVICE_LEVELS['levels'].append(new_level)
        SERVICE_LEVELS['levels'].sort(key=lambda x: x['required_balance'])

        embed = discord.Embed(
            title="✅ Уровень добавлен",
            color=discord.Color(color_int)
        )
        embed.add_field(name="ID", value=str(new_id), inline=True)
        embed.add_field(name="Название", value=f"{emoji} {name}", inline=True)
        embed.add_field(
            name="Требуемый баланс",
            value=f"{required_balance:,} {CURRENCY['NAME']}",
            inline=True
        )
        embed.add_field(
            name="Привилегии",
            value="\n".join(f"• {b}" for b in new_level['benefits']),
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name='edit_level',
        description='Редактировать существующий уровень'
    )
    @app_commands.describe(
        level_id='ID уровня',
        name='Новое название (оставьте пустым для сохранения текущего)',
        emoji='Новый эмодзи (оставьте пустым для сохранения текущего)',
        required_balance='Новый требуемый баланс (0 для сохранения текущего)',
        color='Новый цвет (hex код, оставьте пустым для сохранения текущего)',
        benefits='Новый список привилегий через запятую (оставьте пустым для сохранения текущего)'
    )
    @has_command_permission('edit_level')
    async def edit_level(
        self,
        interaction: discord.Interaction,
        level_id: int,
        name: str = None,
        emoji: str = None,
        required_balance: int = 0,
        color: str = None,
        benefits: str = None
    ):
        """Edit existing service level"""
        level = next((l for l in SERVICE_LEVELS['levels'] if l['id'] == level_id), None)
        if not level:
            await interaction.response.send_message(
                ERRORS['LEVEL_NOT_FOUND'],
                ephemeral=True
            )
            return

        # Update fields if provided
        if name:
            level['name'] = name
        if emoji:
            level['emoji'] = emoji
        if required_balance > 0:
            level['required_balance'] = required_balance
        if color:
            try:
                level['color'] = int(color.replace('#', ''), 16)
            except ValueError:
                await interaction.response.send_message(
                    '❌ Неверный формат цвета! Используйте hex код (например: FF0000)',
                    ephemeral=True
                )
                return
        if benefits:
            level['benefits'] = [b.strip() for b in benefits.split(',')]

        # Resort levels by required balance
        SERVICE_LEVELS['levels'].sort(key=lambda x: x['required_balance'])

        embed = discord.Embed(
            title="✅ Уровень обновлен",
            color=discord.Color(level['color'])
        )
        embed.add_field(name="ID", value=str(level['id']), inline=True)
        embed.add_field(name="Название", value=f"{level['emoji']} {level['name']}", inline=True)
        embed.add_field(
            name="Требуемый баланс",
            value=f"{level['required_balance']:,} {CURRENCY['NAME']}",
            inline=True
        )
        embed.add_field(
            name="Привилегии",
            value="\n".join(f"• {b}" for b in level['benefits']),
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name='remove_level',
        description='Удалить уровень обслуживания'
    )
    @app_commands.describe(level_id='ID уровня для удаления')
    @has_command_permission('remove_level')
    async def remove_level(
        self,
        interaction: discord.Interaction,
        level_id: int
    ):
        """Remove service level"""
        level = next((l for l in SERVICE_LEVELS['levels'] if l['id'] == level_id), None)
        if not level:
            await interaction.response.send_message(
                ERRORS['LEVEL_NOT_FOUND'],
                ephemeral=True
            )
            return

        SERVICE_LEVELS['levels'].remove(level)
        await interaction.response.send_message(
            f"✅ Уровень {level['emoji']} {level['name']} успешно удален"
        )

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

    @app_commands.command(
        name='help',
        description='Показать список всех доступных команд'
    )
    @has_command_permission('help')
    async def help_command(self, interaction: discord.Interaction):
        """Show all available commands with their descriptions"""
        user_level = get_user_permission_level(interaction.user)
        print(f"Showing help for user {interaction.user.name} with permission level {user_level}")

        embed = discord.Embed(
            title="📚 Справка по командам",
            description="Список доступных команд и их описание",
            color=discord.Color.blue()
        )

        # Group commands by category
        categories = {
            "💰 Экономика": [
                ('balance', 'Показать баланс вашего счета'),
                ('send', 'Перевести монеты другому пользователю'),
                ('top', 'Показать список богатейших пользователей')
            ],
            "⚙️ Администрирование": [
                ('admin_set', 'Установить баланс пользователя'),
                ('admin_reset', 'Сбросить баланс пользователя'),
                ('set_currency', 'Изменить настройки валюты'),
                ('set_permission', 'Установить права доступа для команды'),
                ('get_permission', 'Показать права доступа для команды'),
                ('add_level', 'Добавить новый уровень обслуживания'),
                ('edit_level', 'Редактировать существующий уровень'),
                ('remove_level', 'Удалить уровень обслуживания')
            ]
        }

        for category, commands in categories.items():
            field_value = ""
            for cmd_name, desc in commands:
                perm = get_command_permission(cmd_name)
                if user_level >= perm['level']:
                    level_str = f"(Уровень {perm['level']})" if perm['level'] > 0 else ""
                    field_value += f"**/{cmd_name}** {level_str}\n{desc}\n\n"

            if field_value:
                embed.add_field(
                    name=category,
                    value=field_value,
                    inline=False
                )

        embed.set_footer(text=f"Ваш уровень доступа: {user_level}")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Admin(bot))