import discord
from discord.ext import commands
from discord import app_commands
from utils.permissions import check_admin
from utils.storage import JsonStorage
from utils.logger import Logger
from utils.minecraft_utils import MinecraftServerUtils
import os
from datetime import datetime, timedelta

class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.storage = JsonStorage('data/minecraft.json')
        self.logger = Logger('minecraft')
        # Initialize Minecraft server utils with server address from environment
        server_address = os.getenv('MINECRAFT_SERVER', 'localhost:25565')
        self.mc_utils = MinecraftServerUtils(server_address)

    @app_commands.command(
        name='mcstatus',
        description='Показать статус Minecraft сервера'
    )
    async def server_status(self, interaction: discord.Interaction):
        """Show Minecraft server status"""
        status = await self.mc_utils.get_server_status()

        if status['online']:
            embed = discord.Embed(
                title="🟢 Minecraft Сервер Онлайн",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Игроки",
                value=f"{status['players_online']}/{status['players_max']}",
                inline=True
            )
            embed.add_field(
                name="Версия",
                value=status['version'],
                inline=True
            )
            embed.add_field(
                name="Пинг",
                value=f"{round(status['latency'])}мс",
                inline=True
            )

            # Get online players
            players = await self.mc_utils.get_players()
            if players:
                embed.add_field(
                    name="Сейчас играют",
                    value="\n".join(players),
                    inline=False
                )
        else:
            embed = discord.Embed(
                title="🔴 Minecraft Сервер Оффлайн",
                description=f"Ошибка: {status.get('error', 'Неизвестная ошибка')}",
                color=discord.Color.red()
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name='linkmc',
        description='Привязать ваш Discord аккаунт к Minecraft'
    )
    @app_commands.describe(
        minecraft_username='Ваш ник в Minecraft'
    )
    async def link_minecraft(self, interaction: discord.Interaction, minecraft_username: str):
        """Link Discord account to Minecraft username"""
        user_id = str(interaction.user.id)

        # Verify if player exists on server
        is_valid = await self.mc_utils.is_player_online(minecraft_username)
        if not is_valid:
            embed = discord.Embed(
                title="❌ Ошибка привязки",
                description="Игрок с таким ником не найден на сервере. Убедитесь, что вы онлайн на сервере.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.storage.set_minecraft_link(user_id, minecraft_username)

        embed = discord.Embed(
            title="✅ Minecraft Аккаунт Привязан",
            description=f"Ваш Discord аккаунт привязан к: {minecraft_username}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        self.logger.log(f"User {user_id} linked Minecraft account: {minecraft_username}")

    @app_commands.command(
        name='unlinkmc',
        description='Отвязать ваш Minecraft аккаунт'
    )
    async def unlink_minecraft(self, interaction: discord.Interaction):
        """Unlink Minecraft account"""
        user_id = str(interaction.user.id)
        self.storage.remove_minecraft_link(user_id)

        embed = discord.Embed(
            title="Minecraft Аккаунт Отвязан",
            description="Ваш Minecraft аккаунт успешно отвязан",
            color=discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed)
        self.logger.log(f"User {user_id} unlinked Minecraft account")

    @app_commands.command(
        name='mcreward',
        description='Получить награду за игру на сервере'
    )
    async def minecraft_reward(self, interaction: discord.Interaction):
        """Get reward for playing on the server"""
        user_id = str(interaction.user.id)
        minecraft_username = self.storage.get_minecraft_username(user_id)

        if not minecraft_username:
            await interaction.response.send_message(
                "❌ Сначала привяжите ваш Minecraft аккаунт используя /linkmc",
                ephemeral=True
            )
            return

        # Check if player is online
        is_online = await self.mc_utils.is_player_online(minecraft_username)
        if not is_online:
            await interaction.response.send_message(
                "❌ Вы должны быть онлайн на сервере для получения награды",
                ephemeral=True
            )
            return

        try:
            amount = self.storage.give_minecraft_reward(user_id)
            embed = discord.Embed(
                title="💰 Награда Получена",
                description=f"Вы получили {amount} монет за игру на сервере!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Minecraft(bot))
    print("Minecraft cog setup complete")