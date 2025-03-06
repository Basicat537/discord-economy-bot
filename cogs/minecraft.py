import discord
from discord.ext import commands
from utils.permissions import check_admin
from utils.storage import JsonStorage
from utils.logger import Logger
import os

class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.storage = JsonStorage('data/minecraft.json')
        self.logger = Logger('minecraft')

    @commands.command(name='linkmc')
    async def link_minecraft(self, ctx, minecraft_username: str):
        """Link your Discord account to Minecraft username"""
        user_id = str(ctx.author.id)
        self.storage.set_minecraft_link(user_id, minecraft_username)
        
        embed = discord.Embed(
            title="Minecraft Account Linked",
            description=f"Your Discord account is now linked to Minecraft username: {minecraft_username}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        self.logger.log(f"User {user_id} linked Minecraft account: {minecraft_username}")

    @commands.command(name='unlinkmc')
    async def unlink_minecraft(self, ctx):
        """Unlink your Minecraft account"""
        user_id = str(ctx.author.id)
        self.storage.remove_minecraft_link(user_id)
        
        embed = discord.Embed(
            title="Minecraft Account Unlinked",
            description="Your Minecraft account has been unlinked",
            color=discord.Color.yellow()
        )
        await ctx.send(embed=embed)
        self.logger.log(f"User {user_id} unlinked Minecraft account")

    @commands.command(name='mcstatus')
    async def minecraft_status(self, ctx):
        """Check if your Discord account is linked to Minecraft"""
        user_id = str(ctx.author.id)
        minecraft_username = self.storage.get_minecraft_username(user_id)
        
        if minecraft_username:
            embed = discord.Embed(
                title="Minecraft Status",
                description=f"Your account is linked to: {minecraft_username}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Minecraft Status",
                description="Your account is not linked to Minecraft",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)

    @commands.command(name='mcreward')
    async def minecraft_reward(self, ctx):
        """Get reward for linked Minecraft account"""
        user_id = str(ctx.author.id)
        try:
            amount = self.storage.give_minecraft_reward(user_id)
            embed = discord.Embed(
                title="Minecraft Reward",
                description=f"You received {amount} coins for having a linked Minecraft account!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except ValueError as e:
            await ctx.send(str(e))

async def setup(bot):
    await bot.add_cog(Minecraft(bot))
