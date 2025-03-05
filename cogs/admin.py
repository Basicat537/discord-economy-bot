import discord
from discord.ext import commands
from discord import app_commands
from utils.config import DEFAULT_BALANCE, ERRORS, CURRENCY
from utils.permissions import has_command_permission
from utils.database import get_db, UserProfile, ServiceLevel, Transaction # Added import for database interaction and models
import json

class Admin(commands.Cog):
    """Admin commands implementation"""

    def __init__(self, bot):
        self.bot = bot
        print("Admin cog initialized")

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
        print(f"Add level command called by {interaction.user.name}")

        try:
            color_int = int(color.replace('#', ''), 16)
        except ValueError:
            await interaction.response.send_message(
                '❌ Неверный формат цвета! Используйте hex код (например: FF0000)',
                ephemeral=True
            )
            return

        benefits_list = [b.strip() for b in benefits.split(',')]

        db = next(get_db())
        try:
            # Проверяем, существует ли уже уровень с таким required_balance для этого сервера
            existing_level = db.query(ServiceLevel).filter(
                ServiceLevel.guild_id == interaction.guild_id,
                ServiceLevel.required_balance == required_balance
            ).first()

            if existing_level:
                await interaction.response.send_message(
                    f'❌ Уровень с требуемым балансом {required_balance} уже существует!',
                    ephemeral=True
                )
                return

            new_level = ServiceLevel(
                guild_id=interaction.guild_id,
                name=name,
                emoji=emoji,
                required_balance=required_balance,
                color=color_int,
                benefits=json.dumps(benefits_list)
            )
            db.add(new_level)
            db.commit()

            embed = discord.Embed(
                title="✅ Уровень добавлен",
                color=discord.Color(color_int)
            )
            embed.add_field(name="ID", value=str(new_level.id), inline=True)
            embed.add_field(name="Название", value=f"{emoji} {name}", inline=True)
            embed.add_field(
                name="Требуемый баланс",
                value=f"{required_balance:,} {CURRENCY['NAME']}",
                inline=True
            )
            embed.add_field(
                name="Привилегии",
                value="\n".join(f"• {b}" for b in benefits_list),
                inline=False
            )

            await interaction.response.send_message(embed=embed)
        finally:
            db.close()

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
        print(f"Edit level command called by {interaction.user.name} for level {level_id}")

        db = next(get_db())
        try:
            level = db.query(ServiceLevel).filter_by(
                id=level_id,
                guild_id=interaction.guild_id
            ).first()

            if not level:
                await interaction.response.send_message(
                    ERRORS['LEVEL_NOT_FOUND'],
                    ephemeral=True
                )
                return

            if name:
                level.name = name
            if emoji:
                level.emoji = emoji
            if required_balance > 0:
                # Проверяем, не конфликтует ли новый required_balance с другими уровнями
                existing_level = db.query(ServiceLevel).filter(
                    ServiceLevel.guild_id == interaction.guild_id,
                    ServiceLevel.required_balance == required_balance,
                    ServiceLevel.id != level_id
                ).first()

                if existing_level:
                    await interaction.response.send_message(
                        f'❌ Уровень с требуемым балансом {required_balance} уже существует!',
                        ephemeral=True
                    )
                    return

                level.required_balance = required_balance

            if color:
                try:
                    level.color = int(color.replace('#', ''), 16)
                except ValueError:
                    await interaction.response.send_message(
                        '❌ Неверный формат цвета! Используйте hex код (например: FF0000)',
                        ephemeral=True
                    )
                    return

            if benefits:
                level.benefits = json.dumps([b.strip() for b in benefits.split(',')])

            db.commit()

            embed = discord.Embed(
                title="✅ Уровень обновлен",
                color=discord.Color(level.color)
            )
            embed.add_field(name="ID", value=str(level.id), inline=True)
            embed.add_field(
                name="Название",
                value=f"{level.emoji} {level.name}",
                inline=True
            )
            embed.add_field(
                name="Требуемый баланс",
                value=f"{level.required_balance:,} {CURRENCY['NAME']}",
                inline=True
            )
            embed.add_field(
                name="Привилегии",
                value="\n".join(f"• {b}" for b in json.loads(level.benefits)),
                inline=False
            )

            await interaction.response.send_message(embed=embed)
        finally:
            db.close()

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
        print(f"Remove level command called by {interaction.user.name} for level {level_id}")

        db = next(get_db())
        try:
            level = db.query(ServiceLevel).filter_by(
                id=level_id,
                guild_id=interaction.guild_id
            ).first()

            if not level:
                await interaction.response.send_message(
                    ERRORS['LEVEL_NOT_FOUND'],
                    ephemeral=True
                )
                return

            db.delete(level)
            db.commit()

            await interaction.response.send_message(
                f"✅ Уровень {level.emoji} {level.name} успешно удален"
            )
        finally:
            db.close()

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

        db = next(get_db())
        try:
            profile = db.query(UserProfile).filter(
                UserProfile.user_id == user.id,
                UserProfile.guild_id == interaction.guild_id
            ).first()

            if not profile:
                profile = UserProfile(
                    user_id=user.id,
                    guild_id=interaction.guild_id,
                    balance=amount
                )
                db.add(profile)
            else:
                old_balance = profile.balance
                profile.balance = amount

            # Record transaction
            transaction = Transaction(
                from_user_id=interaction.user.id,
                to_user_id=user.id,
                guild_id=interaction.guild_id,
                amount=amount - (old_balance if 'old_balance' in locals() else 0),
                transaction_type='admin_set'
            )
            db.add(transaction)
            db.commit()

            embed = discord.Embed(title="Изменение баланса", color=discord.Color.blue())
            embed.add_field(name="Пользователь", value=user.name, inline=True)
            embed.add_field(
                name="Старый баланс",
                value=f"{CURRENCY['SYMBOL']} {old_balance if 'old_balance' in locals() else 0:,} {CURRENCY['NAME']}",
                inline=True
            )
            embed.add_field(
                name="Новый баланс",
                value=f"{CURRENCY['SYMBOL']} {amount:,} {CURRENCY['NAME']}",
                inline=True
            )
            embed.set_footer(text=f"Изменено администратором: {interaction.user.name}")

            await interaction.response.send_message(embed=embed)
        finally:
            db.close()

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
        print(f"Help command called by {interaction.user.name} with permission level {user_level}")

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
                ('top', 'Показать список богатейших пользователей'),
                ('level', 'Информация об уровнях обслуживания')
            ],
            "⚙️ Администрирование": [
                ('admin_set', 'Установить баланс пользователя'),
                ('admin_reset', 'Сбросить баланс пользователя'),
                ('set_currency', 'Изменить настройки валюты'),
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
    print("Admin cog setup complete")