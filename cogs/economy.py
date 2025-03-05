import json
import os
import discord
from discord.ext import commands
from discord import app_commands
from utils.config import DEFAULT_BALANCE, ERRORS, CURRENCY, SERVICE_LEVELS

DATA_FILE = 'data/accounts.json'

class Economy(commands.Cog):
    """Economy system implementation"""

    def __init__(self, bot):
        self.bot = bot
        self.accounts = {}
        self.load_accounts()
        print("Economy cog initialized")

    def load_accounts(self):
        """Load accounts from file"""
        os.makedirs('data', exist_ok=True)
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    self.accounts = {int(k): v for k, v in json.load(f).items()}
                print(f"Loaded {len(self.accounts)} accounts from file")
            else:
                print("No accounts file found, starting with empty accounts")
        except Exception as e:
            print(f"Error loading accounts: {e}")
            self.accounts = {}

    def save_accounts(self):
        """Save accounts to file"""
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump({str(k): v for k, v in self.accounts.items()}, f)
            print(f"Saved {len(self.accounts)} accounts to file")
        except Exception as e:
            print(f"Error saving accounts: {e}")

    def get_balance(self, user_id: int) -> int:
        """Get user balance, initialize if doesn't exist"""
        if user_id not in self.accounts:
            print(f"Creating new account for user {user_id}")
            self.accounts[user_id] = DEFAULT_BALANCE
            self.save_accounts()
        return self.accounts[user_id]

    def get_user_level(self, balance: int) -> dict:
        """Get user's service level based on balance"""
        for level in reversed(SERVICE_LEVELS['levels']):
            if balance >= level['required_balance']:
                print(f"Found level {level['name']} for balance {balance}")
                return level
        print(f"No level found for balance {balance}")
        return None

    def format_amount(self, amount: int) -> str:
        """Format amount with currency"""
        return f"{amount:,} {CURRENCY['NAME']}"

    @app_commands.command(
        name='balance',
        description='Показать баланс вашего счета'
    )
    async def balance(self, interaction: discord.Interaction):
        """Show user balance command"""
        print(f"Balance command called by {interaction.user.name}")
        balance = self.get_balance(interaction.user.id)
        user_level = self.get_user_level(balance)

        embed = discord.Embed(
            title="Информация о счете",
            color=discord.Color(user_level['color'] if user_level else SERVICE_LEVELS['default_color'])
        )

        # Basic info
        embed.add_field(name="Владелец", value=interaction.user.name, inline=False)
        embed.add_field(
            name="Баланс",
            value=f"{CURRENCY['SYMBOL']} {self.format_amount(balance)}",
            inline=False
        )

        # Level info if exists
        if user_level:
            embed.add_field(
                name="Уровень обслуживания",
                value=f"{user_level['emoji']} {user_level['name']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

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

        sender_balance = self.get_balance(interaction.user.id)
        if sender_balance < amount:
            await interaction.response.send_message(
                ERRORS['INSUFFICIENT_FUNDS'],
                ephemeral=True
            )
            return

        # Perform transfer
        self.accounts[interaction.user.id] -= amount
        self.get_balance(user.id)  # Ensure recipient account exists
        self.accounts[user.id] += amount
        self.save_accounts()  # Save changes

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
            value=f"{CURRENCY['SYMBOL']} {self.format_amount(self.accounts[interaction.user.id])}",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name='top',
        description='Показать список богатейших пользователей'
    )
    async def top(self, interaction: discord.Interaction):
        """Show top richest users"""
        print(f"Top command called by {interaction.user.name}")

        if not self.accounts:
            embed = discord.Embed(
                title="Топ счетов",
                description="Список пуст. Пока нет ни одного счета!",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed)
            return

        sorted_accounts = sorted(
            self.accounts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        embed = discord.Embed(title="Топ счетов", color=discord.Color.gold())
        added_count = 0

        for i, (user_id, balance) in enumerate(sorted_accounts, 1):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(
                    name=f"#{i} {user.name}",
                    value=f"{CURRENCY['SYMBOL']} {self.format_amount(balance)}",
                    inline=False
                )
                added_count += 1
            if added_count >= 10:  # Show only top 10
                break

        if added_count == 0:
            embed.description = "Не удалось получить информацию о пользователях"
        else:
            embed.set_footer(text=f"Всего пользователей в списке: {len(self.accounts)}")

        await interaction.response.send_message(embed=embed)

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

        if level_id is not None:
            # Show specific level info
            level = next((l for l in SERVICE_LEVELS['levels'] if l['id'] == level_id), None)
            if not level:
                await interaction.response.send_message(
                    ERRORS['LEVEL_NOT_FOUND'],
                    ephemeral=True
                )
                return

            embed = discord.Embed(
                title=f"Уровень {level['emoji']} {level['name']}",
                color=discord.Color(level['color'])
            )
            embed.add_field(
                name="Требуемый баланс",
                value=self.format_amount(level['required_balance']),
                inline=False
            )
            embed.add_field(
                name="Привилегии",
                value="\n".join(f"• {benefit}" for benefit in level['benefits']),
                inline=False
            )
        else:
            # Show all levels overview
            embed = discord.Embed(
                title="📊 Уровни обслуживания",
                description="Список всех доступных уровней",
                color=discord.Color(SERVICE_LEVELS['default_color'])
            )

            current_balance = self.get_balance(interaction.user.id)
            current_level = self.get_user_level(current_balance)

            for level in SERVICE_LEVELS['levels']:
                status = ""
                if current_level and level['id'] == current_level['id']:
                    status = "✅ Текущий уровень"
                elif current_balance >= level['required_balance']:
                    status = "✓ Доступен"
                else:
                    remaining = level['required_balance'] - current_balance
                    status = f"Требуется еще {self.format_amount(remaining)}"

                embed.add_field(
                    name=f"{level['emoji']} {level['name']} (ID: {level['id']})",
                    value=f"Требуемый баланс: {self.format_amount(level['required_balance'])}\n{status}",
                    inline=False
                )

            embed.set_footer(text="Используйте /level <ID> для подробной информации об уровне")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
    print("Economy cog setup complete")