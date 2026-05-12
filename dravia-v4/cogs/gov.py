"""cogs/gov.py — Government commands v4"""

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
    def __init__(self, bot): self.bot = bot

    gov = app_commands.Group(name="gov", description="Government commands [Admin]",
                              guild_ids=[int(cfg["guild_id"])])

    @gov.command(name="give", description="Give Drav to a citizen")
    @app_commands.describe(citizen="Who", amount="Amount", reason="Why")
    async def give(self, interaction: discord.Interaction, citizen: discord.Member, amount: int, reason: str = "Government payment"):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        new_bal = db.update_balance(citizen.id, amount, reason, STARTING)
        e = utils.embed("🏛️ Treasury Payment", color=utils.GREEN)
        e.add_field(name="📥 To",      value=citizen.mention,    inline=True)
        e.add_field(name="💰 Amount",  value=utils.money(amount), inline=True)
        e.add_field(name="📝 Reason",  value=reason,              inline=False)
        await interaction.response.send_message(embed=e)

    @gov.command(name="take", description="Remove Drav from a citizen")
    @app_commands.describe(citizen="Who", amount="Amount", reason="Why")
    async def take(self, interaction: discord.Interaction, citizen: discord.Member, amount: int, reason: str = "Government deduction"):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        new_bal = db.update_balance(citizen.id, -amount, reason, STARTING)
        e = utils.embed("🏛️ Treasury Deduction", color=utils.RED)
        e.add_field(name="📤 From",   value=citizen.mention,    inline=True)
        e.add_field(name="💸 Amount", value=utils.money(amount), inline=True)
        e.add_field(name="📝 Reason", value=reason,              inline=False)
        await interaction.response.send_message(embed=e)

    @gov.command(name="salary", description="Pay all members of a role")
    @app_commands.describe(role="Role to pay", amount="Per person", reason="Period")
    async def salary(self, interaction: discord.Interaction, role: discord.Role, amount: int, reason: str = "Weekly salary"):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        await interaction.response.defer()
        count = 0
        for member in role.members:
            if not member.bot:
                db.update_balance(member.id, amount, f"Salary ({role.name}): {reason}", STARTING)
                count += 1
        e = utils.embed("💼 Salary Disbursement", color=utils.GREEN)
        e.add_field(name="👥 Role",       value=role.mention,            inline=True)
        e.add_field(name="💰 Per Person", value=utils.money(amount),     inline=True)
        e.add_field(name="👤 Paid",       value=f"{count} citizens",     inline=True)
        e.add_field(name="💸 Total",      value=utils.money(amount*count),inline=True)
        await interaction.followup.send(embed=e)

    @gov.command(name="stats", description="View economy statistics")
    async def stats(self, interaction: discord.Interaction):
        if not utils.is_admin(interaction.member):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        raw = db.raw()
        users = raw.get("users", {})
        total = sum(u.get("balance",0) + u.get("bank",0) for u in users.values())
        wallets = sum(u.get("balance",0) for u in users.values())
        banks = sum(u.get("bank",0) for u in users.values())
        avg = round(total / len(users), 1) if users else 0
        e = utils.embed("📊 Dravia Economy Report", color=utils.BLUE)
        e.add_field(name="👥 Citizens",         value=f"{len(users):,}",        inline=True)
        e.add_field(name="💰 Total Wallets",    value=utils.money(wallets),      inline=True)
        e.add_field(name="🏦 Total Vaults",     value=utils.money(banks),        inline=True)
        e.add_field(name="📈 Total Circulation",value=utils.money(total),        inline=True)
        e.add_field(name="📊 Avg Balance",      value=f"{avg:,} {cfg['currency']}",inline=True)
        e.add_field(name="🎨 Art Listings",     value=str(len(raw.get("art_listings",[]))), inline=True)
        e.add_field(name="⚖️ Open Cases",       value=str(len(db.get_open_cases())),        inline=True)
        e.add_field(name="🏢 Businesses",       value=str(len(raw.get("businesses",[]))),   inline=True)
        e.add_field(name="🎰 Lottery Pool",     value=utils.money(raw.get("lottery",{}).get("pool",0)), inline=True)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @gov.command(name="reset", description="Reset a citizen's balance")
    @app_commands.describe(citizen="Who", amount="Set balance to")
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


async def setup(bot): await bot.add_cog(Gov(bot))
