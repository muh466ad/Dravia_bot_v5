"""cogs/registration.py — Citizen ID & Registration System"""

import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD = discord.Object(id=int(cfg["guild_id"]))

DISTRICTS = [
    "Capital District",
    "Northern Region",
    "Southern Region",
    "Coastal Region",
    "Mountain Region"
]

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="register", description="🆔 Register as a Dravia citizen (REQUIRED)")
    @app_commands.guilds(GUILD)
    @app_commands.describe(full_name="Your full roleplay name", district="Your district of residence")
    @app_commands.choices(district=[app_commands.Choice(name=d, value=d) for d in DISTRICTS])
    async def register(self, interaction: discord.Interaction, full_name: str, district: str):
        citizen_id, status = db.register_citizen(interaction.user.id, full_name, district)
        
        if status == "already_registered":
            existing = db.get_citizen(interaction.user.id)
            e = utils.embed("❌ Already Registered",
                f"You are already registered!\n**Citizen ID:** {existing['citizen_id']}\nUse `/citizenid` to view your ID card.",
                color=utils.ORANGE)
            return await interaction.response.send_message(embed=e, ephemeral=True)
        
        e = utils.embed("✅ REGISTRATION APPROVED", color=utils.GREEN)
        e.description = (
            f"Your Citizen ID has been issued!\n\n"
            f"🆔 **Citizen ID:** {citizen_id}\n"
            f"👤 **Name:** {full_name}\n"
            f"🏠 **District:** {district}\n"
            f"📅 **Issued:** {datetime.now().strftime('%B %d, %Y')}\n"
            f"✅ **Status:** Active Citizen\n\n"
            f"You may now participate in all government services!\n"
            f"Use `/citizenid` to view your full ID card."
        )
        e.set_thumbnail(url=interaction.user.display_avatar.url)
        e.set_footer(text="🆔 Ministry of Interior Affairs • Republic of Dravia")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="citizenid", description="🪪 View your official Citizen ID card")
    @app_commands.guilds(GUILD)
    async def citizenid(self, interaction: discord.Interaction):
        citizen = db.get_citizen(interaction.user.id)
        
        if not citizen:
            e = utils.embed("❌ Not Registered",
                "You are not a registered citizen!\nUse `/register` to obtain your Citizen ID.",
                color=utils.RED)
            return await interaction.response.send_message(embed=e, ephemeral=True)
        
        status_emoji = {"active": "✅", "suspended": "⚠️", "revoked": "❌"}.get(citizen["status"], "⚪")
        tier_text = citizen["tier"].replace("_", " ").title()
        
        issued_date = datetime.fromisoformat(citizen["registration_date"]).strftime("%b %d, %Y")
        expiry_date = datetime.fromisoformat(citizen["expiry_date"]).strftime("%b %d, %Y")
        
        user_data = db.get_user(interaction.user.id, cfg["starting_balance"])
        level = utils.xp_to_level(user_data.get("xp", 0))
        
        e = utils.embed("", color=utils.DARK)
        e.title = None
        
        card = f"""
```
╔═══════════════════════════════════════════════╗
║      🦢 REPUBLIC OF DRAVIA                    ║
║         NATIONAL IDENTITY CARD                ║
╠═══════════════════════════════════════════════╣
║                                               ║
║  CITIZEN ID:  {citizen['citizen_id']:<30}  ║
║  STATUS:      {status_emoji} {citizen['status'].upper():<27}  ║
║                                               ║
║  FULL NAME:   {citizen['full_name']:<30}  ║
║  DISTRICT:    {citizen['district']:<30}  ║
║  TIER:        {tier_text:<30}  ║
║                                               ║
║  ISSUED:      {issued_date:<30}  ║
║  EXPIRES:     {expiry_date:<30}  ║
║                                               ║
║  OCCUPATION:  {(citizen.get('occupation') or 'Unemployed'):<30}  ║
║  LEVEL:       {f'Level {level} - {utils.level_title(level)}':<30}  ║
║                                               ║
╠═══════════════════════════════════════════════╣
║  🔐 VERIFIED CITIZEN         {interaction.user.name:<17}║
╚═══════════════════════════════════════════════╝
```
"""
        
        e.description = card
        e.set_thumbnail(url=interaction.user.display_avatar.url)
        
        if citizen.get("flags"):
            e.add_field(name="⚠️ Flags", value="\n".join(citizen["flags"][-3:]), inline=False)
        
        e.set_footer(text="🆔 Ministry of Interior Affairs • Republic of Dravia")
        await interaction.response.send_message(embed=e)

    id_group = app_commands.Group(name="id", description="ID management commands", guild_ids=[int(cfg["guild_id"])])

    @id_group.command(name="renew", description="Renew your Citizen ID")
    async def id_renew(self, interaction: discord.Interaction):
        citizen = db.get_citizen(interaction.user.id)
        if not citizen:
            return await interaction.response.send_message("❌ You are not registered!", ephemeral=True)
        
        user_data = db.get_user(interaction.user.id, cfg["starting_balance"])
        cost = cfg["id_renewal_cost"]
        
        if user_data["balance"] < cost:
            return await interaction.response.send_message(
                f"❌ ID renewal costs {utils.money(cost)}. You have {utils.money(user_data['balance'])}.",
                ephemeral=True)
        
        db.update_balance(interaction.user.id, -cost, "ID renewal fee", cfg["starting_balance"])
        db.renew_id(interaction.user.id)
        db.update_treasury(cost, f"ID renewal from {citizen['full_name']}")
        
        e = utils.embed("✅ ID Renewed", color=utils.GREEN)
        e.description = f"Your Citizen ID has been renewed for 5 more years!\n💸 Fee: {utils.money(cost)}"
        await interaction.response.send_message(embed=e)

    @id_group.command(name="check", description="Check someone's ID status [Police/Admin]")
    @app_commands.describe(user="Citizen to check")
    async def id_check(self, interaction: discord.Interaction, user: discord.Member):
        if not utils.is_police(interaction.member) and not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Police or Admin only!", ephemeral=True)
        
        citizen = db.get_citizen(user.id)
        if not citizen:
            e = utils.embed("❌ Not Registered",
                f"{user.display_name} is not a registered citizen!",
                color=utils.RED)
            return await interaction.response.send_message(embed=e, ephemeral=True)
        
        status_emoji = {"active": "✅", "suspended": "⚠️", "revoked": "❌"}.get(citizen["status"], "⚪")
        
        e = utils.embed(f"🔍 ID Verification — {user.display_name}", color=utils.BLUE)
        e.set_thumbnail(url=user.display_avatar.url)
        e.add_field(name="🆔 ID Number", value=citizen["citizen_id"], inline=True)
        e.add_field(name="📊 Status", value=f"{status_emoji} {citizen['status'].title()}", inline=True)
        e.add_field(name="🏠 District", value=citizen["district"], inline=True)
        e.add_field(name="👤 Full Name", value=citizen["full_name"], inline=True)
        e.add_field(name="💼 Occupation", value=citizen.get("occupation") or "Unemployed", inline=True)
        e.add_field(name="🏢 Employer", value=citizen.get("employer") or "None", inline=True)
        
        if citizen.get("flags"):
            e.add_field(name="⚠️ Flags", value="\n".join(citizen["flags"][-3:]), inline=False)
        else:
            e.add_field(name="✅ Flags", value="None", inline=False)
        
        await interaction.response.send_message(embed=e, ephemeral=True)

    @id_group.command(name="suspend", description="Suspend a citizen's ID [Judge/Admin]")
    @app_commands.describe(user="Citizen to suspend", reason="Reason for suspension")
    async def id_suspend(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not utils.is_judge(interaction.member) and not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Judge or Admin only!", ephemeral=True)
        
        if not db.is_registered(user.id):
            return await interaction.response.send_message("❌ User is not registered!", ephemeral=True)
        
        db.suspend_citizen(user.id, reason)
        citizen = db.get_citizen(user.id)
        
        e = utils.embed("⚠️ Citizenship Suspended", color=utils.ORANGE)
        e.add_field(name="👤 Citizen", value=f"{user.mention}\n{citizen['citizen_id']}", inline=True)
        e.add_field(name="👨‍⚖️ By", value=interaction.user.mention, inline=True)
        e.add_field(name="📝 Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=e)

    @id_group.command(name="flag", description="Add a warning flag to citizen's ID [Police]")
    @app_commands.describe(user="Citizen to flag", flag="Warning flag text")
    async def id_flag(self, interaction: discord.Interaction, user: discord.Member, flag: str):
        if not utils.is_police(interaction.member):
            return await interaction.response.send_message("❌ Police only!", ephemeral=True)
        
        if not db.is_registered(user.id):
            return await interaction.response.send_message("❌ User is not registered!", ephemeral=True)
        
        db.add_flag(user.id, flag)
        citizen = db.get_citizen(user.id)
        
        e = utils.embed("🚩 Flag Added", color=utils.ORANGE)
        e.add_field(name="👤 Citizen", value=f"{user.mention}\n{citizen['citizen_id']}", inline=True)
        e.add_field(name="👮 By", value=interaction.user.mention, inline=True)
        e.add_field(name="🚩 Flag", value=flag, inline=False)
        await interaction.response.send_message(embed=e, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Registration(bot))
