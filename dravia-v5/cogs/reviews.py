"""cogs/reviews.py — Review system (coming soon)"""
import discord
from discord.ext import commands

class Reviews(commands.Cog):
    def __init__(self, bot): self.bot = bot

async def setup(bot): await bot.add_cog(Reviews(bot))
