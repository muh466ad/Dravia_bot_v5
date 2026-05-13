"""cogs/citizen_id.py — Mandatory Citizen ID System"""

import discord
from discord import app_commands
from discord.ext import commands
import database as db
import utils
import json

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))

class CitizenID(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cid = app_commands.Group(name="citizenid", description="Official Dravia ID System")

    @app_commands.command(name="register", description="Register for your official Dravia Citizen ID")
    @app_commands.guilds(GUILD)
    async def register(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        user = db.get_user(interaction.user.id, cfg["starting_balance"])
        
        if user.get("citizen_id") and user.get("citizen_id") != "PENDING":
            return await interaction.response.send_message("✅ You already have a valid Citizen ID!", ephemeral=True)

        cid = db.register_citizen(interaction.user.id, interaction.user.display_name)
        
        e = utils.embed("🪪 Dravia National ID Issued!", color=utils.GREEN)
        e.add_field(name="👤 Citizen", value=interaction.user.mention, inline=True)
        e.add_field(name="🆔 ID Number", value=f"`{cid}`", inline=True)
        e.add_field(name="📅 Issued", value="Today", inline=True)
        e.set_footer(text="Welcome to Dravia — Nation of Law and Unity")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="show", description="View your Official Citizen ID Card")
    @app_commands.guilds(GUILD)
    async def show(self, interaction: discord.Interaction):
        data = db.get_user(interaction.user.id)
        if not data.get("citizen_id") or data.get("citizen_id") == "PENDING":
            return await interaction.response.send_message("❌ You are not registered! Use `/register` first.", ephemeral=True)

        e = utils.embed("🪪 DRAVIA NATIONAL ID", color=0x2C3E50)
        e.set_thumbnail(url=interaction.user.display_avatar.url)
        e.add_field(name="Full Name", value=interaction.user.display_name, inline=True)
        e.add_field(name="ID Number", value=f"`{data['citizen_id']}`", inline=True)
        e.add_field(name="Status", value=data.get("id_status", "Active"), inline=True)
        e.add_field(name="Issued", value=data.get("joined","?")[:10], inline=True)
        await interaction.response.send_message(embed=e)

    # Government Commands
    id_group = app_commands.Group(name="id", description="Government ID Management", guild_ids=[int(cfg["guild_id"])])

    @id_group.command(name="check", description="Check someone's ID [Police/Admin]")
    @app_commands.describe(target="Citizen to check")
    async def id_check(self, interaction: discord.Interaction, target: discord.Member):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Government Officials only!", ephemeral=True)
        
        data = db.get_user(target.id)
        status = data.get("id_status", "Unregistered")
        e = utils.embed(f"🪪 ID Check — {target.display_name}", color=utils.BLUE)
        e.add_field(name="ID Number", value=data.get("citizen_id", "None"), inline=True)
        e.add_field(name="Status", value=status, inline=True)
        await interaction.response.send_message(embed=e)

async def setup(bot): 
    await bot.add_cog(CitizenID(bot))
