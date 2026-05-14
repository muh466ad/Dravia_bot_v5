"""cogs/citizen_id.py — Dravia National ID System"""
import discord
from discord import app_commands
from discord.ext import commands
import json, time
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))
CURRENCY = cfg.get("currency", "Dravio")

class CitizenID(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="register", description="🪪 Register for your official Dravia ID")
    @app_commands.guilds(GUILD)
    async def register(self, interaction: discord.Interaction):
        existing = db.get_citizen(interaction.user.id)
        if existing:
            return await interaction.response.send_message(f"✅ You already have ID `{existing['id_number']}`!", ephemeral=True)

        modal = discord.ui.Modal(title="Dravia Citizen Registration")
        modal.add_item(discord.ui.TextInput(label="Full Name", max_length=50, placeholder="e.g. John Doe"))
        modal.add_item(discord.ui.TextInput(label="Address/Region", max_length=100, placeholder="e.g. Capital District"))
        modal.add_item(discord.ui.TextInput(label="Occupation", max_length=50, placeholder="e.g. Miner, Student"))

        async def on_submit(m_int: discord.Interaction):
            name = m_int.data["components"][0]["components"][0]["value"]
            addr = m_int.data["components"][1]["components"][0]["value"]
            job  = m_int.data["components"][2]["components"][0]["value"]
            
            new_id = db.register_citizen(m_int.user.id, name, addr, job)
            await m_int.response.send_message(
                f"✅ **Registration Complete!**\n🆔 ID: `{new_id}`\n🏅 Tier: Full Citizen\n\nUse `/citizenid` to view your card.", ephemeral=True)
        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

    @app_commands.command(name="citizenid", description="🪪 View your official Dravia ID card")
    @app_commands.guilds(GUILD)
    async def citizenid(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        citizen = db.get_citizen(target.id)
        if not citizen:
            return await interaction.response.send_message("❌ Not registered. Use `/register` first.", ephemeral=True)
        
        status_emoji = {"active": "🟢", "suspended": "🔴", "revoked": "⚫"}.get(citizen["status"], "⚪")
        e = utils.embed("🪪 Dravia National ID", color=0x2C3E50)
        e.set_thumbnail(url=target.display_avatar.url)
        e.add_field(name="🆔 ID Number", value=f"`{citizen['id_number']}`", inline=True)
        e.add_field(name="👤 Full Name", value=citizen["full_name"], inline=True)
        e.add_field(name="📊 Status", value=f"{status_emoji} {citizen['status'].title()}", inline=True)
        e.add_field(name="🏅 Tier", value=citizen["tier"].replace("_", " ").title(), inline=True)
        e.add_field(name="🏠 Address", value=citizen["address"], inline=True)
        e.add_field(name="💼 Occupation", value=citizen["occupation"], inline=True)
        e.add_field(name="📅 Issued", value=citizen["issued_at"][:10], inline=True)
        e.add_field(name="⚠️ Flags", value=", ".join(citizen.get("flags", [])) or "None", inline=True)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="id_check", description="🔍 Verify a citizen's ID [Admin/Judge]")
    @app_commands.guilds(GUILD)
    async def id_check(self, interaction: discord.Interaction, user: discord.Member):
        if not utils.is_admin(interaction.member) and not utils.is_judge(interaction.member):
            return await interaction.response.send_message("❌ Government clearance required.", ephemeral=True)
        c = db.get_citizen(user.id)
        if not c: return await interaction.response.send_message("❌ User is not registered.", ephemeral=True)
        e = utils.embed("🔍 ID Verification", color=0x3498DB)
        e.add_field(name="🆔 ID", value=c["id_number"], inline=True)
        e.add_field(name="👤 Name", value=c["full_name"], inline=True)
        e.add_field(name="📊 Status", value=c["status"], inline=True)
        e.add_field(name="⚠️ Flags", value=str(len(c.get("flags", []))), inline=True)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="id_suspend", description="🔴 Suspend a citizen's ID [Admin/Judge]")
    @app_commands.guilds(GUILD)
    async def id_suspend(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not utils.is_admin(interaction.member) and not utils.is_judge(interaction.member):
            return await interaction.response.send_message("❌ Government clearance required.", ephemeral=True)
        db.update_citizen_status(user.id, "suspended", reason=reason)
        await interaction.response.send_message(f"✅ `{db.get_citizen(user.id)['id_number']}` suspended for {user.mention}\n📝 Reason: {reason}")

    @app_commands.command(name="id_revoke", description="⚫ Permanently revoke citizenship [Admin Only]")
    @app_commands.guilds(GUILD)
    async def id_revoke(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admins only.", ephemeral=True)
        db.update_citizen_status(user.id, "revoked", reason=reason)
        await interaction.response.send_message(f"⚫ `{db.get_citizen(user.id)['id_number']}` revoked. {user.mention} is no longer a citizen.\n📝 Reason: {reason}")

async def setup(bot): await bot.add_cog(CitizenID(bot))
