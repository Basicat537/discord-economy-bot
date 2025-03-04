import discord
from discord.ext import commands
from discord import app_commands
from utils.config import DEFAULT_BALANCE, ERRORS, CURRENCY
from utils.permissions import has_command_permission

class Economy(commands.Cog):
    """Economy system implementation"""

    def __init__(self, bot):
        self.bot = bot
        self.accounts = {}  # Store user balances in memory

    def get_balance(self, user_id: int) -> int:
        """Get user balance, initialize if doesn't exist"""
        if user_id not in self.accounts:
            self.accounts[user_id] = DEFAULT_BALANCE
        return self.accounts[user_id]

    def format_amount(self, amount: int) -> str:
        """Format amount with currency"""
        return CURRENCY['FORMAT'].format(
            amount=amount,
            currency=CURRENCY['NAME']
        )

    @app_commands.command(
        name='balance',
        description='Показать баланс вашего счета'
    )
    @has_command_permission('balance')
    async def balance(self, interaction: discord.Interaction):
        """Show user balance command"""
        balance = self.get_balance(interaction.user.id)
        embed = discord.Embed(
            title="Информация о счете",
            color=discord.Color.blue()
        )
        embed.add_field(name="Владелец", value=interaction.user.name, inline=False)
        embed.add_field(
            name="Баланс",
            value=f"{CURRENCY['SYMBOL']} {self.format_amount(balance)}",
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
    @has_command_permission('send')
    async def transfer(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        amount: int
    ):
        """Transfer money to another user"""
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
    @has_command_permission('top')
    async def top(self, interaction: discord.Interaction):
        """Show top richest users"""
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

async def setup(bot):
    await bot.add_cog(Economy(bot))