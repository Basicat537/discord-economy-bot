import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from utils.permissions import check_admin
from utils.storage import JsonStorage
from utils.logger import Logger

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.storage = JsonStorage('data/economy.json')
        self.logger = Logger('economy')

    @commands.command(name='balance')
    async def balance(self, ctx):
        """Check your current balance"""
        user_id = str(ctx.author.id)
        balance = self.storage.get_user_balance(user_id)

        embed = discord.Embed(
            title="Balance",
            description=f"Your current balance: {balance} coins",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='pay')
    async def pay(self, ctx, recipient: discord.Member, amount: int):
        """Transfer coins to another user"""
        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return

        sender_id = str(ctx.author.id)
        recipient_id = str(recipient.id)

        try:
            self.storage.transfer_coins(sender_id, recipient_id, amount)
            embed = discord.Embed(
                title="Transaction Successful",
                description=f"Transferred {amount} coins to {recipient.name}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            self.logger.log(f"Transfer: {sender_id} -> {recipient_id}: {amount} coins")
        except ValueError as e:
            await ctx.send(str(e))

    @commands.command(name='addcoins')
    @check_admin()
    async def add_coins(self, ctx, user: discord.Member, amount: int):
        """Admin command to add coins to a user"""
        user_id = str(user.id)
        self.storage.add_coins(user_id, amount)
        embed = discord.Embed(
            title="Admin Action",
            description=f"Added {amount} coins to {user.name}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        self.logger.log(f"Admin added {amount} coins to {user_id}")

    @commands.command(name='removecoins')
    @check_admin()
    async def remove_coins(self, ctx, user: discord.Member, amount: int):
        """Admin command to remove coins from a user"""
        user_id = str(user.id)
        try:
            self.storage.remove_coins(user_id, amount)
            embed = discord.Embed(
                title="Admin Action",
                description=f"Removed {amount} coins from {user.name}",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            self.logger.log(f"Admin removed {amount} coins from {user_id}")
        except ValueError as e:
            await ctx.send(str(e))

async def setup(bot):
    await bot.add_cog(Economy(bot))