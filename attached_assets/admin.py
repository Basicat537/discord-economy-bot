import discord
from discord.ext import commands
from discord import app_commands
from utils.config import DEFAULT_BALANCE

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin():
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)

    @app_commands.command(name='admin_set', description='Установить баланс пользователя (для администраторов)')
    @app_commands.describe(
        user='Пользователь',
        amount='Новый баланс'
    )
    @is_admin()
    async def set_balance(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount < 0:
            await interaction.response.send_message('❌ Баланс не может быть отрицательным', ephemeral=True)
            return

        economy_cog = self.bot.get_cog('Economy')
        if not economy_cog:
            await interaction.response.send_message('❌ Ошибка: модуль экономики не доступен', ephemeral=True)
            return

        old_balance = economy_cog.get_balance(user.id)
        economy_cog.accounts[user.id] = amount

        embed = discord.Embed(title="Изменение баланса", color=discord.Color.blue())
        embed.add_field(name="Пользователь", value=user.name, inline=True)
        embed.add_field(name="Старый баланс", value=f"{old_balance} монет", inline=True)
        embed.add_field(name="Новый баланс", value=f"{amount} монет", inline=True)
        embed.set_footer(text=f"Изменено администратором: {interaction.user.name}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='admin_reset', description='Сбросить баланс пользователя (для администраторов)')
    @app_commands.describe(user='Пользователь')
    @is_admin()
    async def reset_balance(self, interaction: discord.Interaction, user: discord.Member):
        economy_cog = self.bot.get_cog('Economy')
        if not economy_cog:
            await interaction.response.send_message('❌ Ошибка: модуль экономики не доступен', ephemeral=True)
            return

        old_balance = economy_cog.get_balance(user.id)
        economy_cog.accounts[user.id] = DEFAULT_BALANCE

        embed = discord.Embed(title="Сброс баланса", color=discord.Color.orange())
        embed.add_field(name="Пользователь", value=user.name, inline=True)
        embed.add_field(name="Старый баланс", value=f"{old_balance} монет", inline=True)
        embed.add_field(name="Новый баланс", value=f"{DEFAULT_BALANCE} монет", inline=True)
        embed.set_footer(text=f"Сброшено администратором: {interaction.user.name}")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))