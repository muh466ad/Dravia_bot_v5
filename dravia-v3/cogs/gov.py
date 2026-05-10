"""cogs/gov.py — Dravia Government Commands"""

import discord
from discord import app_commands
from discord.ext import commands
import json
import database as db
import utils

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD    = discord.Object(id=int(cfg["guild_id"]))
STARTING = cfg["starting_balance"]


class Gov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    gov = app_commands.Group(name="gov", description="Government treasury commands [Admin only]",
                              guild_ids=[int(cfg["guild_id"])])

    @gov.command(name="give", description="Give Drav to a citizen")
    @app_commands.describe(citizen="Who to pay", amount="Amount", reason="Reason")
    async def give(self, interaction: discord.Interaction,
                   citizen: discord.Member, amount: int, reason: str = "Government payment"):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        new_bal = db.update_balance(citizen.id, amount, reason, STARTING)
        e = utils.embed("🏛️ Treasury Payment", color=utils.GREEN)
        e.add_field(name="📥 Recipient", value=citizen.mention,       inline=True)
        e.add_field(name="💰 Amount",   value=utils.money(amount),    inline=True)
        e.add_field(name="📝 Reason",   value=reason,                 inline=False)
        e.add_field(name="💳 New Bal",  value=utils.money(new_bal),   inline=True)
        await interaction.response.send_message(embed=e)

    @gov.command(name="take", description="Remove Drav from a citizen")
    @app_commands.describe(citizen="Who to charge", amount="Amount", reason="Reason")
    async def take(self, interaction: discord.Interaction,
                   citizen: discord.Member, amount: int, reason: str = "Government deduction"):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        new_bal = db.update_balance(citizen.id, -amount, reason, STARTING)
        e = utils.embed("🏛️ Treasury Deduction", color=utils.RED)
        e.add_field(name="📤 From",    value=citizen.mention,      inline=True)
        e.add_field(name="💸 Amount",  value=utils.money(amount),  inline=True)
        e.add_field(name="📝 Reason",  value=reason,               inline=False)
        e.add_field(name="💳 New Bal", value=utils.money(new_bal), inline=True)
        await interaction.response.send_message(embed=e)

    @gov.command(name="salary", description="Pay all members of a role")
    @app_commands.describe(role="The role to pay", amount="Per person", reason="Pay period")
    async def salary(self, interaction: discord.Interaction,
                     role: discord.Role, amount: int, reason: str = "Weekly salary"):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        await interaction.response.defer()

        count = 0
        for member in role.members:
            if not member.bot:
                db.update_balance(member.id, amount, f"Salary ({role.name}): {reason}", STARTING)
                count += 1

        e = utils.embed("💼 Salary Disbursement", color=utils.GREEN)
        e.add_field(name="👥 Role",        value=role.mention,              inline=True)
        e.add_field(name="💰 Per Person",  value=utils.money(amount),       inline=True)
        e.add_field(name="👤 Paid",        value=f"{count} citizens",       inline=True)
        e.add_field(name="💸 Total Spent", value=utils.money(amount*count), inline=True)
        e.add_field(name="📝 Period",      value=reason,                    inline=False)
        await interaction.followup.send(embed=e)

    @gov.command(name="stats", description="View economy statistics")
    async def stats(self, interaction: discord.Interaction):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)

        raw      = db.raw()
        users    = raw.get("users", {})
        cases    = raw.get("cases", [])
        art      = raw.get("art_listings", [])
        lottery  = raw.get("lottery", {})

        total    = sum(u.get("balance", 0) + u.get("bank", 0) for u in users.values())
        wallets  = sum(u.get("balance", 0) for u in users.values())
        banks    = sum(u.get("bank", 0)    for u in users.values())
        avg      = round(total / len(users), 1) if users else 0
        richest  = max(users.values(), key=lambda u: u.get("balance", 0), default={})
        open_c   = sum(1 for c in cases if c["status"] == "open")

        e = utils.embed("📊 Dravia Economy Report", color=utils.BLUE)
        e.add_field(name="👥 Citizens",          value=f"{len(users):,}",          inline=True)
        e.add_field(name="💰 Total in Wallets",  value=utils.money(wallets),        inline=True)
        e.add_field(name="🏦 Total in Banks",    value=utils.money(banks),          inline=True)
        e.add_field(name="📈 Total Circulation", value=utils.money(total),          inline=True)
        e.add_field(name="📊 Avg Balance",       value=f"{avg:,} {cfg['currency']}", inline=True)
        e.add_field(name="🎨 Art For Sale",      value=str(len(art)),              inline=True)
        e.add_field(name="⚖️ Open Cases",        value=str(open_c),                inline=True)
        e.add_field(name="📋 Total Cases",       value=str(len(cases)),            inline=True)
        e.add_field(name="🎰 Lottery Pool",      value=utils.money(lottery.get("pool", 0)), inline=True)
        e.set_footer(text="Dravia Treasury Department • Confidential")
        await interaction.response.send_message(embed=e, ephemeral=True)

    @gov.command(name="reset", description="Reset a citizen's balance [Admin only]")
    @app_commands.describe(citizen="Who to reset", amount="Set their balance to this amount")
    async def reset(self, interaction: discord.Interaction, citizen: discord.Member, amount: int = 100):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        raw = db.raw()
        uid = str(citizen.id)
        if uid in raw["users"]:
            raw["users"][uid]["balance"] = amount
            db._save(raw)
        e = utils.embed("🔄 Balance Reset", color=utils.ORANGE)
        e.add_field(name="👤 Citizen",     value=citizen.mention,    inline=True)
        e.add_field(name="💰 New Balance", value=utils.money(amount), inline=True)
        await interaction.response.send_message(embed=e, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Gov(bot))
