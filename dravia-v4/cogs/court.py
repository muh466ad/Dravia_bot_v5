"""cogs/court.py — Full court system with evidence and appeals"""

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
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="complaint", description=f"File a court complaint (costs {cfg['complaint_fee']} Drav)")
    @app_commands.guilds(GUILD)
    @app_commands.describe(against="Who you're filing against", reason="What happened?", lawyer="Hire a lawyer? (optional)")
    async def complaint(self, interaction: discord.Interaction,
                        against: discord.Member, reason: str, lawyer: discord.Member = None):
        p = interaction.user
        if against.id == p.id or against.bot:
            return await interaction.response.send_message("❌ Invalid target!", ephemeral=True)

        data = db.get_user(p.id, STARTING)
        total_cost = COMP_FEE
        if lawyer:
            total_cost += cfg.get("lawyer_fee", 30)

        if data["balance"] < total_cost:
            return await interaction.response.send_message(
                f"❌ Filing costs {utils.money(total_cost)} (includes lawyer fee). You have {utils.money(data['balance'])}.", ephemeral=True)

        db.update_balance(p.id, -total_cost, f"Court filing fee vs {against.name}", STARTING)
        if lawyer:
            db.update_balance(lawyer.id, cfg.get("lawyer_fee",30), f"Lawyer fee from {p.name}", STARTING)

        case_id = db.add_case(p.id, against.id, reason, COMP_FEE, lawyer.id if lawyer else None)

        e = utils.embed(f"📜 Case #{case_id} Filed", color=utils.BLUE)
        e.add_field(name="👤 Plaintiff",  value=p.mention,              inline=True)
        e.add_field(name="🧑 Defendant",  value=against.mention,        inline=True)
        e.add_field(name="💸 Fee Paid",   value=utils.money(total_cost), inline=True)
        if lawyer:
            e.add_field(name="💼 Lawyer", value=lawyer.mention,         inline=True)
        e.add_field(name="📝 Complaint",  value=reason,                 inline=False)
        e.add_field(name="📊 Status",     value="🟡 Open — Awaiting Judge", inline=True)
        e.set_footer(text=f"Case #{case_id} • Use /evidence {case_id} to submit evidence!")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="evidence", description="Submit evidence for a court case")
    @app_commands.guilds(GUILD)
    @app_commands.describe(case_id="The case number", evidence="Your evidence or statement")
    async def evidence(self, interaction: discord.Interaction, case_id: int, evidence: str):
        case = db.get_case(case_id)
        if not case or case["status"] != "open":
            return await interaction.response.send_message(f"❌ Case #{case_id} not found or not open!", ephemeral=True)

        uid = str(interaction.user.id)
        if uid not in (case["plaintiff"], case["defendant"],
                       case.get("lawyer_plaintiff",""), str(cfg.get("judge_role_id",""))):
            if not utils.is_judge(interaction.member):
                return await interaction.response.send_message("❌ Only plaintiff, defendant, or their lawyer can submit evidence!", ephemeral=True)

        db.add_evidence(case_id, interaction.user.id, evidence)
        e = utils.embed(f"📋 Evidence Submitted — Case #{case_id}", color=utils.BLUE)
        e.add_field(name="👤 Submitted by", value=interaction.user.mention, inline=True)
        e.add_field(name="📝 Evidence",     value=evidence,                 inline=False)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="caseinfo", description="View full details of a court case")
    @app_commands.guilds(GUILD)
    @app_commands.describe(case_id="The case number")
    async def caseinfo(self, interaction: discord.Interaction, case_id: int):
        case = db.get_case(case_id)
        if not case:
            return await interaction.response.send_message(f"❌ Case #{case_id} not found!", ephemeral=True)

        status_emoji = {"open":"🟡","closed":"🟢","appealed":"🔴"}.get(case["status"],"⚪")
        e = utils.embed(f"⚖️ Case #{case_id}", color=utils.BLUE)
        e.add_field(name="👤 Plaintiff",  value=f"<@{case['plaintiff']}>",  inline=True)
        e.add_field(name="🧑 Defendant",  value=f"<@{case['defendant']}>",  inline=True)
        e.add_field(name="📊 Status",     value=f"{status_emoji} {case['status'].title()}", inline=True)
        e.add_field(name="📝 Complaint",  value=case["reason"],             inline=False)
        if case.get("lawyer_plaintiff"):
            e.add_field(name="💼 Lawyer", value=f"<@{case['lawyer_plaintiff']}>", inline=True)
        if case.get("verdict"):
            e.add_field(name="🏆 Verdict", value=case["verdict"].title(),  inline=True)
        if case.get("notes"):
            e.add_field(name="📋 Judge Notes", value=case["notes"],        inline=False)
        evidence = case.get("evidence", [])
        if evidence:
            ev_lines = [f"**<@{ev['user']}>**: {ev['text']}" for ev in evidence[-5:]]
            e.add_field(name=f"📋 Evidence ({len(evidence)} item(s))", value="\n".join(ev_lines), inline=False)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="fine", description="Issue a fine [Judge/Admin only]")
    @app_commands.guilds(GUILD)
    @app_commands.describe(citizen="Who to fine", amount="Amount", reason="Reason")
    async def fine(self, interaction: discord.Interaction, citizen: discord.Member, amount: int, reason: str):
        if not utils.is_judge(interaction.member):
            return await interaction.response.send_message("❌ Judges and Admins only!", ephemeral=True)
        data    = db.get_user(citizen.id, STARTING)
        actual  = min(amount, data["balance"])
        new_bal = db.update_balance(citizen.id, -actual, f"FINE: {reason}", STARTING)
        e = utils.embed("⚖️ Fine Issued", color=utils.RED)
        e.add_field(name="👤 Citizen",   value=citizen.mention,          inline=True)
        e.add_field(name="👨‍⚖️ Judge",    value=interaction.user.mention, inline=True)
        e.add_field(name="💸 Fine",      value=utils.money(actual),      inline=True)
        e.add_field(name="📝 Reason",    value=reason,                   inline=False)
        e.add_field(name="💰 Remaining", value=utils.money(new_bal),     inline=True)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="verdict", description="Issue a verdict [Judge only]")
    @app_commands.guilds(GUILD)
    @app_commands.describe(case_id="Case number", winner="Who won?", notes="Your ruling")
    @app_commands.choices(winner=[
        app_commands.Choice(name="Plaintiff wins",  value="plaintiff"),
        app_commands.Choice(name="Defendant wins",  value="defendant"),
        app_commands.Choice(name="Case Dismissed",  value="dismissed"),
    ])
    async def verdict(self, interaction: discord.Interaction, case_id: int, winner: str, notes: str = "No notes."):
        if not utils.is_judge(interaction.member):
            return await interaction.response.send_message("❌ Judges only!", ephemeral=True)
        case = db.close_case(case_id, winner, notes)
        if not case:
            return await interaction.response.send_message(f"❌ Case #{case_id} not found or already closed!", ephemeral=True)
        db.update_balance(interaction.user.id, JUDGE_PAY, f"Judge pay: Case #{case_id}", STARTING)
        if winner == "plaintiff":
            db.update_balance(case["plaintiff"], case["fee"], f"Fee refund: Won Case #{case_id}", STARTING)
            db.unlock_achievement(case["plaintiff"], "won_case")
            winner_text = f"<@{case['plaintiff']}> **(Plaintiff)** 🏆 *(fee refunded!)*"
        elif winner == "defendant":
            winner_text = f"<@{case['defendant']}> **(Defendant)** 🏆"
        else:
            winner_text = "⚖️ Case Dismissed"
        e = utils.embed(f"⚖️ Case #{case_id} — Verdict", color=utils.GREEN)
        e.add_field(name="👤 Plaintiff", value=f"<@{case['plaintiff']}>",  inline=True)
        e.add_field(name="🧑 Defendant", value=f"<@{case['defendant']}>",  inline=True)
        e.add_field(name="🏆 Ruling",    value=winner_text,                inline=False)
        e.add_field(name="📝 Notes",     value=notes,                      inline=False)
        e.add_field(name="👨‍⚖️ Judge",    value=interaction.user.mention,   inline=True)
        e.add_field(name="💰 Judge Pay", value=utils.money(JUDGE_PAY),     inline=True)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="appeal", description="Appeal a closed court case")
    @app_commands.guilds(GUILD)
    @app_commands.describe(case_id="The case to appeal", reason="Grounds for appeal")
    async def appeal(self, interaction: discord.Interaction, case_id: int, reason: str):
        case = db.get_case(case_id)
        if not case:
            return await interaction.response.send_message(f"❌ Case #{case_id} not found!", ephemeral=True)
        uid = str(interaction.user.id)
        if uid not in (case["plaintiff"], case["defendant"]):
            return await interaction.response.send_message("❌ Only parties involved can appeal!", ephemeral=True)
        data = db.get_user(interaction.user.id, STARTING)
        if data["balance"] < COMP_FEE:
            return await interaction.response.send_message(f"❌ Appeal costs {utils.money(COMP_FEE)}.", ephemeral=True)
        db.update_balance(interaction.user.id, -COMP_FEE, f"Appeal fee: Case #{case_id}", STARTING)
        result = db.appeal_case(case_id, reason)
        if not result:
            return await interaction.response.send_message("❌ Case cannot be appealed!", ephemeral=True)
        e = utils.embed(f"📜 Case #{case_id} — Appeal Filed", color=utils.ORANGE)
        e.add_field(name="👤 Appellant", value=interaction.user.mention, inline=True)
        e.add_field(name="📝 Grounds",  value=reason,                   inline=False)
        e.set_footer(text="A judge will review this appeal")
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="cases", description="View all open court cases")
    @app_commands.guilds(GUILD)
    async def cases(self, interaction: discord.Interaction):
        open_cases = db.get_open_cases()
        if not open_cases:
            return await interaction.response.send_message("✅ No open cases!", ephemeral=True)
        lines = [
            f"**Case #{c['id']}** {'🔴 APPEAL' if c['status']=='appealed' else '🟡'} | "
            f"<@{c['plaintiff']}> vs <@{c['defendant']}>\n📝 _{c['reason'][:60]}_"
            for c in open_cases
        ]
        e = utils.embed("📋 Open Court Cases", "\n\n".join(lines), color=utils.BLUE)
        e.set_footer(text="Use /caseinfo [id] for full details")
        await interaction.response.send_message(embed=e)


async def setup(bot): await bot.add_cog(Court(bot))
