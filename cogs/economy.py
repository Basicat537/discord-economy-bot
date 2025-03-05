import discord
from discord.ext import commands
from discord import app_commands
from utils.config import DEFAULT_BALANCE, ERRORS, CURRENCY, DEFAULT_COLOR
from utils.database import get_db, UserProfile, Transaction, ServiceLevel
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
import json
import sys

class Economy(commands.Cog):
    """Economy system implementation"""

    def __init__(self, bot):
        self.bot = bot
        print("Economy cog initialized")

    def get_balance(self, user_id: int, guild_id: int) -> int:
        """Get user balance for specific server, initialize if doesn't exist"""
        if not guild_id:
            print(f"Warning: get_balance called without guild_id for user {user_id}", file=sys.stderr)
            return DEFAULT_BALANCE

        try:
            with get_db() as db:
                profile = db.query(UserProfile).filter(
                    UserProfile.user_id == user_id,
                    UserProfile.guild_id == guild_id
                ).first()

                if not profile:
                    profile = UserProfile(
                        user_id=user_id,
                        guild_id=guild_id,
                        balance=DEFAULT_BALANCE
                    )
                    db.add(profile)
                    db.commit()
                    print(f"Created new profile for user {user_id} in guild {guild_id}")

                return profile.balance
        except SQLAlchemyError as e:
            print(f"Database error in get_balance: {str(e)}", file=sys.stderr)
            return DEFAULT_BALANCE

    def get_user_level(self, balance: int, guild_id: int) -> dict:
        """Get user's service level based on balance"""
        if not guild_id:
            print(f"Warning: get_user_level called without guild_id", file=sys.stderr)
            return None

        try:
            with get_db() as db:
                levels = db.query(ServiceLevel).filter(
                    ServiceLevel.guild_id == guild_id,
                    ServiceLevel.required_balance <= balance
                ).order_by(desc(ServiceLevel.required_balance)).all()

                if levels:
                    level = levels[0]
                    return {
                        'id': level.id,
                        'name': level.name,
                        'emoji': level.emoji,
                        'required_balance': level.required_balance,
                        'color': level.color,
                        'benefits': json.loads(level.benefits)
                    }
                return None
        except SQLAlchemyError as e:
            print(f"Database error in get_user_level: {str(e)}", file=sys.stderr)
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error in get_user_level: {str(e)}", file=sys.stderr)
            return None

    def format_amount(self, amount: int) -> str:
        """Format amount with currency"""
        return f"{amount:,} {CURRENCY['NAME']}"

    @app_commands.command(
        name='balance',
        description='Показать баланс счета'
    )
    @app_commands.describe(
        user='Пользователь (опционально)'
    )
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        """Show user balance command"""
        try:
            print(f"Balance command called by {interaction.user.name}")

            if not interaction.guild_id:
                await interaction.response.send_message(
                    "❌ Эта команда работает только на серверах!",
                    ephemeral=True
                )
                return

            # If no user specified, show own balance
            target_user = user or interaction.user

            balance = self.get_balance(target_user.id, interaction.guild_id)
            user_level = self.get_user_level(balance, interaction.guild_id)

            embed = discord.Embed(
                title="Информация о счете",
                color=discord.Color(user_level['color'] if user_level else DEFAULT_COLOR)
            )

            embed.add_field(name="Владелец", value=target_user.name, inline=False)
            embed.add_field(
                name="Баланс",
                value=f"{CURRENCY['SYMBOL']} {self.format_amount(balance)}",
                inline=False
            )

            if user_level:
                embed.add_field(
                    name="Уровень обслуживания",
                    value=f"{user_level['emoji']} {user_level['name']}",
                    inline=False
                )
                embed.add_field(
                    name="Привилегии",
                    value="\n".join(f"• {benefit}" for benefit in user_level['benefits']),
                    inline=False
                )

                with get_db() as db:
                    try:
                        next_level = db.query(ServiceLevel).filter(
                            ServiceLevel.guild_id == interaction.guild_id,
                            ServiceLevel.required_balance > balance
                        ).order_by(ServiceLevel.required_balance).first()

                        if next_level:
                            remaining = next_level.required_balance - balance
                            embed.add_field(
                                name="До следующего уровня",
                                value=f"Накопите еще {self.format_amount(remaining)} для получения уровня {next_level.emoji} {next_level.name}",
                                inline=False
                            )
                        else:
                            embed.add_field(
                                name="Поздравляем! 🎉",
                                value="Вы достигли максимального уровня обслуживания!",
                                inline=False
                            )
                    except SQLAlchemyError as e:
                        print(f"Database error in balance command (next level): {str(e)}", file=sys.stderr)

            else:
                with get_db() as db:
                    try:
                        first_level = db.query(ServiceLevel).filter(
                            ServiceLevel.guild_id == interaction.guild_id
                        ).order_by(ServiceLevel.required_balance).first()

                        if first_level:
                            remaining = first_level.required_balance - balance
                            embed.add_field(
                                name="Уровень обслуживания",
                                value="У вас пока нет уровня обслуживания",
                                inline=False
                            )
                            embed.add_field(
                                name="Следующий уровень",
                                value=f"Накопите еще {self.format_amount(remaining)} для получения уровня {first_level.emoji} {first_level.name}",
                                inline=False
                            )
                    except SQLAlchemyError as e:
                        print(f"Database error in balance command (first level): {str(e)}", file=sys.stderr)

            if user:
                embed.set_footer(text=f"Запрошено пользователем: {interaction.user.name}")

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error in balance command: {e}", file=sys.stderr)
            await interaction.response.send_message(
                "❌ Произошла ошибка при получении информации о балансе",
                ephemeral=True
            )

    @app_commands.command(
        name='send',
        description='Перевести монеты другому пользователю'
    )
    @app_commands.describe(
        user='Получатель перевода',
        amount='Сумма перевода'
    )
    async def transfer(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Transfer money to another user"""
        print(f"Transfer command called by {interaction.user.name} to {user.name} amount {amount}")

        if amount <= 0:
            await interaction.response.send_message(
                ERRORS['INVALID_AMOUNT'],
                ephemeral=True
            )
            return

        if user.id == interaction.user.id:
            await interaction.response.send_message(
                '❌ Нельзя переводить деньги самому себе!',
                ephemeral=True
            )
            return

        with get_db() as db:
            try:
                # Get or create sender profile
                sender_profile = db.query(UserProfile).filter(
                    UserProfile.user_id == interaction.user.id,
                    UserProfile.guild_id == interaction.guild_id
                ).first()

                if not sender_profile or sender_profile.balance < amount:
                    await interaction.response.send_message(
                        ERRORS['INSUFFICIENT_FUNDS'],
                        ephemeral=True
                    )
                    return

                # Get or create recipient profile
                recipient_profile = db.query(UserProfile).filter(
                    UserProfile.user_id == user.id,
                    UserProfile.guild_id == interaction.guild_id
                ).first()

                if not recipient_profile:
                    recipient_profile = UserProfile(
                        user_id=user.id,
                        guild_id=interaction.guild_id,
                        balance=DEFAULT_BALANCE
                    )
                    db.add(recipient_profile)

                # Perform transfer
                sender_profile.balance -= amount
                recipient_profile.balance += amount

                # Record transaction
                transaction = Transaction(
                    from_user_id=interaction.user.id,
                    to_user_id=user.id,
                    guild_id=interaction.guild_id,
                    amount=amount,
                    transaction_type='transfer'
                )
                db.add(transaction)
                db.commit()

                embed = discord.Embed(title="Перевод выполнен", color=discord.Color.green())
                embed.add_field(name="От", value=interaction.user.name, inline=True)
                embed.add_field(name="Кому", value=user.name, inline=True)
                embed.add_field(
                    name="Сумма",
                    value=f"{CURRENCY['SYMBOL']} {self.format_amount(amount)}",
                    inline=True
                )
                embed.add_field(
                    name="Остаток",
                    value=f"{CURRENCY['SYMBOL']} {self.format_amount(sender_profile.balance)}",
                    inline=False
                )

                await interaction.response.send_message(embed=embed)
            except SQLAlchemyError as e:
                print(f"Database error in transfer command: {str(e)}", file=sys.stderr)
                await interaction.response.send_message(
                    "❌ Произошла ошибка при переводе денег",
                    ephemeral=True
                )

    @app_commands.command(
        name='top',
        description='Показать список богатейших пользователей'
    )
    async def top(self, interaction: discord.Interaction):
        """Show top richest users"""
        print(f"Top command called by {interaction.user.name}")

        with get_db() as db:
            try:
                sorted_accounts = db.query(UserProfile).filter(
                    UserProfile.guild_id == interaction.guild_id
                ).order_by(desc(UserProfile.balance)).all()

                if not sorted_accounts:
                    embed = discord.Embed(
                        title="Топ счетов",
                        description="Список пуст. Пока нет ни одного счета!",
                        color=discord.Color.gold()
                    )
                    await interaction.response.send_message(embed=embed)
                    return

                embed = discord.Embed(title="Топ счетов", color=discord.Color.gold())
                added_count = 0

                for i, profile in enumerate(sorted_accounts, 1):
                    user = self.bot.get_user(profile.user_id)
                    if user:
                        embed.add_field(
                            name=f"#{i} {user.name}",
                            value=f"{CURRENCY['SYMBOL']} {self.format_amount(profile.balance)}",
                            inline=False
                        )
                        added_count += 1
                    if added_count >= 10:  # Show only top 10
                        break

                if added_count == 0:
                    embed.description = "Не удалось получить информацию о пользователях"
                else:
                    embed.set_footer(text=f"Всего пользователей в списке: {len(sorted_accounts)}")

                await interaction.response.send_message(embed=embed)
            except SQLAlchemyError as e:
                print(f"Database error in top command: {str(e)}", file=sys.stderr)
                await interaction.response.send_message(
                    "❌ Произошла ошибка при получении топа счетов",
                    ephemeral=True
                )

    @app_commands.command(
        name='level',
        description='Информация об уровнях обслуживания'
    )
    @app_commands.describe(
        level_id='ID уровня для подробной информации'
    )
    async def level(self, interaction: discord.Interaction, level_id: int = None):
        """Show service level information"""
        print(f"Level command called by {interaction.user.name}, level_id={level_id}")

        with get_db() as db:
            try:
                if level_id is not None:
                    # Show specific level info
                    level = db.query(ServiceLevel).filter(
                        ServiceLevel.guild_id == interaction.guild_id,
                        ServiceLevel.id == level_id
                    ).first()
                    if not level:
                        await interaction.response.send_message(
                            ERRORS['LEVEL_NOT_FOUND'],
                            ephemeral=True
                        )
                        return

                    embed = discord.Embed(
                        title=f"Уровень {level.emoji} {level.name}",
                        color=discord.Color(level.color)
                    )
                    embed.add_field(
                        name="Требуемый баланс",
                        value=self.format_amount(level.required_balance),
                        inline=False
                    )
                    embed.add_field(
                        name="Привилегии",
                        value="\n".join(f"• {benefit}" for benefit in json.loads(level.benefits)),
                        inline=False
                    )
                else:
                    # Show all levels overview
                    embed = discord.Embed(
                        title="📊 Уровни обслуживания",
                        description="Список всех доступных уровней",
                        color=discord.Color(DEFAULT_COLOR)
                    )

                    current_balance = self.get_balance(interaction.user.id, interaction.guild_id)
                    current_level = self.get_user_level(current_balance, interaction.guild_id)

                    levels = db.query(ServiceLevel).filter(
                        ServiceLevel.guild_id == interaction.guild_id
                    ).order_by(ServiceLevel.required_balance).all()

                    for level in levels:
                        status = ""
                        if current_level and level.id == current_level['id']:
                            status = "✅ Текущий уровень"
                        elif current_balance >= level.required_balance:
                            status = "✓ Доступен"
                        else:
                            remaining = level.required_balance - current_balance
                            status = f"Требуется еще {self.format_amount(remaining)}"

                        embed.add_field(
                            name=f"{level.emoji} {level.name} (ID: {level.id})",
                            value=f"Требуемый баланс: {self.format_amount(level.required_balance)}\n{status}",
                            inline=False
                        )

                    embed.set_footer(text="Используйте /level <ID> для подробной информации об уровне")

                await interaction.response.send_message(embed=embed)
            except SQLAlchemyError as e:
                print(f"Database error in level command: {str(e)}", file=sys.stderr)
                await interaction.response.send_message(
                    "❌ Произошла ошибка при получении информации об уровнях",
                    ephemeral=True
                )
            except json.JSONDecodeError as e:
                print(f"JSON decode error in level command: {str(e)}", file=sys.stderr)
                await interaction.response.send_message(
                    "❌ Произошла ошибка при обработке данных уровней",
                    ephemeral=True
                )


async def setup(bot):
    await bot.add_cog(Economy(bot))
    print("Economy cog setup complete")