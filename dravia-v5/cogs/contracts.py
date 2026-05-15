"""cogs/contracts.py — Contracts & Escrow (coming soon)"""
import discord
from discord.ext import commands

class Contracts(commands.Cog):
    def __init__(self, bot): self.bot = bot

async def setup(bot): await bot.add_cog(Contracts(bot))
