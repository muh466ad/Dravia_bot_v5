"""cogs/court.py — Dravia Court of Law"""

import discord
from discord import app_commands
from discord.ext import commands
import json
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD     = discord.Object(id=int(cfg["guild_id"]))
STARTING  = cfg["starting_balance"]
COMP_FEE  = cfg["complaint_fee"]
JUDGE_PAY = cfg["judge_pay"]


class Court(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="complaint", description=f"File a court complaint (costs {cfg['complaint_fee']} Drav)")
    @app_commands.guilds(GUILD)
    @app_commands.describe(against="Who you're filing against", reason="What happened?")
    async def complaint(self, interaction: discord.Interaction,
                        against: discord.Member, reason: str):
        p = interaction.user
        if against.id == p.id or against.bot:
            return await interaction.response.send_message("❌ Invalid target!", ephemeral=True)

        data = db.get_user(p.id, STARTING)
        if data["balance"] < COMP_FEE:
            e = utils.embed("❌ Insufficient Funds",
                f"Filing costs {utils.money(COMP_FEE)}. You have {utils.money(data['balance'])}.", color=utils.RED)
            return await interaction.response.send_message(embed=e, ephemeral=True)

        db.update_balance(p.id, -COMP_FEE, f"Filing fee vs {against.name}", STARTING)
        case_id = db.add_case(p.id, against.id, reason, COMP_FEE)

        e = utils.embed(f"📜 Case #{case_id} Filed", color=utils.BLUE)
        e.add_field(name="👤 Plaintiff",  value=p.mention,             inline=True)
        e.add_field(name="🧑 Defendant",  value=against.mention,       inline=True)
        e.add_field(name="💸 Filing Fee", value=utils.money(COMP_FEE), inline=True)
        e.add_field(name="📝 Complaint",  value=reason,                inline=False)
        e.add_field(name="📊 Status",     value="🟡 Open — Awaiting Judge", inline=True)
        e.set_footer(text=f"Case #{case_id} • Fee refunded if you win")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="fine", description="Issue a fine [Judge/Admin only]")
    @app_commands.guilds(GUILD)
    @app_commands.describe(citizen="Who to fine", amount="Amount in Drav", reason="Reason")
    async def fine(self, interaction: discord.Interaction,
                   citizen: discord.Member, amount: int, reason: str):
        if not utils.is_judge(interaction.member):
            return await interaction.response.send_message("❌ Judges and Admins only!", ephemeral=True)
        if citizen.bot or amount < 1:
            return await interaction.response.send_message("❌ Invalid.", ephemeral=True)

        data    = db.get_user(citizen.id, STARTING)
        actual  = min(amount, data["balance"])
        new_bal = db.update_balance(citizen.id, -actual, f"FINE: {reason}", STARTING)

        e = utils.embed("⚖️ Fine Issued", color=utils.RED)
        e.add_field(name="👤 Citizen",    value=citizen.mention,          inline=True)
        e.add_field(name="👨‍⚖️ Judge",     value=interaction.user.mention, inline=True)
        e.add_field(name="💸 Fine",       value=utils.money(actual),      inline=True)
        e.add_field(name="📝 Reason",     value=reason,                   inline=False)
        e.add_field(name="💰 Remaining",  value=utils.money(new_bal),     inline=True)
        if actual < amount:
            e.add_field(name="⚠️ Note", value="Citizen didn't have enough. Partial fine collected.", inline=False)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="verdict", description="Issue verdict on a case [Judge only]")
    @app_commands.guilds(GUILD)
    @app_commands.describe(case_id="Case number", winner="Who won?", notes="Your ruling")
    @app_commands.choices(winner=[
        app_commands.Choice(name="Plaintiff wins",  value="plaintiff"),
        app_commands.Choice(name="Defendant wins",  value="defendant"),
        app_commands.Choice(name="Case Dismissed",  value="dismissed"),
    ])
    async def verdict(self, interaction: discord.Interaction,
                      case_id: int, winner: str, notes: str = "No notes."):
        if not utils.is_judge(interaction.member):
            return await interaction.response.send_message("❌ Judges only!", ephemeral=True)

        case = db.close_case(case_id, winner, notes)
        if not case:
            return await interaction.response.send_message(
                f"❌ Case #{case_id} not found or already closed!", ephemeral=True)

        db.update_balance(interaction.user.id, JUDGE_PAY, f"Judge pay: Case #{case_id}", STARTING)

        if winner == "plaintiff":
            db.update_balance(case["plaintiff"], case["fee"], f"Fee refund: Won Case #{case_id}", STARTING)
            winner_text = f"<@{case['plaintiff']}> **(Plaintiff)** 🏆 *(fee refunded!)*"
        elif winner == "defendant":
            winner_text = f"<@{case['defendant']}> **(Defendant)** 🏆"
        else:
            winner_text = "⚖️ Case Dismissed"

        e = utils.embed(f"⚖️ Case #{case_id} — Verdict", color=utils.GREEN)
        e.add_field(name="👤 Plaintiff",  value=f"<@{case['plaintiff']}>",  inline=True)
        e.add_field(name="🧑 Defendant",  value=f"<@{case['defendant']}>",  inline=True)
        e.add_field(name="🏆 Ruling",     value=winner_text,                inline=False)
        e.add_field(name="📝 Notes",      value=notes,                      inline=False)
        e.add_field(name="👨‍⚖️ Judge",     value=interaction.user.mention,   inline=True)
        e.add_field(name="💰 Judge Pay",  value=utils.money(JUDGE_PAY),     inline=True)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="cases", description="View all open court cases")
    @app_commands.guilds(GUILD)
    async def cases(self, interaction: discord.Interaction):
        open_cases = db.get_open_cases()
        if not open_cases:
            return await interaction.response.send_message("✅ No open cases right now!", ephemeral=True)

        lines = [
            f"**Case #{c['id']}** | <@{c['plaintiff']}> vs <@{c['defendant']}>\n"
            f"📝 _{c['reason']}_ • 📅 {c['filed'][:10]}"
            for c in open_cases
        ]
        e = utils.embed("📋 Open Court Cases", "\n\n".join(lines), color=utils.BLUE)
        e.set_footer(text="Use /verdict [id] to close a case")
        await interaction.response.send_message(embed=e)


async def setup(bot):
    await bot.add_cog(Court(bot))
