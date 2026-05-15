"""cogs/auctions.py — Auction system (coming soon)"""
import discord
from discord.ext import commands

class Auctions(commands.Cog):
    def __init__(self, bot): self.bot = bot

async def setup(bot): await bot.add_cog(Auctions(bot))
