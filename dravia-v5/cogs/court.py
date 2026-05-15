"""cogs/court.py — Court system"""
import discord
from discord import app_commands
from discord.ext import commands
import json
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))

class Court(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="fine", description="Issue fine [Judge]")
    @app_commands.guilds(GUILD)
    @app_commands.describe(citizen="Who", amount="Amount", reason="Reason")
    async def fine(self, interaction: discord.Interaction, citizen: discord.Member, amount: int, reason: str):
        if not utils.is_judge(interaction.member):
            return await interaction.response.send_message("❌ Judges only!", ephemeral=True)
        
        data = db.get_user(citizen.id, cfg["starting_balance"])
        actual = min(amount, data["balance"])
        
        db.update_balance(citizen.id, -actual, f"FINE: {reason}", cfg["starting_balance"])
        db.update_treasury(actual, f"Fine from {citizen.name}: {reason}")
        
        e = utils.embed("⚖️ Fine Issued", color=utils.RED)
        e.add_field(name="👤 Citizen", value=citizen.mention, inline=True)
        e.add_field(name="💸 Fine", value=utils.money(actual), inline=True)
        e.add_field(name="📝 Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=e)

async def setup(bot): await bot.add_cog(Court(bot))
