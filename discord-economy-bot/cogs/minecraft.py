import discord
from discord.ext import commands
from discord import app_commands
from mcstatus import JavaServer
from utils.config import MINECRAFT_CONFIG, ERRORS, CURRENCY
from utils.permissions import requires_role
import asyncio

class Minecraft(commands.Cog):
    """Minecraft server integration"""

    def __init__(self, bot):
        self.bot = bot
        self.server = None
        self.last_status = None
        self.status_task = None

    async def cog_load(self):
        """Called when the cog is loaded"""
        try:
            print(f"Attempting to connect to Minecraft server at {MINECRAFT_CONFIG['SERVER_ADDRESS']}")
            self.server = JavaServer.lookup(MINECRAFT_CONFIG['SERVER_ADDRESS'])
            self.status_task = self.bot.loop.create_task(self.update_status_loop())
            print("Successfully initialized Minecraft server connection")
        except Exception as e:
            print(f"Failed to initialize Minecraft server connection: {e}")
            self.server = None

    async def cog_unload(self):
        """Called when the cog is unloaded"""
        if self.status_task:
            self.status_task.cancel()

    async def update_status_loop(self):
        """Periodically update server status"""
        while True:
            try:
                if self.server:
                    self.last_status = await self.server.async_status()
                    print("Successfully updated Minecraft server status")
                else:
                    print("No server connection available")
            except Exception as e:
                print(f"Failed to update Minecraft server status: {e}")
                self.last_status = None
            await asyncio.sleep(MINECRAFT_CONFIG['UPDATE_INTERVAL'])

    @app_commands.command(
        name='mc_status',
        description='Показать статус Minecraft сервера'
    )
    async def status(self, interaction: discord.Interaction):
        """Show Minecraft server status"""
        if not self.server:
            await interaction.response.send_message(
                "❌ Сервер Minecraft недоступен",
                ephemeral=True
            )
            return

        try:
            status = await self.server.async_status()
            self.last_status = status

            embed = discord.Embed(
                title="Статус Minecraft сервера",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Адрес",
                value=MINECRAFT_CONFIG['SERVER_ADDRESS'],
                inline=False
            )
            embed.add_field(
                name="Игроков",
                value=f"{status.players.online}/{status.players.max}",
                inline=True
            )
            embed.add_field(
                name="Версия",
                value=status.version.name,
                inline=True
            )
            embed.add_field(
                name="Пинг",
                value=f"{status.latency:.1f}мс",
                inline=True
            )

            if status.players.sample:
                players = "\n".join(p.name for p in status.players.sample)
                embed.add_field(
                    name="Онлайн",
                    value=players,
                    inline=False
                )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error getting server status: {e}")
            await interaction.response.send_message(
                "❌ Не удалось получить статус сервера",
                ephemeral=True
            )

    @app_commands.command(
        name='mc_reward',
        description='Наградить игрока за время на сервере'
    )
    @app_commands.describe(
        player='Ник игрока',
        amount='Количество монет'
    )
    @requires_role('ADMIN')
    async def reward_player(
        self,
        interaction: discord.Interaction,
        player: str,
        amount: int
    ):
        """Reward a player with currency"""
        if amount <= 0:
            await interaction.response.send_message(
                ERRORS['INVALID_AMOUNT'],
                ephemeral=True
            )
            return

        # Check if player is online
        try:
            if not self.last_status:
                await interaction.response.send_message(
                    "❌ Статус сервера недоступен",
                    ephemeral=True
                )
                return

            player_online = any(
                p.name.lower() == player.lower()
                for p in (self.last_status.players.sample or [])
            )

            if not player_online:
                await interaction.response.send_message(
                    "❌ Игрок не найден на сервере",
                    ephemeral=True
                )
                return

            # Find Discord user by Minecraft nickname
            discord_member = None
            for guild_member in interaction.guild.members:
                if guild_member.display_name.lower() == player.lower():
                    discord_member = guild_member
                    break

            if not discord_member:
                await interaction.response.send_message(
                    "❌ Не удалось найти Discord пользователя с таким ником",
                    ephemeral=True
                )
                return

            # Add reward
            economy_cog = self.bot.get_cog('Economy')
            if not economy_cog:
                await interaction.response.send_message(
                    ERRORS['ECONOMY_MODULE_ERROR'],
                    ephemeral=True
                )
                return

            economy_cog.get_balance(discord_member.id)  # Ensure account exists
            economy_cog.accounts[discord_member.id] += amount

            embed = discord.Embed(
                title="Награда за игру",
                color=discord.Color.gold()
            )
            embed.add_field(name="Игрок", value=player, inline=True)
            embed.add_field(
                name="Награда",
                value=f"{CURRENCY['SYMBOL']} {economy_cog.format_amount(amount)}",
                inline=True
            )
            embed.add_field(
                name="Новый баланс",
                value=f"{CURRENCY['SYMBOL']} {economy_cog.format_amount(economy_cog.accounts[discord_member.id])}",
                inline=False
            )
            embed.set_footer(
                text=f"Выдано администратором: {interaction.user.name}"
            )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error rewarding player: {e}")
            await interaction.response.send_message(
                f"❌ Произошла ошибка: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Minecraft(bot))