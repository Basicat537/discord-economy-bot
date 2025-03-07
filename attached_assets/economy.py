import discord
from discord.ext import commands
from discord import app_commands
from utils.config import DEFAULT_BALANCE

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.accounts = {}  # Store user balances in memory

    def get_balance(self, user_id: int) -> int:
        if user_id not in self.accounts:
            self.accounts[user_id] = DEFAULT_BALANCE
        return self.accounts[user_id]

    @app_commands.command(name='balance', description='Показать баланс вашего счета')
    async def balance(self, interaction: discord.Interaction):
        balance = self.get_balance(interaction.user.id)
        embed = discord.Embed(title="Информация о счете", color=discord.Color.blue())
        embed.add_field(name="Владелец", value=interaction.user.name, inline=False)
        embed.add_field(name="Баланс", value=f"{balance} монет", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='send', description='Перевести монеты другому пользователю')
    @app_commands.describe(
        user='Получатель перевода',
        amount='Сумма перевода'
    )
    async def transfer(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message('❌ Сумма перевода должна быть положительной!', ephemeral=True)
            return

        sender_balance = self.get_balance(interaction.user.id)
        if sender_balance < amount:
            await interaction.response.send_message('❌ Недостаточно средств на счете!', ephemeral=True)
            return

        # Выполняем перевод
        self.accounts[interaction.user.id] -= amount
        self.get_balance(user.id)  # Ensure recipient account exists
        self.accounts[user.id] += amount

        embed = discord.Embed(title="Перевод выполнен", color=discord.Color.green())
        embed.add_field(name="От", value=interaction.user.name, inline=True)
        embed.add_field(name="Кому", value=user.name, inline=True)
        embed.add_field(name="Сумма", value=f"{amount} монет", inline=True)
        embed.add_field(name="Остаток", value=f"{self.accounts[interaction.user.id]} монет", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='top', description='Показать список богатейших пользователей')
    async def top(self, interaction: discord.Interaction):
        if not self.accounts:
            embed = discord.Embed(
                title="Топ счетов",
                description="Список пуст. Пока нет ни одного счета!",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed)
            return

        sorted_accounts = sorted(self.accounts.items(), key=lambda x: x[1], reverse=True)

        embed = discord.Embed(title="Топ счетов", color=discord.Color.gold())
        added_count = 0

        for i, (user_id, balance) in enumerate(sorted_accounts, 1):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(
                    name=f"#{i} {user.name}",
                    value=f"{balance} монет",
                    inline=False
                )
                added_count += 1
            if added_count >= 10:  # Показываем только топ-10
                break

        if added_count == 0:
            embed.description = "Не удалось получить информацию о пользователях"
        else:
            embed.set_footer(text=f"Всего пользователей в списке: {len(self.accounts)}")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))